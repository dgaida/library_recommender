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

from utils.io import DATA_DIR

BLACKLIST_FILES = {
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

    def __init__(self):
        self.blacklists = {
            "films": self._load_blacklist("films"),
            "albums": self._load_blacklist("albums"),
            "books": self._load_blacklist("books"),
        }

    def _load_blacklist(self, category):
        """
        Lädt die Blacklist für eine Kategorie aus der JSON-Datei.

        Args:
            category (str): Kategorie ('films', 'albums', 'books')

        Returns:
            list[dict]: Liste der geblacklisteten Medien
        """
        filepath = BLACKLIST_FILES.get(category)
        if not filepath:
            return []

        if os.path.exists(filepath):
            try:
                with open(filepath, "r", encoding="utf-8") as f:
                    data = json.load(f)
                print(f"DEBUG: {len(data)} geblacklistete {category} geladen")
                return data
            except (json.JSONDecodeError, IOError) as e:
                print(f"WARNUNG: Fehler beim Laden von {filepath}: {e}")
                return []
        else:
            return []

    def _save_blacklist(self, category):
        """
        Speichert die Blacklist für eine Kategorie in die JSON-Datei.

        Args:
            category (str): Kategorie ('films', 'albums', 'books')
        """
        filepath = BLACKLIST_FILES.get(category)
        if not filepath:
            return

        try:
            os.makedirs(DATA_DIR, exist_ok=True)
            with open(filepath, "w", encoding="utf-8") as f:
                json.dump(self.blacklists[category], f, ensure_ascii=False, indent=2)
            print(f"DEBUG: {len(self.blacklists[category])} {category} in Blacklist gespeichert")
        except IOError as e:
            print(f"FEHLER beim Speichern von {filepath}: {e}")

    def is_blacklisted(self, category, item):
        """
        Prüft, ob ein Medium auf der Blacklist steht.

        Args:
            category (str): Kategorie ('films', 'albums', 'books')
            item (dict): Medium mit 'title' und optional 'author'

        Returns:
            bool: True wenn geblacklistet, sonst False
        """
        if category not in self.blacklists:
            return False

        title_lower = item["title"].lower().strip()
        author_lower = item.get("author", "").lower().strip()

        for blacklisted in self.blacklists[category]:
            bl_title = blacklisted["title"].lower().strip()
            bl_author = blacklisted.get("author", "").lower().strip()

            # Vergleiche Titel und Autor
            if bl_title == title_lower:
                # Wenn kein Autor vorhanden, nur Titel vergleichen
                if not author_lower or not bl_author:
                    return True
                # Wenn beide Autoren vorhanden, beide vergleichen
                if bl_author == author_lower:
                    return True

        return False

    def add_to_blacklist(self, category, item, reason="Nicht in Bibliothek gefunden"):
        """
        Fügt ein Medium zur Blacklist hinzu.

        Args:
            category (str): Kategorie ('films', 'albums', 'books')
            item (dict): Medium mit 'title' und optional 'author'
            reason (str): Grund für die Blacklistung
        """
        if category not in self.blacklists:
            print(f"WARNUNG: Unbekannte Kategorie '{category}'")
            return

        # Prüfe ob schon geblacklistet
        if self.is_blacklisted(category, item):
            print(f"DEBUG: '{item['title']}' ist bereits geblacklistet")
            return

        # Erstelle Blacklist-Eintrag
        blacklist_entry = {
            "title": item["title"],
            "author": item.get("author", ""),
            "type": item.get("type", ""),
            "reason": reason,
            "added_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        }

        self.blacklists[category].append(blacklist_entry)
        self._save_blacklist(category)

        print(f"✅ '{item['title']}' zur {category}-Blacklist hinzugefügt: {reason}")

    def remove_from_blacklist(self, category, item):
        """
        Entfernt ein Medium von der Blacklist.

        Args:
            category (str): Kategorie ('films', 'albums', 'books')
            item (dict): Medium mit 'title' und optional 'author'

        Returns:
            bool: True wenn entfernt, False wenn nicht gefunden
        """
        if category not in self.blacklists:
            return False

        title_lower = item["title"].lower().strip()
        author_lower = item.get("author", "").lower().strip()

        original_length = len(self.blacklists[category])

        # Filtere Blacklist
        self.blacklists[category] = [
            bl
            for bl in self.blacklists[category]
            if not (
                bl["title"].lower().strip() == title_lower
                and (not author_lower or not bl.get("author") or bl.get("author", "").lower().strip() == author_lower)
            )
        ]

        removed = original_length > len(self.blacklists[category])

        if removed:
            self._save_blacklist(category)
            print(f"✅ '{item['title']}' von {category}-Blacklist entfernt")

        return removed

    def clear_blacklist(self, category=None):
        """
        Löscht die Blacklist für eine oder alle Kategorien.

        Args:
            category (str, optional): Spezifische Kategorie oder None für alle
        """
        if category:
            if category in self.blacklists:
                self.blacklists[category] = []
                self._save_blacklist(category)
                print(f"✅ {category}-Blacklist gelöscht")
        else:
            for cat in self.blacklists.keys():
                self.blacklists[cat] = []
                self._save_blacklist(cat)
            print("✅ Alle Blacklists gelöscht")

    def get_blacklist_stats(self):
        """
        Gibt Statistiken über die Blacklists zurück.

        Returns:
            dict: Statistiken pro Kategorie
        """
        return {category: {"count": len(items), "items": items} for category, items in self.blacklists.items()}

    def print_stats(self):
        """
        Druckt Statistiken über die Blacklists.
        """
        stats = self.get_blacklist_stats()
        total = sum(s["count"] for s in stats.values())

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


# Globale Blacklist-Instanz
_blacklist_instance = None


def get_blacklist():
    """
    Gibt die globale Blacklist-Instanz zurück (Singleton-Pattern).

    Returns:
        Blacklist: Die globale Blacklist-Instanz
    """
    global _blacklist_instance
    if _blacklist_instance is None:
        _blacklist_instance = Blacklist()
    return _blacklist_instance
