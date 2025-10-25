#!/usr/bin/env python3
"""
Blacklist-System für Medien, die in der Bibliothek nicht existieren.

Speichert Medien, die bei der Suche keine Treffer liefern, um wiederholte
Suchanfragen zu vermeiden. Medien, die nur ausgeliehen sind, werden NICHT
auf die Blacklist gesetzt.
"""

import os
import json
from datetime import datetime
from typing import Dict, List, Any, Optional
from utils.io import DATA_DIR
from utils.logging_config import get_logger

logger = get_logger(__name__)

BLACKLIST_FILES: Dict[str, str] = {
    "films": os.path.join(DATA_DIR, "blacklist_films.json"),
    "albums": os.path.join(DATA_DIR, "blacklist_albums.json"),
    "books": os.path.join(DATA_DIR, "blacklist_books.json"),
}


class Blacklist:
    """
    Verwaltet Blacklists für Medien, die in der Bibliothek nicht existieren.

    Ein Medium kommt auf die Blacklist, wenn:
    - Die Suche KEINE Treffer liefert (leere Ergebnisliste)

    Ein Medium kommt NICHT auf die Blacklist, wenn:
    - Treffer gefunden wurden, aber alle ausgeliehen sind
    """

    def __init__(self) -> None:
        """Initialisiert Blacklist und lädt existierende Listen."""
        self.blacklists: Dict[str, List[Dict[str, Any]]] = {
            "films": self._load_blacklist("films"),
            "albums": self._load_blacklist("albums"),
            "books": self._load_blacklist("books"),
        }
        logger.info("Blacklist-System initialisiert")

    def _load_blacklist(self, category: str) -> List[Dict[str, Any]]:
        """
        Lädt die Blacklist für eine Kategorie aus der JSON-Datei.

        Args:
            category: Kategorie ('films', 'albums', 'books')

        Returns:
            Liste der geblacklisteten Medien
        """
        filepath: Optional[str] = BLACKLIST_FILES.get(category)
        if not filepath:
            logger.warning(f"Keine Blacklist-Datei für Kategorie '{category}'")
            return []

        if os.path.exists(filepath):
            try:
                with open(filepath, "r", encoding="utf-8") as f:
                    data: List[Dict[str, Any]] = json.load(f)
                logger.info(f"{len(data)} geblacklistete {category} geladen")
                return data
            except (json.JSONDecodeError, IOError) as e:
                logger.error(f"Fehler beim Laden von {filepath}: {e}")
                return []
        else:
            logger.info(f"Keine existierende Blacklist für {category}")
            return []

    def _save_blacklist(self, category: str) -> None:
        """
        Speichert die Blacklist für eine Kategorie in die JSON-Datei.

        Args:
            category: Kategorie ('films', 'albums', 'books')
        """
        filepath: Optional[str] = BLACKLIST_FILES.get(category)
        if not filepath:
            logger.warning(f"Keine Blacklist-Datei für Kategorie '{category}'")
            return

        try:
            os.makedirs(DATA_DIR, exist_ok=True)
            with open(filepath, "w", encoding="utf-8") as f:
                json.dump(self.blacklists[category], f, ensure_ascii=False, indent=2)
            logger.info(f"{len(self.blacklists[category])} {category} " f"in Blacklist gespeichert")
        except IOError as e:
            logger.error(f"Fehler beim Speichern von {filepath}: {e}")

    def is_blacklisted(self, category: str, item: Dict[str, Any]) -> bool:
        """
        Prüft, ob ein Medium auf der Blacklist steht.

        Args:
            category: Kategorie ('films', 'albums', 'books')
            item: Medium mit 'title' und optional 'author'

        Returns:
            True wenn geblacklistet, sonst False
        """
        if category not in self.blacklists:
            logger.warning(f"Unbekannte Kategorie '{category}'")
            return False

        title_lower: str = item["title"].lower().strip()
        author_lower: str = item.get("author", "").lower().strip()

        for blacklisted in self.blacklists[category]:
            bl_title: str = blacklisted["title"].lower().strip()
            bl_author: str = blacklisted.get("author", "").lower().strip()

            # Vergleiche Titel und Autor
            if bl_title == title_lower:
                # Wenn kein Autor vorhanden, nur Titel vergleichen
                if not author_lower or not bl_author:
                    return True
                # Wenn beide Autoren vorhanden, beide vergleichen
                if bl_author == author_lower:
                    return True

        return False

    def add_to_blacklist(self, category: str, item: Dict[str, Any], reason: str = "Nicht in Bibliothek gefunden") -> None:
        """
        Fügt ein Medium zur Blacklist hinzu.

        Args:
            category: Kategorie ('films', 'albums', 'books')
            item: Medium mit 'title' und optional 'author'
            reason: Grund für die Blacklistung
        """
        if category not in self.blacklists:
            logger.warning(f"Unbekannte Kategorie '{category}'")
            return

        # Prüfe ob schon geblacklistet
        if self.is_blacklisted(category, item):
            logger.debug(f"'{item['title']}' ist bereits geblacklistet")
            return

        # Erstelle Blacklist-Eintrag
        blacklist_entry: Dict[str, Any] = {
            "title": item["title"],
            "author": item.get("author", ""),
            "type": item.get("type", ""),
            "reason": reason,
            "added_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        }

        self.blacklists[category].append(blacklist_entry)
        self._save_blacklist(category)

        logger.info(f"✅ '{item['title']}' zur {category}-Blacklist hinzugefügt: {reason}")

    def remove_from_blacklist(self, category: str, item: Dict[str, Any]) -> bool:
        """
        Entfernt ein Medium von der Blacklist.

        Args:
            category: Kategorie ('films', 'albums', 'books')
            item: Medium mit 'title' und optional 'author'

        Returns:
            True wenn entfernt, False wenn nicht gefunden
        """
        if category not in self.blacklists:
            logger.warning(f"Unbekannte Kategorie '{category}'")
            return False

        title_lower: str = item["title"].lower().strip()
        author_lower: str = item.get("author", "").lower().strip()

        original_length: int = len(self.blacklists[category])

        # Filtere Blacklist
        self.blacklists[category] = [
            bl
            for bl in self.blacklists[category]
            if not (
                bl["title"].lower().strip() == title_lower
                and (not author_lower or not bl.get("author") or bl.get("author", "").lower().strip() == author_lower)
            )
        ]

        removed: bool = original_length > len(self.blacklists[category])

        if removed:
            self._save_blacklist(category)
            logger.info(f"✅ '{item['title']}' von {category}-Blacklist entfernt")

        return removed

    def clear_blacklist(self, category: Optional[str] = None) -> None:
        """
        Löscht die Blacklist für eine oder alle Kategorien.

        Args:
            category: Spezifische Kategorie oder None für alle
        """
        if category:
            if category in self.blacklists:
                self.blacklists[category] = []
                self._save_blacklist(category)
                logger.info(f"✅ {category}-Blacklist gelöscht")
            else:
                logger.warning(f"Unbekannte Kategorie '{category}'")
        else:
            for cat in self.blacklists.keys():
                self.blacklists[cat] = []
                self._save_blacklist(cat)
            logger.info("✅ Alle Blacklists gelöscht")

    def get_blacklist_stats(self) -> Dict[str, Dict[str, Any]]:
        """
        Gibt Statistiken über die Blacklists zurück.

        Returns:
            Dictionary mit Statistiken pro Kategorie
        """
        stats: Dict[str, Dict[str, Any]] = {
            category: {"count": len(items), "items": items} for category, items in self.blacklists.items()
        }
        return stats

    def print_stats(self) -> None:
        """Druckt Statistiken über die Blacklists."""
        stats: Dict[str, Dict[str, Any]] = self.get_blacklist_stats()
        total: int = sum(s["count"] for s in stats.values())

        print("\n" + "=" * 50)
        print("BLACKLIST STATISTIKEN")
        print("=" * 50)
        print(f"Gesamt geblacklistet: {total} Medien")

        for category, data in stats.items():
            if data["count"] > 0:
                print(f"\n{category.capitalize()}: {data['count']}")
                for item in data["items"][:5]:  # Zeige max. 5
                    print(f"  - {item['title']}", end="")
                    if item.get("author"):
                        print(f" ({item['author']})", end="")
                    print(f" - {item.get('reason', 'Unbekannt')}")

                if data["count"] > 5:
                    print(f"  ... und {data['count'] - 5} weitere")

        print("=" * 50 + "\n")


# Globale Blacklist-Instanz (Singleton)
_blacklist_instance: Optional[Blacklist] = None


def get_blacklist() -> Blacklist:
    """
    Gibt die globale Blacklist-Instanz zurück (Singleton-Pattern).

    Returns:
        Die globale Blacklist-Instanz
    """
    global _blacklist_instance
    if _blacklist_instance is None:
        _blacklist_instance = Blacklist()
        logger.info("Neue Blacklist-Instanz erstellt")
    return _blacklist_instance
