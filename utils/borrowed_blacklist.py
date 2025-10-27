#!/usr/bin/env python3
"""
Entleih-Blacklist System für ausgeliehene Medien

Verwaltet temporär entliehene Medien mit Rückgabedatum und verhindert
wiederholte Suchanfragen bis das Medium zurückgegeben wurde.
"""

import os
import json
import re
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
from utils.io import DATA_DIR
from utils.logging_config import get_logger

logger = get_logger(__name__)

BORROWED_BLACKLIST_FILE: str = os.path.join(DATA_DIR, "entliehen_blacklist.json")


class BorrowedBlacklist:
    """
    Verwaltet Blacklist für entliehene Medien mit Rückgabedatum.

    Ein Medium kommt auf die Blacklist, wenn:
    - Es im Katalog gefunden wurde
    - Aber als "Entliehen" markiert ist
    - Ein Rückgabedatum extrahiert werden konnte

    Das Medium wird wieder geprüft, wenn:
    - Das Rückgabedatum erreicht oder überschritten wurde
    """

    def __init__(self) -> None:
        """Initialisiert BorrowedBlacklist und lädt existierende Daten."""
        self.blacklist: Dict[str, Dict[str, Any]] = self._load_blacklist()
        logger.info(f"Entleih-Blacklist initialisiert mit {len(self.blacklist)} Einträgen")

    def _load_blacklist(self) -> Dict[str, Dict[str, Any]]:
        """
        Lädt die Entleih-Blacklist aus der JSON-Datei.

        Returns:
            Dictionary mit Medium-Key und Metadaten als Value
        """
        if os.path.exists(BORROWED_BLACKLIST_FILE):
            try:
                with open(BORROWED_BLACKLIST_FILE, "r", encoding="utf-8") as f:
                    data: Dict[str, Dict[str, Any]] = json.load(f)
                logger.info(f"{len(data)} entliehene Medien aus {BORROWED_BLACKLIST_FILE} geladen")
                return data
            except (json.JSONDecodeError, IOError) as e:
                logger.error(f"Fehler beim Laden von {BORROWED_BLACKLIST_FILE}: {e}")
                return {}
        else:
            logger.info("Keine existierende Entleih-Blacklist gefunden")
            return {}

    def _save_blacklist(self) -> None:
        """Speichert die Entleih-Blacklist in die JSON-Datei."""
        try:
            os.makedirs(DATA_DIR, exist_ok=True)
            with open(BORROWED_BLACKLIST_FILE, "w", encoding="utf-8") as f:
                json.dump(self.blacklist, f, ensure_ascii=False, indent=2)
            logger.info(f"{len(self.blacklist)} entliehene Medien in {BORROWED_BLACKLIST_FILE} gespeichert")
        except IOError as e:
            logger.error(f"Fehler beim Speichern von {BORROWED_BLACKLIST_FILE}: {e}")

    def _create_key(self, title: str, author: str = "") -> str:
        """
        Erstellt einen eindeutigen Key für ein Medium.

        Args:
            title: Titel des Mediums
            author: Autor/Künstler/Regisseur

        Returns:
            Normalisierter Key
        """
        key = f"{title}_{author}".lower().strip()
        return key

    def extract_return_date(self, availability_text: str) -> Optional[str]:
        """
        Extrahiert das Rückgabedatum aus der Verfügbarkeitsangabe.

        Sucht nach Pattern wie:
        - "voraussichtlich bis 08/11/2025"
        - "bis 08/11/2025"
        - "Entliehen, voraussichtlich bis 08/11/2025"

        Args:
            availability_text: Verfügbarkeitstext aus Bibliothek

        Returns:
            Datum im Format YYYY-MM-DD oder None

        Example:
            >>> extract_return_date("Entliehen,voraussichtlich bis 08/11/2025")
            '2025-11-08'
        """
        if not availability_text:
            return None

        # Pattern: DD/MM/YYYY oder DD/MM/YY
        pattern = r"bis\s+(\d{2})/(\d{2})/(\d{4})"
        match = re.search(pattern, availability_text)

        if match:
            day = match.group(1)
            month = match.group(2)
            year = match.group(3)

            try:
                # Validiere Datum
                date_obj = datetime.strptime(f"{day}/{month}/{year}", "%d/%m/%Y")
                iso_date = date_obj.strftime("%Y-%m-%d")
                logger.debug(f"Rückgabedatum extrahiert: {iso_date}")
                return iso_date
            except ValueError as e:
                logger.warning(f"Ungültiges Datum gefunden: {day}/{month}/{year} - {e}")
                return None

        logger.debug("Kein Rückgabedatum im Text gefunden")
        return None

    def is_blacklisted(self, title: str, author: str = "") -> bool:
        """
        Prüft, ob ein Medium auf der Entleih-Blacklist steht.

        Args:
            title: Titel des Mediums
            author: Autor/Künstler/Regisseur

        Returns:
            True wenn geblacklistet und Rückgabedatum noch nicht erreicht
        """
        key = self._create_key(title, author)

        if key not in self.blacklist:
            return False

        # Prüfe Rückgabedatum
        entry = self.blacklist[key]
        return_date_str = entry.get("return_date", "")

        if not return_date_str:
            logger.warning(f"Kein Rückgabedatum für '{title}' - entferne von Blacklist")
            self.remove_from_blacklist(title, author)
            return False

        try:
            return_date = datetime.strptime(return_date_str, "%Y-%m-%d")
            today = datetime.now()

            if today >= return_date:
                logger.info(f"Rückgabedatum erreicht für '{title}' - kann neu geprüft werden")
                return False

            days_left = (return_date - today).days
            logger.debug(f"'{title}' noch {days_left} Tage entliehen")
            return True

        except ValueError as e:
            logger.error(f"Ungültiges Datum für '{title}': {return_date_str} - {e}")
            self.remove_from_blacklist(title, author)
            return False

    def add_to_blacklist(self, title: str, author: str = "", media_type: str = "", availability_text: str = "") -> bool:
        """
        Fügt ein entliehenes Medium zur Blacklist hinzu.

        Args:
            title: Titel des Mediums
            author: Autor/Künstler/Regisseur
            media_type: Art des Mediums (DVD, CD, Buch)
            availability_text: Vollständiger Verfügbarkeitstext

        Returns:
            True wenn hinzugefügt, False wenn kein Datum extrahiert werden konnte
        """
        # Extrahiere Rückgabedatum
        return_date = self.extract_return_date(availability_text)

        if not return_date:
            logger.warning(f"Kein Rückgabedatum für '{title}' gefunden - nicht auf Blacklist")
            return False

        key = self._create_key(title, author)

        # Wenn bereits vorhanden, nutze früheres Datum
        if key in self.blacklist:
            existing_date_str = self.blacklist[key]["return_date"]
            existing_date = datetime.strptime(existing_date_str, "%Y-%m-%d")
            new_date = datetime.strptime(return_date, "%Y-%m-%d")

            if new_date < existing_date:
                logger.info(f"Früheres Rückgabedatum für '{title}': {return_date}")
                return_date = return_date
            else:
                logger.debug(f"Behalte früheres Datum für '{title}': {existing_date_str}")
                return_date = existing_date_str

        # Erstelle/Update Eintrag
        self.blacklist[key] = {
            "title": title,
            "author": author,
            "media_type": media_type,
            "return_date": return_date,
            "added_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "availability_text": availability_text[:300],  # Gekürzt
        }

        self._save_blacklist()
        logger.info(f"📅 '{title}' auf Entleih-Blacklist bis {return_date}")
        return True

    def remove_from_blacklist(self, title: str, author: str = "") -> bool:
        """
        Entfernt ein Medium von der Entleih-Blacklist.

        Args:
            title: Titel des Mediums
            author: Autor/Künstler/Regisseur

        Returns:
            True wenn entfernt, False wenn nicht gefunden
        """
        key = self._create_key(title, author)

        if key in self.blacklist:
            del self.blacklist[key]
            self._save_blacklist()
            logger.info(f"✅ '{title}' von Entleih-Blacklist entfernt")
            return True

        return False

    def cleanup_expired_entries(self) -> int:
        """
        Entfernt Einträge mit abgelaufenem Rückgabedatum.

        Returns:
            Anzahl entfernter Einträge
        """
        logger.info("Bereinige abgelaufene Entleih-Einträge...")

        today = datetime.now()
        to_remove: List[str] = []

        for key, entry in self.blacklist.items():
            return_date_str = entry.get("return_date", "")

            try:
                return_date = datetime.strptime(return_date_str, "%Y-%m-%d")

                if today >= return_date:
                    to_remove.append(key)
                    logger.debug(f"Abgelaufen: {entry['title']}")

            except ValueError:
                to_remove.append(key)
                logger.warning(f"Ungültiges Datum: {entry['title']}")

        # Entferne abgelaufene
        for key in to_remove:
            del self.blacklist[key]

        if to_remove:
            self._save_blacklist()

        logger.info(f"{len(to_remove)} abgelaufene Einträge entfernt")
        return len(to_remove)

    def get_stats(self) -> Dict[str, Any]:
        """
        Gibt Statistiken über die Entleih-Blacklist zurück.

        Returns:
            Dictionary mit Statistiken
        """
        if not self.blacklist:
            return {"total_entries": 0, "by_media_type": {}, "upcoming_returns": []}

        # Nach Medientyp
        by_type: Dict[str, int] = {}
        for entry in self.blacklist.values():
            media_type = entry.get("media_type", "Unbekannt")
            by_type[media_type] = by_type.get(media_type, 0) + 1

        # Kommende Rückgaben (nächste 7 Tage)
        today = datetime.now()
        week_later = today + timedelta(days=7)
        upcoming: List[Dict[str, Any]] = []

        for entry in self.blacklist.values():
            return_date_str = entry.get("return_date", "")
            try:
                return_date = datetime.strptime(return_date_str, "%Y-%m-%d")
                if today <= return_date <= week_later:
                    upcoming.append(
                        {"title": entry["title"], "return_date": return_date_str, "days_left": (return_date - today).days}
                    )
            except ValueError:
                continue

        # Sortiere nach Datum
        upcoming.sort(key=lambda x: x["return_date"])

        return {"total_entries": len(self.blacklist), "by_media_type": by_type, "upcoming_returns": upcoming[:10]}  # Top 10

    def print_stats(self) -> None:
        """Druckt Statistiken über die Entleih-Blacklist."""
        stats = self.get_stats()

        print("\n" + "=" * 60)
        print("📅 ENTLEIH-BLACKLIST STATISTIKEN")
        print("=" * 60)
        print(f"Gesamt entliehene Medien: {stats['total_entries']}")

        if stats["by_media_type"]:
            print("\nNach Medientyp:")
            for media_type, count in stats["by_media_type"].items():
                print(f"  - {media_type}: {count}")

        if stats["upcoming_returns"]:
            print("\nBald verfügbar (nächste 7 Tage):")
            for item in stats["upcoming_returns"]:
                print(f"  - {item['title']}")
                print(f"    Rückgabe: {item['return_date']} ({item['days_left']} Tage)")

        print("=" * 60 + "\n")


# Globale Instanz (Singleton)
_borrowed_blacklist_instance: Optional[BorrowedBlacklist] = None


def get_borrowed_blacklist() -> BorrowedBlacklist:
    """
    Gibt die globale Entleih-Blacklist-Instanz zurück (Singleton-Pattern).

    Returns:
        Die globale BorrowedBlacklist-Instanz
    """
    global _borrowed_blacklist_instance
    if _borrowed_blacklist_instance is None:
        _borrowed_blacklist_instance = BorrowedBlacklist()
        logger.info("Neue BorrowedBlacklist-Instanz erstellt")
    return _borrowed_blacklist_instance


def initialize_borrowed_blacklist() -> None:
    """
    Initialisiert die Entleih-Blacklist beim App-Start.

    Lädt die Blacklist und bereinigt abgelaufene Einträge.
    """
    logger.info("Initialisiere Entleih-Blacklist beim Start...")

    blacklist = get_borrowed_blacklist()
    removed = blacklist.cleanup_expired_entries()

    if removed > 0:
        logger.info(f"{removed} abgelaufene Einträge bereinigt")

    # Zeige Statistiken
    blacklist.print_stats()
