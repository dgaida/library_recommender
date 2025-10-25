#!/usr/bin/env python3
"""
Recommender-System für Bibliotheksmedien mit Type Hints und Logging
"""

from typing import List, Dict, Any
from .state import AppState
from utils.blacklist import get_blacklist, Blacklist
from utils.logging_config import get_logger

logger = get_logger(__name__)


class Recommender:
    """
    Stellt Empfehlungslogik für Filme, Musik und Bücher bereit.

    Diese Klasse nutzt KoelnLibrarySearch, um Titel in der Stadtbibliothek Köln
    zu suchen und prüft deren aktuelle Verfügbarkeit. Bereits vorgeschlagene
    Items werden in AppState gespeichert, um Mehrfachvorschläge zu verhindern.
    """

    def __init__(self, library_search: Any, state: AppState) -> None:
        """
        Initialisiert den Recommender.

        Args:
            library_search: KoelnLibrarySearch-Instanz
            state: AppState für Zustandsverwaltung
        """
        self.library_search = library_search
        self.state: AppState = state
        self.blacklist: Blacklist = get_blacklist()
        logger.info("Recommender initialisiert")

    def _pick_available_items(
        self, items: List[Dict[str, Any]], category: str, n: int = 4, verbose: bool = False
    ) -> List[Dict[str, Any]]:
        """
        Wählt n zufällige, heute verfügbare Items aus einer Liste.

        Args:
            items: Liste von Werken mit 'title', 'author', etc.
            category: Kategorie ('films', 'albums', 'books')
            n: Anzahl gewünschter Vorschläge
            verbose: Ausführliches Logging

        Returns:
            Liste der ausgewählten Werke
        """
        results: List[Dict[str, Any]] = []

        logger.info(f"Suche {n} verfügbare Items in Kategorie '{category}'")

        for item in items:
            # Überspringe geblacklistete Items
            if self.blacklist.is_blacklisted(category, item):
                if verbose:
                    logger.debug(f"Überspringe '{item['title']}' (geblacklistet)")
                continue

            # Überspringe bereits vorgeschlagene Items
            if self.state.is_already_suggested(category, item):
                if verbose:
                    logger.debug(f"Überspringe '{item['title']}' (bereits vorgeschlagen)")
                continue

            media_type: str = item.get("type", "")

            if media_type == "Buch":
                query = f"{item.get('author', '')} {item.get('title')} " f"{media_type}".strip()
            else:
                query = f"{item.get('title')} {item.get('author', '')} " f"{media_type}".strip()

            # Suche in Bibliothek
            logger.debug(f"Suche nach: '{query}'")
            hits: List[Dict[str, Any]] = self.library_search.search(query)

            # Keine Treffer → Blacklist
            if not hits or len(hits) == 0:
                logger.info(f"⚫ Keine Treffer für '{item['title']}' - wird geblacklistet")
                self.blacklist.add_to_blacklist(category, item, reason="Keine Treffer in Bibliothekskatalog")
                continue

            # Prüfen, ob verfügbar (nur auf zentralbibliothek_info)
            available: List[Dict[str, Any]] = [
                h for h in hits if "zentralbibliothek_info" in h and "verfügbar" in h["zentralbibliothek_info"].lower()
            ]

            if available:
                # Alle Verfügbarkeits-Infos zusammenfassen
                infos: List[str] = [h["zentralbibliothek_info"] for h in hits if "zentralbibliothek_info" in h]

                # Kopiere das Item und füge bib_number hinzu
                result_item: Dict[str, Any] = item.copy()
                result_item["bib_number"] = f"{', '.join(infos)}"

                results.append(result_item)
                self.state.mark_suggested(category, item)

                logger.info(f"✅ '{item['title']}' verfügbar und vorgeschlagen")

            if len(results) >= n:
                break

        logger.info(f"Gefunden: {len(results)}/{n} verfügbare Items in '{category}'")
        return results

    def suggest_films(self, films: List[Dict[str, Any]], n: int = 4) -> List[Dict[str, Any]]:
        """
        Wählt verfügbare Filme aus der bereitgestellten Liste.

        Args:
            films: Liste von Filmen mit Titeln, Autoren und Typ
            n: Anzahl gewünschter Vorschläge

        Returns:
            Liste der vorgeschlagenen Filme, die aktuell in der
            Zentralbibliothek verfügbar sind
        """
        logger.info(f"Erstelle {n} Filmvorschläge")
        return self._pick_available_items(films, "films", n)

    def suggest_albums(self, albums: List[Dict[str, Any]], n: int = 4) -> List[Dict[str, Any]]:
        """
        Wählt verfügbare Musikalben aus der bereitgestellten Liste.

        Args:
            albums: Liste von Alben mit Titel, Künstler und Typ
            n: Anzahl gewünschter Vorschläge

        Returns:
            Liste der vorgeschlagenen Alben, die aktuell in der
            Zentralbibliothek verfügbar sind
        """
        logger.info(f"Erstelle {n} Albumvorschläge")
        return self._pick_available_items(albums, "albums", n)

    def suggest_books(self, books: List[Dict[str, Any]], n: int = 4) -> List[Dict[str, Any]]:
        """
        Wählt verfügbare Bücher aus der bereitgestellten Liste.

        Args:
            books: Liste von Büchern mit Titel, Autor und Typ
            n: Anzahl gewünschter Vorschläge

        Returns:
            Liste der vorgeschlagenen Bücher, die aktuell in der
            Zentralbibliothek verfügbar sind
        """
        logger.info(f"Erstelle {n} Buchvorschläge")
        return self._pick_available_items(books, "books", n)
