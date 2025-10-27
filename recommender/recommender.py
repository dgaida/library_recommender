#!/usr/bin/env python3
"""
Recommender-System für Bibliotheksmedien mit ausgewogener Quellenverteilung

Dieses Modul stellt sicher, dass Empfehlungen gleichmäßig aus allen verfügbaren
Datenquellen stammen (z.B. 4 Filme von BBC, 4 von FBW, 4 von Oscar).
"""

import re
from typing import List, Dict, Any, Optional
from collections import defaultdict
from .state import AppState
from utils.blacklist import get_blacklist, Blacklist
from utils.logging_config import get_logger
from utils.borrowed_blacklist import get_borrowed_blacklist

logger = get_logger(__name__)


class Recommender:
    """
    Stellt Empfehlungslogik für Filme, Musik und Bücher bereit.

    Diese Klasse nutzt KoelnLibrarySearch, um Titel in der Stadtbibliothek Köln
    zu suchen und prüft deren aktuelle Verfügbarkeit. Bereits vorgeschlagene
    Items werden in AppState gespeichert, um Mehrfachvorschläge zu verhindern.

    Die Empfehlungen werden so verteilt, dass aus jeder Datenquelle gleichmäßig
    Medien vorgeschlagen werden (z.B. 4 pro Quelle).
    """

    def __init__(self, library_search: Any, state: AppState) -> None:
        """
        Initialisiert den Recommender.

        Args:
            library_search: KoelnLibrarySearch-Instanz für Bibliothekssuche
            state: AppState für Zustandsverwaltung (vorgeschlagen/abgelehnt)
        """
        self.library_search = library_search
        self.state: AppState = state
        self.blacklist: Blacklist = get_blacklist()

        # Tracking für Quellen-Balance pro Kategorie
        self.source_counts: Dict[str, Dict[str, int]] = {
            "films": defaultdict(int),
            "albums": defaultdict(int),
            "books": defaultdict(int),
        }

        logger.info("Recommender initialisiert mit Quellen-Balancing")

    def _get_items_by_source(self, items: List[Dict[str, Any]]) -> Dict[str, List[Dict[str, Any]]]:
        """
        Gruppiert Items nach ihrer Quelle.

        Args:
            items: Liste von Medien mit 'source' Attribut

        Returns:
            Dictionary mit Quelle als Key und Liste von Items als Value
        """
        items_by_source: Dict[str, List[Dict[str, Any]]] = defaultdict(list)

        for item in items:
            source = item.get("source", "Unbekannt")

            # Handle personalisierte Empfehlungen
            if "Interessant für dich" in source:
                source = "Personalisiert"
            # elif "besten Ratgeber" in source:
            #    source = "Ratgeber"

            items_by_source[source].append(item)

        logger.debug(f"Items gruppiert: {len(items_by_source)} Quellen gefunden")
        for source, source_items in items_by_source.items():
            logger.debug(f"  - {source}: {len(source_items)} Items")

        return items_by_source

    def _pick_balanced_items(
        self, items: List[Dict[str, Any]], category: str, n: int = 12, items_per_source: int = 4
    ) -> List[Dict[str, Any]]:
        """
        Wählt Items aus, wobei aus jeder Quelle gleichmäßig gewählt wird.

        Args:
            items: Liste aller verfügbaren Items
            category: Kategorie ('films', 'albums', 'books')
            n: Gesamtanzahl gewünschter Items
            items_per_source: Items pro Quelle (default: 4)

        Returns:
            Liste der ausgewählten Items, balanciert nach Quelle
        """
        logger.info(f"Wähle {n} balancierte Items für '{category}' " f"({items_per_source} pro Quelle)")

        # Gruppiere Items nach Quelle
        items_by_source = self._get_items_by_source(items)

        if not items_by_source:
            logger.warning(f"Keine Items für '{category}' gefunden")
            return []

        selected_items: List[Dict[str, Any]] = []
        sources = list(items_by_source.keys())

        # Reset Source Counts für neue Empfehlungsrunde
        current_counts: Dict[str, int] = defaultdict(int)

        # Durchlaufe Quellen round-robin bis genug Items gefunden
        source_index = 0
        max_iterations = n * len(sources) * 2  # Sicherheit gegen Endlosschleife
        iterations = 0

        while len(selected_items) < n and iterations < max_iterations:
            iterations += 1

            # Wähle nächste Quelle
            current_source = sources[source_index % len(sources)]
            source_items = items_by_source[current_source]

            # Prüfe ob diese Quelle schon genug Items beigetragen hat
            if current_counts[current_source] >= items_per_source:
                source_index += 1
                continue

            # Durchsuche Items dieser Quelle
            found_item = False
            for item in source_items:
                # Überspringe bereits vorgeschlagene oder geblacklistete Items
                if self.state.is_already_suggested(category, item):
                    continue
                if self.blacklist.is_blacklisted(category, item):
                    continue

                # Prüfe Verfügbarkeit in Bibliothek
                available_item = self._check_availability(item, category)

                if available_item:
                    selected_items.append(available_item)
                    current_counts[current_source] += 1
                    self.state.mark_suggested(category, item)

                    logger.info(
                        f"✅ '{item['title']}' von Quelle '{current_source}' "
                        f"(Count: {current_counts[current_source]}/{items_per_source})"
                    )

                    found_item = True
                    break

            # Wenn kein Item gefunden, markiere Quelle als erschöpft
            if not found_item:
                # Entferne erschöpfte Quelle
                if current_source in sources:
                    logger.debug(f"Quelle '{current_source}' erschöpft, entferne aus Rotation")
                    sources.remove(current_source)

                    if not sources:
                        logger.warning("Alle Quellen erschöpft")
                        break

            source_index += 1

        # Logging der finalen Verteilung
        logger.info(f"Balancierte Auswahl abgeschlossen: {len(selected_items)}/{n} Items")
        for source, count in current_counts.items():
            logger.info(f"  - {source}: {count} Items")

        return selected_items

    def _check_availability(self, item: Dict[str, Any], category: str) -> Optional[Dict[str, Any]]:
        """
        Prüft ob ein Medium in der Bibliothek verfügbar ist.

        NEU: Fügt entliehene Medien zur Entleih-Blacklist hinzu.

        Für Filme: Filtert Nicht-Filme anhand des "Uv" Kürzels aus.
        Alle Verfügbarkeitsangaben werden auf 300 Zeichen begrenzt.

        Args:
            item: Medium-Dictionary mit title, author, type
            category: Kategorie ('films', 'albums', 'books')

        Returns:
            Item-Dictionary mit Verfügbarkeitsinfo oder None falls nicht verfügbar
        """
        media_type: str = item.get("type", "")

        # Prüfe zuerst Entleih-Blacklist
        borrowed_blacklist = get_borrowed_blacklist()
        if borrowed_blacklist.is_blacklisted(item.get("title", ""), item.get("author", "")):
            logger.debug(f"'{item['title']}' ist entliehen - überspringe Suche")
            return None

        if media_type == "Buch":
            query = f"{item.get('author', '')} {item.get('title')} {media_type}".strip()
        else:
            query = f"{item.get('title')} {item.get('author', '')} {media_type}".strip()

        logger.debug(f"Suche nach: '{query}'")
        hits: List[Dict[str, Any]] = self.library_search.search(query)

        # Keine Treffer → Blacklist
        if not hits or len(hits) == 0:
            logger.info(f"⚫ Keine Treffer für '{item['title']}' - wird geblacklistet")
            self.blacklist.add_to_blacklist(category, item, reason="Keine Treffer in Bibliothekskatalog")
            return None

        # Spezielle Filterung für Filme: Prüfe auf "Uv" Kürzel
        if category == "films":
            logger.debug("Filtere Filme nach 'Uv' Kürzel")
            film_hits = []

            for hit in hits:
                zentralbib_info = hit.get("zentralbibliothek_info", "")

                # Prüfe auf "Uv" ohne Wortgrenzen
                has_uv = bool(re.search(r"Uv", zentralbib_info))

                if has_uv:
                    film_hits.append(hit)
                    logger.debug(f"Film bestätigt: {hit.get('title', 'Unknown')}")
                else:
                    logger.debug(f"Kein Film (fehlendes Uv): {hit.get('title', 'Unknown')}")

            # Wenn keine Film-Treffer, auf Blacklist
            if not film_hits:
                logger.info(f"⚫ Keine Film-Treffer für '{item['title']}' " "(kein 'Uv' Kürzel) - wird geblacklistet")
                self.blacklist.add_to_blacklist(category, item, reason="Keine Film-Treffer (fehlendes Uv Kürzel)")
                return None

            # Verwende nur Film-Treffer
            hits = film_hits

        # Prüfen auf verfügbar UND entliehen
        available: List[Dict[str, Any]] = []
        borrowed: List[Dict[str, Any]] = []

        for hit in hits:
            zentralbib_info = hit.get("zentralbibliothek_info", "")

            if "verfügbar" in zentralbib_info.lower():
                available.append(hit)
            elif "entliehen" in zentralbib_info.lower():
                borrowed.append(hit)

        # NEU: Entliehene auf Entleih-Blacklist
        if borrowed:
            for borrowed_item in borrowed:
                zentralbib_info = borrowed_item.get("zentralbibliothek_info", "")

                success = borrowed_blacklist.add_to_blacklist(
                    title=borrowed_item.get("title", item.get("title", "")),
                    author=item.get("author", ""),
                    media_type=media_type,
                    availability_text=zentralbib_info,
                )

                if success:
                    logger.debug(f"📅 Auf Entleih-Blacklist: {borrowed_item.get('title', '')}")

        # Prüfe verfügbare
        if available:
            # Alle Verfügbarkeits-Infos zusammenfassen
            infos: List[str] = [h["zentralbibliothek_info"] for h in hits if "zentralbibliothek_info" in h]

            # Kombiniere und kürze auf 300 Zeichen
            combined_info = ", ".join(infos)
            truncated_info = Recommender._truncate_text(combined_info, max_length=300)

            # Kopiere das Item und füge bib_number hinzu
            result_item: Dict[str, Any] = item.copy()
            result_item["bib_number"] = truncated_info

            logger.debug(f"Verfügbarkeit gekürzt: {len(combined_info)} -> " f"{len(truncated_info)} Zeichen")

            return result_item

        logger.debug(f"'{item['title']}' nicht verfügbar (alle entliehen)")
        return None

    @staticmethod
    def _truncate_text(text: str, max_length: int = 400) -> str:
        """
        Kürzt Text auf maximale Länge.

        Args:
            text: Zu kürzender Text
            max_length: Maximale Länge (default: 400)

        Returns:
            Gekürzter Text mit "..." falls nötig
        """
        if not text or len(text) <= max_length:
            return text

        return text[: max_length - 3].strip() + "..."

    def suggest_films(self, films: List[Dict[str, Any]], n: int = 12, items_per_source: int = 4) -> List[Dict[str, Any]]:
        """
        Wählt verfügbare Filme aus, balanciert nach Quellen.

        Stellt sicher, dass aus jeder Quelle (BBC, FBW, Oscar) gleichmäßig
        Filme vorgeschlagen werden.

        Args:
            films: Liste von Filmen mit Titeln, Autoren und Typ
            n: Gesamtanzahl gewünschter Vorschläge (default: 12)
            items_per_source: Items pro Quelle (default: 4)

        Returns:
            Liste der vorgeschlagenen Filme, balanciert nach Quelle
        """
        logger.info(f"Erstelle {n} balancierte Filmvorschläge " f"({items_per_source} pro Quelle)")
        return self._pick_balanced_items(films, "films", n, items_per_source)

    def suggest_albums(self, albums: List[Dict[str, Any]], n: int = 12, items_per_source: int = 4) -> List[Dict[str, Any]]:
        """
        Wählt verfügbare Musikalben aus, balanciert nach Quellen.

        Stellt sicher, dass aus jeder Quelle (Radio Eins, Oscar, Personalisiert)
        gleichmäßig Alben vorgeschlagen werden.

        Args:
            albums: Liste von Alben mit Titel, Künstler und Typ
            n: Gesamtanzahl gewünschter Vorschläge (default: 12)
            items_per_source: Items pro Quelle (default: 4)

        Returns:
            Liste der vorgeschlagenen Alben, balanciert nach Quelle
        """
        logger.info(f"Erstelle {n} balancierte Albumvorschläge " f"({items_per_source} pro Quelle)")
        return self._pick_balanced_items(albums, "albums", n, items_per_source)

    def suggest_books(self, books: List[Dict[str, Any]], n: int = 12, items_per_source: int = 4) -> List[Dict[str, Any]]:
        """
        Wählt verfügbare Bücher aus, balanciert nach Quellen.

        Stellt sicher, dass aus jeder Quelle (NYT Kanon, Ratgeber)
        gleichmäßig Bücher vorgeschlagen werden.

        Args:
            books: Liste von Büchern mit Titel, Autor und Typ
            n: Gesamtanzahl gewünschter Vorschläge (default: 12)
            items_per_source: Items pro Quelle (default: 4)

        Returns:
            Liste der vorgeschlagenen Bücher, balanciert nach Quelle
        """
        logger.info(f"Erstelle {n} balancierte Buchvorschläge " f"({items_per_source} pro Quelle)")
        return self._pick_balanced_items(books, "books", n, items_per_source)
