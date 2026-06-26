#!/usr/bin/env python3
"""
Zustandsverwaltung für Medien-Empfehlungen
Speichert nur explizit abgelehnte Medien persistent
"""

import os
import json
from typing import Dict, List, Any, Union, Set

from utils.io import DATA_DIR
from utils.logging_config import get_logger

logger = get_logger(__name__)

STATE_FILE = os.path.join(DATA_DIR, "state.json")


class AppState:
    """
    Verwaltet den Zustand der Medien-Empfehlungen.

    Trennt zwischen:
    - suggested: Alle vorgeschlagenen Medien (nur im Arbeitsspeicher)
    - rejected: Explizit abgelehnte Medien (persistent gespeichert)
    - session_unavailable: In dieser Sitzung als nicht verfügbar geprüfte Medien
    - session_searched_artists: In dieser Sitzung bereits nach Alben durchsuchte Künstler
    """

    def __init__(self) -> None:
        """Initialisiert den AppState und lädt abgelehnte Medien."""
        # Struktur: { "films": [ {title:..., author:...}, ...], "albums": [...], "books": [...] }
        # Nur abgelehnte Medien, persistent gespeichert
        self.rejected = self.load_rejected_state()

        # Alle vorgeschlagenen Medien, nur im Arbeitsspeicher
        # Wird bei jedem App-Start zurückgesetzt
        self.suggested = {"films": [], "albums": [], "books": []}

        # Cache für in dieser Sitzung als nicht verfügbar identifizierte Medien
        # (Um wiederholte Bibliotheks-Anfragen zu vermeiden)
        self.session_unavailable = {"films": set(), "albums": set(), "books": set()}

        # Cache für bereits in dieser Sitzung durchsuchte Künstler (Musik)
        self.session_searched_artists: Set[str] = set()

    @staticmethod
    def load_rejected_state() -> Dict[str, List[Dict[str, Any]]]:
        """
        Lädt nur die abgelehnten Medien aus der JSON-Datei.

        Returns:
            Dict[str, List[Dict[str, Any]]]: Abgelehnte Medien nach Kategorien.
        """
        if os.path.exists(STATE_FILE):
            try:
                with open(STATE_FILE, "r", encoding="utf-8") as f:
                    rejected = json.load(f)
                logger.info(f"{sum(len(items) for items in rejected.values())} abgelehnte Medien aus state.json geladen.")
                return rejected
            except (json.JSONDecodeError, KeyError) as e:
                logger.error(f"Fehler beim Laden der state.json: {e}")
                logger.info("Erstelle neue state.json")
                return {"films": [], "albums": [], "books": []}
        else:
            rejected = {"films": [], "albums": [], "books": []}
            AppState.save_rejected_state(rejected)
            logger.info("Neue state.json erstellt.")
            return rejected

    @staticmethod
    def save_rejected_state(rejected: Dict[str, List[Dict[str, Any]]]) -> None:
        """
        Speichert nur die abgelehnten Medien in die JSON-Datei.

        Args:
            rejected (Dict[str, List[Dict[str, Any]]]): Abzulehnende Medien.
        """
        try:
            with open(STATE_FILE, "w", encoding="utf-8") as f:
                json.dump(rejected, f, ensure_ascii=False, indent=2)
            logger.info(f"{sum(len(items) for items in rejected.values())} abgelehnte Medien in state.json gespeichert.")
        except Exception as e:
            logger.error(f"Fehler beim Speichern der state.json: {e}")

    def is_already_suggested(self, category: str, item: Dict[str, Any]) -> bool:
        """
        Prüft, ob ein Item schon vorgeschlagen wurde oder explizit abgelehnt wurde.

        Args:
            category (str): Kategorie ('films', 'albums', 'books').
            item (Dict[str, Any]): Das zu prüfende Medium.

        Returns:
            bool: True wenn bereits vorgeschlagen oder abgelehnt, sonst False.
        """
        title_lower = item["title"].lower()

        # Prüfe ob schon in diesem Lauf vorgeschlagen
        already_suggested_this_run = any(x["title"].lower() == title_lower for x in self.suggested.get(category, []))

        # Prüfe ob explizit abgelehnt (persistent)
        already_rejected = any(x["title"].lower() == title_lower for x in self.rejected.get(category, []))

        if already_suggested_this_run:
            logger.debug(f"'{item['title']}' bereits in diesem Lauf vorgeschlagen")
        if already_rejected:
            logger.debug(f"'{item['title']}' wurde früher abgelehnt")

        return already_suggested_this_run or already_rejected

    def mark_suggested(self, category: str, item: Dict[str, Any]) -> None:
        """
        Markiert ein Item als vorgeschlagen (nur im Arbeitsspeicher).

        Args:
            category (str): Kategorie ('films', 'albums', 'books').
            item (Dict[str, Any]): Das vorgeschlagene Medium.
        """
        if category not in self.suggested:
            self.suggested[category] = []

        # Prüfe ob schon vorhanden
        title_lower = item["title"].lower()
        if not any(x["title"].lower() == title_lower for x in self.suggested[category]):
            self.suggested[category].append(item)
            logger.debug(f"'{item['title']}' als vorgeschlagen markiert")

    def reject(self, category: str, item: Dict[str, Any]) -> None:
        """
        Lehnt ein Item explizit ab - wird persistent gespeichert.

        Args:
            category (str): Kategorie ('films', 'albums', 'books').
            item (Dict[str, Any]): Das abgelehnte Medium.
        """
        if category not in self.rejected:
            self.rejected[category] = []

        title_lower = item["title"].lower()

        # Prüfe ob schon in abgelehnten Items
        if not any(x["title"].lower() == title_lower for x in self.rejected[category]):
            self.rejected[category].append(item)
            logger.info(f"'{item['title']}' als abgelehnt markiert")

            # Speichere sofort persistent
            self.save_rejected_state(self.rejected)
        else:
            logger.debug(f"'{item['title']}' war bereits als abgelehnt markiert")

    def is_item_unavailable(self, category: str, item: Dict[str, Any]) -> bool:
        """
        Prüft, ob ein Item in dieser Sitzung bereits als nicht verfügbar erkannt wurde.

        Args:
            category (str): Kategorie ('films', 'albums', 'books').
            item (Dict[str, Any]): Das zu prüfende Medium.

        Returns:
            bool: True wenn als nicht verfügbar erkannt, sonst False.
        """
        if category not in self.session_unavailable:
            return False

        title_lower = item["title"].lower()
        author_lower = item.get("author", "").lower()
        item_key = f"{title_lower}|{author_lower}"

        return item_key in self.session_unavailable[category]

    def mark_item_unavailable(self, category: str, item: Dict[str, Any]) -> None:
        """
        Markiert ein Item in dieser Sitzung als nicht verfügbar.

        Args:
            category (str): Kategorie ('films', 'albums', 'books').
            item (Dict[str, Any]): Das nicht verfügbare Medium.
        """
        if category not in self.session_unavailable:
            self.session_unavailable[category] = set()

        title_lower = item["title"].lower()
        author_lower = item.get("author", "").lower()
        item_key = f"{title_lower}|{author_lower}"

        if item_key not in self.session_unavailable[category]:
            self.session_unavailable[category].add(item_key)
            logger.debug(f"'{item['title']}' als session-unavailable markiert")

    def is_artist_searched(self, artist_name: str) -> bool:
        """
        Prüft, ob für diesen Künstler in dieser Sitzung bereits eine Suche durchgeführt wurde.

        Args:
            artist_name (str): Name des Künstlers.

        Returns:
            bool: True wenn bereits durchsucht, sonst False.
        """
        return artist_name.lower().strip() in self.session_searched_artists

    def mark_artist_searched(self, artist_name: str) -> None:
        """
        Markiert einen Künstler als in dieser Sitzung bereits durchsucht.

        Args:
            artist_name (str): Name des Künstlers.
        """
        artist_key = artist_name.lower().strip()
        if artist_key not in self.session_searched_artists:
            self.session_searched_artists.add(artist_key)
            logger.debug(f"Artist '{artist_name}' als session-searched markiert")

    def reset_rejected(self) -> None:
        """Setzt alle abgelehnten Medien zurück (löscht state.json)."""
        self.rejected = {"films": [], "albums": [], "books": []}
        self.save_rejected_state(self.rejected)
        logger.info("Alle abgelehnten Medien zurückgesetzt")

    def reset_suggested(self) -> None:
        """Setzt nur die aktuell vorgeschlagenen zurück."""
        self.suggested = {"films": [], "albums": [], "books": []}
        logger.info("Aktuell vorgeschlagene Medien zurückgesetzt")

    def reset_session_cache(self) -> None:
        """Setzt die Sitzungs-Caches für Nicht-Verfügbarkeit und Künstler-Suchen zurück."""
        self.session_unavailable = {"films": set(), "albums": set(), "books": set()}
        self.session_searched_artists = set()
        logger.info("Sitzungs-Caches zurückgesetzt")

    def get_stats(self) -> Dict[str, Any]:
        """
        Gibt Statistiken über den aktuellen Zustand zurück.

        Returns:
            Dict[str, Any]: Statistiken über abgelehnte, vorgeschlagene und session-unavailable Medien.
        """
        stats = {
            "rejected_total": sum(len(items) for items in self.rejected.values()),
            "suggested_total": sum(len(items) for items in self.suggested.values()),
            "session_unavailable_total": sum(len(items) for items in self.session_unavailable.values()),
            "session_searched_artists": len(self.session_searched_artists),
            "rejected_by_category": {category: len(items) for category, items in self.rejected.items()},
            "suggested_by_category": {category: len(items) for category, items in self.suggested.items()},
        }
        return stats

    def print_stats(self) -> None:
        """Druckt Statistiken über den aktuellen Zustand."""
        stats = self.get_stats()
        print("\n" + "=" * 50)
        print("MEDIEN-ZUSTAND STATISTIKEN")
        print("=" * 50)
        print(f"Abgelehnte Medien (persistent): {stats['rejected_total']}")
        for category, count in stats["rejected_by_category"].items():
            if count > 0:
                print(f"  - {category.capitalize()}: {count}")

        print(f"Vorgeschlagene Medien (aktueller Lauf): {stats['suggested_total']}")
        for category, count in stats["suggested_by_category"].items():
            if count > 0:
                print(f"  - {category.capitalize()}: {count}")

        print(f"Session-Caches:")
        print(f"  - Nicht verfügbare Medien: {stats['session_unavailable_total']}")
        print(f"  - Durchsuchte Künstler: {stats['session_searched_artists']}")
        print("=" * 50 + "\n")

    def list_rejected_items(self, category: str = None) -> Union[Dict[str, List[Dict[str, Any]]], List[Dict[str, Any]]]:
        """
        Listet abgelehnte Items auf.

        Args:
            category (str, optional): Spezifische Kategorie oder None für alle (default: None).

        Returns:
            Union[Dict[str, List[Dict[str, Any]]], List[Dict[str, Any]]]: Abgelehnte Items.
        """
        if category:
            return self.rejected.get(category, [])
        else:
            return self.rejected
