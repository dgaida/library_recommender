#!/usr/bin/env python3
"""
Recommender-System für Bibliotheksmedien mit ausgewogener Quellenverteilung

Dieses Modul stellt sicher, dass Empfehlungen gleichmäßig aus allen verfügbaren
Datenquellen stammen (z.B. 5 Filme von BBC, 5 von FBW, 5 von Oscar).
"""

import re
import random
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
    Medien vorgeschlagen werden (z.B. 5 pro Quelle).
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

    def _pick_balanced_items(  # noqa: C901
        self, items: List[Dict[str, Any]], category: str, n: int = 25, items_per_source: int = 5
    ) -> List[Dict[str, Any]]:
        """
        Wählt Items aus, wobei aus jeder Quelle gleichmäßig gewählt wird.

        Args:
            items: Liste aller verfügbaren Items
            category: Kategorie ('films', 'albums', 'books')
            n: Gesamtanzahl gewünschter Items (default: 25)
            items_per_source: Items pro Quelle (default: 5)

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
            random.shuffle(source_items)

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
        status = {
            "zentralbib_available": False,
            "zentralbib_exists": False,
            "stadtbib_available_list": [],
            "borrowed_items": [],
            "onleihe_link": None,
            "onleihe_text": "",
        }

        for hit in hits:
            detail_url = hit.get("link", "")
            if not detail_url:
                continue

            availability_dict = self.library_search.get_availability_details(detail_url)
            if not availability_dict:
                continue

            logger.debug(f"Prüfe {len(availability_dict)} Standorte für '{item['title']}'")
            self._process_availability_dict(hit, availability_dict, status)

        # Entliehene Items auf Borrowed-Blacklist
        if status["borrowed_items"]:
            for borrowed_item in status["borrowed_items"]:
                borrowed_blacklist.add_to_blacklist(
                    title=borrowed_item["title"],
                    author=item.get("author", ""),
                    media_type=item.get("type", ""),
                    availability_text=borrowed_item["info"],
                )
                logger.debug(f"📅 Auf Borrowed-Blacklist: {borrowed_item['title']}")

        return (
            status["zentralbib_available"],
            status["zentralbib_exists"],
            status["stadtbib_available_list"],
            status["borrowed_items"],
            status["onleihe_link"],
            status["onleihe_text"],
        )

    def _process_availability_dict(self, hit: Dict[str, Any], availability_dict: Dict[str, Any], status: Dict[str, Any]):
        """Hilfsfunktion zum Verarbeiten des Verfügbarkeits-Dictionaries."""
        # Prüfe Onleihe-Link
        if "_onleihe_link" in availability_dict and not status["onleihe_link"]:
            status["onleihe_link"] = availability_dict["_onleihe_link"]
            status["onleihe_text"] = availability_dict.get("_onleihe_text", "")
            logger.debug(f"📱 Onleihe-Link in Details gefunden: {status['onleihe_link']}")

        for location_key, availability_text in availability_dict.items():
            if location_key.endswith("_full") or location_key.startswith("_"):
                continue

            location_lower = location_key.lower()
            if "zentralbibliothek" in location_lower:
                status["zentralbib_exists"] = True
                if "verfügbar" in availability_text.lower() and "entliehen" not in availability_text.lower():
                    status["zentralbib_available"] = True
                    logger.debug("✅ Zentralbib VERFÜGBAR")
                elif "entliehen" in availability_text.lower():
                    status["borrowed_items"].append({"title": hit.get("title", ""), "info": availability_text})
                    logger.debug("📅 Zentralbib ENTLIEHEN")
            else:
                self._process_stadtbib_availability(location_lower, availability_text, status)

    def _process_stadtbib_availability(self, location_lower: str, availability_text: str, status: Dict[str, Any]):
        """Hilfsfunktion zum Verarbeiten der Stadtteilbibliothek-Verfügbarkeit."""
        for stadtbib in STADTTEILBIBLIOTHEKEN.keys():
            stadtbib_short = stadtbib.replace("stadtteilbibliothek ", "")
            if stadtbib_short in location_lower:
                if "verfügbar" in availability_text.lower() and "entliehen" not in availability_text.lower():
                    status["stadtbib_available_list"].append({"location": stadtbib, "info": availability_text})
                    logger.debug(f"✅ {stadtbib} verfügbar")
                break

    def _check_availability(self, item: Dict[str, Any], category: str) -> Optional[Dict[str, Any]]:
        logger.info(f"Prüfe Verfügbarkeit für: '{item['title']}' von '{item.get('author', 'Unbekannt')}'")
        """Prüft Verfügbarkeit eines Mediums in der Bibliothek."""
        # Prüfe Entleih-Blacklist
        borrowed_blacklist = get_borrowed_blacklist()
        if borrowed_blacklist.is_blacklisted(item.get("title", ""), item.get("author", "")):
            logger.debug(f"'{item['title']}' ist entliehen - überspringe")
            return None

        # Suche und Filterung
        hits = self._search_and_filter_hits(item, category)
        if not hits:
            return None

        # Verfügbarkeits-Status aus allen Bibs
        res = self._check_all_bibs(item, hits, borrowed_blacklist)
        z_av, z_ex, s_av, b_items, o_link, o_text = res

        logger.info(f"Verfügbarkeit für '{item['title']}': Z_EX={z_ex}, Z_AV={z_av}, S_AV={len(s_av)}, ON={bool(o_link)}")

        # Entscheidungs-Logik
        if o_link:
            return self._create_digital_item(item, o_link, o_text)

        if z_av:
            return self._create_zentralbib_item(item, hits)

        if z_ex and s_av:
            logger.info("⏳ In Zentralbib (entliehen) + Stadtbib verfügbar → SKIP")
            return None

        if not z_ex and s_av:
            return self._create_stadtbib_item(item, s_av[0])

        if not b_items:
            logger.info("⚫ Nichts verfügbar → Blacklist")
            self.blacklist.add_to_blacklist(category, item, reason="Nicht verfügbar")

        return None

    def _search_and_filter_hits(self, item: Dict[str, Any], category: str) -> Optional[List[Dict[str, Any]]]:
        """Sucht Titel und wendet Autor/Film-Filter an."""
        media_type = item.get("type", "")
        if media_type == "Buch":
            query = f"{item.get('author', '')} {item.get('title')} {media_type}".strip()
        else:
            query = f"{item.get('title')} {item.get('author', '')} {media_type}".strip()

        hits = self.library_search.search(query)
        if not hits:
            self.blacklist.add_to_blacklist(category, item, reason="Keine Treffer")
            return None

        filtered = self._filter_hits_author(item, category, hits)
        if filtered is None:
            return None
        hits = filtered if filtered else hits

        if category == "films":
            hits = self._filter_film_uv(item, category, hits)

        return hits

    def _create_digital_item(self, item: Dict[str, Any], onleihe_link: str, onleihe_text: str) -> Dict[str, Any]:
        """Erstellt ein Item-Dictionary für digitale Verfügbarkeit."""
        logger.info("📱 Onleihe verfügbar → digitale Empfehlung")
        result_item = item.copy()
        result_item["title"] = f"📱 {item['title']}"
        result_item["onleihe_link"] = onleihe_link
        result_item["onleihe_text"] = onleihe_text
        result_item["bib_number"] = f"Digital verfügbar bei Onleihe: {onleihe_text}"
        return result_item

    def _create_zentralbib_item(self, item: Dict[str, Any], hits: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Erstellt ein Item-Dictionary für Zentralbibliothek-Verfügbarkeit."""
        logger.info("✅ Zentralbibliothek verfügbar → normale Empfehlung")
        for hit in hits:
            detail_url = hit.get("link", "")
            if detail_url:
                zentralbib_info = self.library_search.get_zentralbibliothek_info(detail_url, return_full=False)
                if zentralbib_info:
                    result_item = item.copy()
                    result_item["bib_number"] = self._truncate_text(zentralbib_info, 300)
                    return result_item
        result_item = item.copy()
        result_item["bib_number"] = "Verfügbar in Zentralbibliothek"
        return result_item

    def _create_stadtbib_item(self, item: Dict[str, Any], stadtbib_info_dict: Dict[str, Any]) -> Dict[str, Any]:
        """Erstellt ein Item-Dictionary für Stadtteilbibliothek-Verfügbarkeit."""
        location = stadtbib_info_dict["location"]
        info = stadtbib_info_dict["info"]
        abbreviation = get_stadtbib_abbreviation(location)
        result_item = item.copy()
        result_item["title"] = f"{item['title']} ({abbreviation})"
        result_item["bib_number"] = self._truncate_text(info, 300)
        logger.info(f"✅ Empfehle mit Suffix: '{result_item['title']}'")
        return result_item

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

    def suggest_films(self, films: List[Dict[str, Any]], n: int = 25, items_per_source: int = 5) -> List[Dict[str, Any]]:
        """
        Wählt verfügbare Filme aus, balanciert nach Quellen.

        Stellt sicher, dass aus jeder Quelle (BBC, FBW, Oscar, IMDb) gleichmäßig
        Filme vorgeschlagen werden.

        Args:
            films: Liste von Filmen mit Titeln, Autoren und Typ
            n: Gesamtanzahl gewünschter Vorschläge (default: 25)
            items_per_source: Items pro Quelle (default: 5)

        Returns:
            Liste der vorgeschlagenen Filme, balanciert nach Quelle
        """
        logger.info(f"Erstelle {n} balancierte Filmvorschläge " f"({items_per_source} pro Quelle)")
        return self._pick_balanced_items(films, "films", n, items_per_source)

    def suggest_albums(self, albums: List[Dict[str, Any]], n: int = 25, items_per_source: int = 5) -> List[Dict[str, Any]]:
        """
        Wählt verfügbare Musikalben aus, balanciert nach Quellen.

        Stellt sicher, dass aus jeder Quelle (Radio Eins, Oscar, Personalisiert)
        gleichmäßig Alben vorgeschlagen werden.

        Args:
            albums: Liste von Alben mit Titel, Künstler und Typ
            n: Gesamtanzahl gewünschter Vorschläge (default: 25)
            items_per_source: Items pro Quelle (default: 5)

        Returns:
            Liste der vorgeschlagenen Alben, balanciert nach Quelle
        """
        logger.info(f"Erstelle {n} balancierte Albumvorschläge " f"({items_per_source} pro Quelle)")
        return self._pick_balanced_items(albums, "albums", n, items_per_source)

    def suggest_books(self, books: List[Dict[str, Any]], n: int = 25, items_per_source: int = 5) -> List[Dict[str, Any]]:
        """
        Wählt verfügbare Bücher aus, balanciert nach Quellen.

        Stellt sicher, dass aus jeder Quelle (NYT Kanon, Ratgeber)
        gleichmäßig Bücher vorgeschlagen werden.

        Args:
            books: Liste von Büchern mit Titel, Autor und Typ
            n: Gesamtanzahl gewünschter Vorschläge (default: 25)
            items_per_source: Items pro Quelle (default: 5)

        Returns:
            Liste der vorgeschlagenen Bücher, balanciert nach Quelle
        """
        logger.info(f"Erstelle {n} balancierte Buchvorschläge " f"({items_per_source} pro Quelle)")
        return self._pick_balanced_items(books, "books", n, items_per_source)
