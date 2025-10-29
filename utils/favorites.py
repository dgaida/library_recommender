#!/usr/bin/env python3
"""
utils/favorites.py - Favoriten-Verwaltung

Speichert erfolgreich gefundene Favoriten persistent und lädt sie beim App-Start.
"""

import os
import json
from datetime import datetime
from typing import Dict, List, Any, Optional
from utils.io import DATA_DIR
from utils.logging_config import get_logger

logger = get_logger(__name__)

FAVORITES_FILE: str = os.path.join(DATA_DIR, "favoriten.json")


class FavoritesManager:
    """
    Verwaltet gespeicherte Favoriten (Filme, Alben, Bücher).

    Ein Favorit wird gespeichert, wenn er über den Favoriten-Tab
    erfolgreich gefunden und einer Liste hinzugefügt wurde.
    """

    def __init__(self) -> None:
        """Initialisiert FavoritesManager und lädt existierende Favoriten."""
        self.favorites: Dict[str, List[Dict[str, Any]]] = self._load_favorites()
        logger.info(f"Favoriten-System initialisiert mit {self._count_favorites()} Einträgen")

    def _load_favorites(self) -> Dict[str, List[Dict[str, Any]]]:
        """
        Lädt Favoriten aus der JSON-Datei.

        Returns:
            Dictionary mit Kategorien als Keys und Listen von Favoriten als Values
        """
        if os.path.exists(FAVORITES_FILE):
            try:
                with open(FAVORITES_FILE, "r", encoding="utf-8") as f:
                    data: Dict[str, List[Dict[str, Any]]] = json.load(f)

                total = sum(len(items) for items in data.values())
                logger.info(f"{total} Favoriten aus {FAVORITES_FILE} geladen")
                return data
            except (json.JSONDecodeError, IOError) as e:
                logger.error(f"Fehler beim Laden von {FAVORITES_FILE}: {e}")
                return {"films": [], "albums": [], "books": []}
        else:
            logger.info("Keine existierende Favoriten-Datei gefunden")
            return {"films": [], "albums": [], "books": []}

    def _save_favorites(self) -> None:
        """Speichert Favoriten in die JSON-Datei."""
        try:
            os.makedirs(DATA_DIR, exist_ok=True)
            with open(FAVORITES_FILE, "w", encoding="utf-8") as f:
                json.dump(self.favorites, f, ensure_ascii=False, indent=2)

            total = self._count_favorites()
            logger.info(f"{total} Favoriten in {FAVORITES_FILE} gespeichert")
        except IOError as e:
            logger.error(f"Fehler beim Speichern von {FAVORITES_FILE}: {e}")

    def _count_favorites(self) -> int:
        """Zählt Gesamtanzahl der Favoriten."""
        return sum(len(items) for items in self.favorites.values())

    def add_favorite(
        self, category: str, title: str, author: str = "", media_type: str = "", search_type: str = "specific"
    ) -> bool:
        """
        Fügt einen Favoriten hinzu.

        Args:
            category: Kategorie ('films', 'albums', 'books')
            title: Titel des Mediums
            author: Autor/Künstler/Regisseur
            media_type: Medienart (DVD, CD, Buch)
            search_type: Art der Suche ('specific' oder 'artist')

        Returns:
            True wenn hinzugefügt, False wenn bereits vorhanden
        """
        if category not in self.favorites:
            logger.warning(f"Unbekannte Kategorie '{category}'")
            return False

        # Prüfe ob bereits vorhanden
        if self._is_favorite(category, title, author):
            logger.debug(f"'{title}' ist bereits Favorit")
            return False

        # Erstelle Favoriten-Eintrag
        favorite_entry: Dict[str, Any] = {
            "title": title,
            "author": author,
            "media_type": media_type,
            "search_type": search_type,
            "added_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        }

        self.favorites[category].append(favorite_entry)
        self._save_favorites()

        logger.info(f"✅ Favorit hinzugefügt: '{title}' von '{author}' ({category})")
        return True

    def _is_favorite(self, category: str, title: str, author: str = "") -> bool:
        """
        Prüft ob ein Medium bereits als Favorit gespeichert ist.

        Args:
            category: Kategorie ('films', 'albums', 'books')
            title: Titel des Mediums
            author: Autor/Künstler/Regisseur

        Returns:
            True wenn bereits Favorit, sonst False
        """
        if category not in self.favorites:
            return False

        title_lower = title.lower().strip()
        author_lower = author.lower().strip()

        for fav in self.favorites[category]:
            fav_title = fav["title"].lower().strip()
            fav_author = fav.get("author", "").lower().strip()

            # Titel muss übereinstimmen
            if fav_title == title_lower:
                # Wenn kein Autor angegeben, nur Titel prüfen
                if not author_lower or not fav_author:
                    return True
                # Wenn beide Autoren vorhanden, beide prüfen
                if fav_author == author_lower:
                    return True

        return False

    def get_favorites(self, category: Optional[str] = None) -> Dict[str, List[Dict[str, Any]]]:
        """
        Gibt Favoriten zurück.

        Args:
            category: Spezifische Kategorie oder None für alle

        Returns:
            Dictionary mit Favoriten
        """
        if category:
            return {category: self.favorites.get(category, [])}
        return self.favorites

    def remove_favorite(self, category: str, title: str, author: str = "") -> bool:
        """
        Entfernt einen Favoriten.

        Args:
            category: Kategorie ('films', 'albums', 'books')
            title: Titel des Mediums
            author: Autor/Künstler/Regisseur

        Returns:
            True wenn entfernt, False wenn nicht gefunden
        """
        if category not in self.favorites:
            return False

        title_lower = title.lower().strip()
        author_lower = author.lower().strip()

        original_length = len(self.favorites[category])

        # Filtere Favoriten
        self.favorites[category] = [
            fav
            for fav in self.favorites[category]
            if not (
                fav["title"].lower().strip() == title_lower
                and (not author_lower or not fav.get("author") or fav.get("author", "").lower().strip() == author_lower)
            )
        ]

        removed = original_length > len(self.favorites[category])

        if removed:
            self._save_favorites()
            logger.info(f"✅ Favorit entfernt: '{title}' ({category})")

        return removed

    def get_stats(self) -> Dict[str, Any]:
        """
        Gibt Statistiken über Favoriten zurück.

        Returns:
            Dictionary mit Statistiken
        """
        stats = {
            "total_favorites": self._count_favorites(),
            "by_category": {cat: len(items) for cat, items in self.favorites.items()},
            "recent_additions": [],
        }

        # Letzte 5 hinzugefügte Favoriten
        all_favorites = []
        for category, items in self.favorites.items():
            for item in items:
                all_favorites.append({**item, "category": category})

        # Sortiere nach Datum (neueste zuerst)
        all_favorites.sort(key=lambda x: x.get("added_at", ""), reverse=True)

        stats["recent_additions"] = all_favorites[:5]

        return stats

    def print_stats(self) -> None:
        """Druckt Statistiken über Favoriten."""
        stats = self.get_stats()

        print("\n" + "=" * 60)
        print("⭐ FAVORITEN STATISTIKEN")
        print("=" * 60)
        print(f"Gesamt: {stats['total_favorites']} Favoriten")

        if stats["by_category"]:
            print("\nNach Kategorie:")
            for category, count in stats["by_category"].items():
                if count > 0:
                    cat_name = {"films": "Filme", "albums": "Alben", "books": "Bücher"}.get(category, category)
                    print(f"  - {cat_name}: {count}")

        if stats["recent_additions"]:
            print("\nZuletzt hinzugefügt:")
            for fav in stats["recent_additions"]:
                print(f"  • {fav['title']}", end="")
                if fav.get("author"):
                    print(f" - {fav['author']}", end="")
                print(f" ({fav['category']})")
                print(f"    Hinzugefügt: {fav['added_at']}")

        print("=" * 60 + "\n")


# Globale Instanz (Singleton)
_favorites_manager_instance: Optional[FavoritesManager] = None


def get_favorites_manager() -> FavoritesManager:
    """
    Gibt die globale FavoritesManager-Instanz zurück (Singleton-Pattern).

    Returns:
        Die globale FavoritesManager-Instanz
    """
    global _favorites_manager_instance
    if _favorites_manager_instance is None:
        _favorites_manager_instance = FavoritesManager()
        logger.info("Neue FavoritesManager-Instanz erstellt")
    return _favorites_manager_instance
