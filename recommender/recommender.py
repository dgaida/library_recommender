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
from library.search import filter_results_by_author
from utils.stadtbib_config import get_stadtbib_abbreviation, STADTTEILBIBLIOTHEKEN

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

            # Prüfe, ob diese Quelle schon genug Items beigetragen hat
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

    def _filter_film_uv(self, item: Dict[str, Any], category: str, hits):
        logger.debug("Filtere Filme nach 'Uv' Kürzel")
        film_hits = []

        for hit in hits:
            zentralbib_info = hit.get("zentralbibliothek_info", "")
            if re.search(r"Uv", zentralbib_info):
                film_hits.append(hit)
            else:
                logger.debug(f"Kein Film (kein Uv): {hit.get('title', 'Unknown')}")

        if not film_hits:
            logger.info(f"⚫ Keine Film-Treffer für '{item['title']}' - Blacklist")
            self.blacklist.add_to_blacklist(category, item, reason="Keine Film-Treffer")
            return None

        return film_hits

    def _filter_hits_author(self, item: Dict[str, Any], category: str, hits):
        expected_author = item.get("author", "")
        expected_title = item.get("title", "")
        filtered_hits = []

        if expected_author:
            logger.info(f"Filtere nach Autor '{expected_author}' + Titel '{expected_title}'")

            filtered_hits = filter_results_by_author(hits, expected_author, expected_title=expected_title, threshold=0.7)

            if filtered_hits:
                logger.info(f"Nach Filter: {len(filtered_hits)} Treffer")
            else:
                logger.warning("Filter entfernte alle Treffer")
                self.blacklist.add_to_blacklist(category, item, reason="Keine exakten Treffer")
                return None

        return filtered_hits

    def _check_all_bibs(self, item: Dict[str, Any], hits, borrowed_blacklist):
        # Tracking
        zentralbib_available = False
        zentralbib_exists = False
        stadtbib_available_list = []  # Liste von (location, info) Tupeln
        borrowed_items = []

        for hit in hits:
            # Hole VOLLSTÄNDIGE Verfügbarkeitsinfos von Detailseite
            detail_url = hit.get("link", "")
            if not detail_url:
                continue

            # WICHTIG: Nutze get_availability_details() für ALLE Standorte
            availability_dict = self.library_search.get_availability_details(detail_url)

            if not availability_dict:
                continue

            logger.debug(f"Prüfe {len(availability_dict)} Standorte für '{item['title']}'")

            # Iteriere über ALLE Standorte im Dictionary
            for location_key, availability_text in availability_dict.items():
                # Überspringe interne Keys
                if location_key.endswith("_full"):
                    continue

                location_lower = location_key.lower()

                # Prüfe ob Zentralbibliothek
                if "zentralbibliothek" in location_lower:
                    zentralbib_exists = True

                    # Prüfe Verfügbarkeit
                    if "verfügbar" in availability_text.lower() and "entliehen" not in availability_text.lower():
                        zentralbib_available = True
                        logger.debug("✅ Zentralbib VERFÜGBAR")
                    elif "entliehen" in availability_text.lower():
                        # Zur Entleih-Blacklist
                        borrowed_items.append({"title": hit.get("title", item.get("title", "")), "info": availability_text})
                        logger.debug("📅 Zentralbib ENTLIEHEN")
                else:
                    # Prüfe Stadtteilbibliotheken
                    is_stadtbib = False
                    normalized_location = None

                    for stadtbib in STADTTEILBIBLIOTHEKEN.keys():
                        stadtbib_short = stadtbib.replace("stadtteilbibliothek ", "")
                        if stadtbib_short in location_lower:
                            is_stadtbib = True
                            normalized_location = stadtbib
                            break

                    if is_stadtbib and normalized_location:
                        # Prüfe Verfügbarkeit
                        if "verfügbar" in availability_text.lower() and "entliehen" not in availability_text.lower():
                            stadtbib_available_list.append({"location": normalized_location, "info": availability_text})
                            logger.debug(f"✅ {normalized_location} verfügbar")

        # Entliehene Items auf Borrowed-Blacklist
        if borrowed_items:
            for borrowed_item in borrowed_items:
                borrowed_blacklist.add_to_blacklist(
                    title=borrowed_item["title"],
                    author=item.get("author", ""),
                    media_type=item.get("type", ""),
                    availability_text=borrowed_item["info"],
                )
                logger.debug(f"📅 Auf Borrowed-Blacklist: {borrowed_item['title']}")

        return zentralbib_available, zentralbib_exists, stadtbib_available_list, borrowed_items

    def _check_availability(self, item: Dict[str, Any], category: str) -> Optional[Dict[str, Any]]:
        """
        Prüft, ob ein Medium in der Bibliothek verfügbar ist.

        Logik:
        1. Wenn Zentralbib verfügbar → normale Empfehlung
        2. Wenn NUR Stadtbib verfügbar → Empfehlung mit Suffix
        3. Wenn Zentralbib UND Stadtbib, aber nur Stadtbib verfügbar → SKIP
        4. Wenn nichts verfügbar → Blacklist

        Für Filme: Filtert Nicht-Filme anhand des "Uv" Kürzels aus.
        Alle Verfügbarkeitsangaben werden auf 300 Zeichen begrenzt.

        Args:
            item: Medium-Dictionary mit title, author, type
            category: Kategorie ('films', 'albums', 'books')

        Returns:
            Item-Dictionary mit Verfügbarkeitsinfo oder None falls nicht verfügbar
        """
        media_type: str = item.get("type", "")

        # Prüfe Entleih-Blacklist
        borrowed_blacklist = get_borrowed_blacklist()
        if borrowed_blacklist.is_blacklisted(item.get("title", ""), item.get("author", "")):
            logger.debug(f"'{item['title']}' ist entliehen - überspringe")
            return None

        # Baue Suchquery
        if media_type == "Buch":
            query = f"{item.get('author', '')} {item.get('title')} {media_type}".strip()
        else:
            query = f"{item.get('title')} {item.get('author', '')} {media_type}".strip()

        logger.debug(f"Suche: '{query}'")

        # Suche durchführen
        hits: List[Dict[str, Any]] = self.library_search.search(query)

        if not hits:
            logger.info(f"⚫ Keine Treffer für '{item['title']}' - Blacklist")
            self.blacklist.add_to_blacklist(category, item, reason="Keine Treffer")
            return None

        # Autor-Filterung
        filtered_hits = self._filter_hits_author(item, category, hits)
        if len(filtered_hits) > 0:
            hits = filtered_hits

        # Film-Filterung (UV-Kürzel)
        if category == "films":
            hits = self._filter_film_uv(item, category, hits)

        if hits is None:
            return None

        # ===================================================================
        # KERN-LOGIK: Parse Verfügbarkeit aus ALLEN Standorten
        # ===================================================================

        zentralbib_available, zentralbib_exists, stadtbib_available_list, borrowed_items = self._check_all_bibs(
            item, hits, borrowed_blacklist
        )

        # ===================================================================
        # ENTSCHEIDUNGS-LOGIK (FIXED!)
        # ===================================================================

        logger.info(f"Verfügbarkeit für '{item['title']}':")
        logger.info(f"  Zentralbib existiert: {zentralbib_exists}")
        logger.info(f"  Zentralbib verfügbar: {zentralbib_available}")
        logger.info(f"  Stadtbibs verfügbar: {len(stadtbib_available_list)}")

        # Fall 1: Zentralbib verfügbar → normale Empfehlung ✅
        if zentralbib_available:
            logger.info("✅ Zentralbib verfügbar → normale Empfehlung")

            # Hole Zentralbib-Info aus erstem Hit
            for hit in hits:
                detail_url = hit.get("link", "")
                if detail_url:
                    zentralbib_info = self.library_search.get_zentralbibliothek_info(detail_url, return_full=False)
                    if zentralbib_info:
                        result_item = item.copy()
                        result_item["bib_number"] = self._truncate_text(zentralbib_info, 300)
                        return result_item

            # Fallback (sollte nicht erreicht werden)
            result_item = item.copy()
            result_item["bib_number"] = "Verfügbar in Zentralbibliothek"
            return result_item

        # Fall 2: Existiert in Zentralbib (aber entliehen) UND in Stadtbib verfügbar
        # → SKIP (warte auf Zentralbib) ⏳
        if zentralbib_exists and stadtbib_available_list:
            logger.info("⏳ In Zentralbib (entliehen) + Stadtbib verfügbar → SKIP")
            return None  # NICHT auf Blacklist, nur überspringen

        # Fall 3: NICHT in Zentralbib, aber in Stadtbib verfügbar
        # → Empfehlung mit Suffix 📍
        if not zentralbib_exists and stadtbib_available_list:
            logger.info("📍 Nur in Stadtbib verfügbar → mit Suffix")

            # Nimm erste verfügbare Stadtbib
            first_stadtbib = stadtbib_available_list[0]
            location = first_stadtbib["location"]
            stadtbib_info = first_stadtbib["info"]

            # Hole Abkürzung
            abbreviation = get_stadtbib_abbreviation(location)

            # Titel mit Suffix
            modified_title = f"{item['title']} ({abbreviation})"

            result_item = item.copy()
            result_item["title"] = modified_title
            result_item["bib_number"] = self._truncate_text(stadtbib_info, 300)

            logger.info(f"✅ Empfehle mit Suffix: '{modified_title}'")
            return result_item

        # Fall 4: Nichts verfügbar → Blacklist ⚫
        # (Nur wenn NICHT schon auf Borrowed-Blacklist)
        if not borrowed_items:
            logger.info("⚫ Nichts verfügbar → Blacklist")
            self.blacklist.add_to_blacklist(category, item, reason="Nicht verfügbar")
        else:
            logger.info("📅 Nur entliehen → auf Borrowed-Blacklist, kein normaler Blacklist")

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
