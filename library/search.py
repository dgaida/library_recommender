#!/usr/bin/env python3
"""
Stadtbibliothek Köln Katalog Suche
Programm zur Suche im Online-Katalog der Stadtbibliothek Köln
"""

import requests
from bs4 import BeautifulSoup
import urllib.parse
import re
import time
import random
from typing import Dict, List, Optional, Any
from utils.logging_config import get_logger

logger = get_logger(__name__)


class KoelnLibrarySearch:
    """Suchengine für die Stadtbibliothek Köln."""

    def __init__(self) -> None:
        """Initialisiert die Suchengine mit Basis-URLs und Session."""
        self.base_url: str = "https://katalog.stbib-koeln.de"
        self.search_url: str = f"{self.base_url}/alswww2.dll/APS_ZONES"
        self.session: requests.Session = requests.Session()
        self.session.headers.update({
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                          "AppleWebKit/537.36 (KHTML, like Gecko) "
                          "Chrome/91.0.4472.124 Safari/537.36"
        })

    def advanced_search(
            self,
            title: Optional[str] = None,
            author: Optional[str] = None,
            subject: Optional[str] = None,
            year: Optional[str] = None,
            page_size: int = 20
    ) -> List[Dict[str, Any]]:
        """
        Führt eine erweiterte Suche im Bibliothekskatalog durch.

        Args:
            title: Titel des Mediums
            author: Name/Autor
            subject: Schlagwort
            year: Erscheinungsjahr
            page_size: Anzahl der Ergebnisse pro Seite

        Returns:
            Liste der Suchergebnisse
        """
        query_parts: List[str] = []

        if title:
            query_parts.append(f"( Titel= {title} )")
        if author:
            query_parts.append(f"( Name= {author} )")
        if subject:
            query_parts.append(f"( Schlagwort= {subject} )")
        if year:
            query_parts.append(f"( Jahr= {year} )")

        query_string: str = " Und ".join(query_parts)
        return self._advanced_search(query_string, page_size)

    def _advanced_search(
            self,
            query: str,
            page_size: int = 20,
            verbose: bool = False
    ) -> List[Dict[str, Any]]:
        """
        Führt eine erweiterte Suche mit ExpertQuery durch.

        Args:
            query: ExpertQuery wie "( Titel= ... ) Und ( Name= ... )"
            page_size: Anzahl Ergebnisse pro Seite
            verbose: Ausführliches Logging

        Returns:
            Liste der Suchergebnisse
        """
        try:
            logger.info(f"Erweiterte Suche mit Query: {query}")

            form_url = (
                f"{self.base_url}/alswww2.dll/APS_ZONES?fn=AdvancedSearch"
                f"&Style=Portal3&SubStyle=&Lang=GER&ResponseEncoding=utf-8"
            )

            if verbose:
                logger.debug(f"Rufe Formularseite auf: {form_url}")

            main_response = self.safe_get(form_url, timeout=15)
            main_response.raise_for_status()
            logger.debug(f"Hauptseite Status: {main_response.status_code}")

            soup = BeautifulSoup(main_response.text, "html.parser")
            form = soup.find("form", {"name": "AdvancedSearch"})

            if not form:
                logger.warning("Keine AdvancedSearch-Form gefunden")
                return []

            action = form.get("action")
            if not action:
                logger.warning("Kein Action-Link im Formular gefunden")
                return []

            search_url = f"{self.base_url}/alswww2.dll/{action}"
            logger.debug(f"Verwende URL: {search_url}")

            params: Dict[str, str] = {
                "Style": "Portal3",
                "SubStyle": "",
                "Lang": "GER",
                "ResponseEncoding": "utf-8",
                "Method": "QuerySubmit",
                "SearchType": "AdvancedSearch",
                "DB": "SearchServer",
                "q.Query": query,
                "q.PageSize": str(page_size),
            }

            logger.debug(f"Parameter: {params}")

            search_response = self.session.post(search_url, data=params, timeout=15)
            search_response.raise_for_status()

            logger.info("Starte Parsing der Suchergebnisse...")
            return self._parse_results(search_response.text)

        except Exception as e:
            logger.error(f"Fehler in advanced_search: {e}", exc_info=True)
            return []

    def safe_get(self, url: str, **kwargs: Any) -> requests.Response:
        """
        Sendet einen GET-Request mit automatischen Retries und Backoff.

        Args:
            url: Die Ziel-URL für den GET-Request
            **kwargs: Zusätzliche Argumente für session.get()

        Returns:
            Response-Objekt des erfolgreichen Requests

        Raises:
            Exception: Nach drei erfolglosen Versuchen
        """
        for attempt in range(3):
            try:
                response = self.session.get(url, **kwargs)
                response.raise_for_status()
                return response
            except requests.exceptions.HTTPError as e:
                if response.status_code in [429, 503]:
                    wait = (attempt + 1) * 5 + random.random() * 3
                    logger.warning(
                        f"Server-Fehler {response.status_code}, "
                        f"warte {wait:.1f} Sekunden..."
                    )
                    time.sleep(wait)
                    continue
                raise

        error_msg = f"Fehler nach 3 Versuchen für URL: {url}"
        logger.error(error_msg)
        raise Exception(error_msg)

    def search(
            self,
            search_term: str,
            search_type: str = "all",
            verbose: bool = False
    ) -> List[Dict[str, Any]]:
        """
        Führt eine Suche im Bibliothekskatalog durch.

        Args:
            search_term: Der Suchbegriff
            search_type: Art der Suche ('all', 'title', 'author', 'subject')
            verbose: Ausführliches Logging

        Returns:
            Liste der gefundenen Ergebnisse
        """
        params: Dict[str, str] = {
            "Style": "Portal3",
            "SubStyle": "",
            "Lang": "GER",
            "ResponseEncoding": "utf-8",
            "Method": "QueryWithLimits",
            "SearchType": "QuickSearch",
            "DB": "SearchServer",
            "SubDB": "",
            "q.Query": search_term,
            "q.PageSize": "20",
        }

        try:
            logger.info(f"Suche nach: '{search_term}'")

            search_url, _ = self._prepare_search_request(params, fn="QuickSearch")

            full_url = f"{search_url}?" + urllib.parse.urlencode(params)
            if verbose:
                logger.debug(f"Vollständige URL: {full_url}")

            search_response = self.session.get(search_url, params=params, timeout=15)
            search_response.raise_for_status()

            if verbose:
                logger.debug(f"HTTP Status Code: {search_response.status_code}")
                logger.debug(f"Response URL: {search_response.url}")
                logger.debug(f"Response Length: {len(search_response.text)} Zeichen")

            if "Ergebnisse" not in search_response.text:
                soup = BeautifulSoup(search_response.text, "html.parser")
                error_advice_table = soup.find("table", {"id": "ErrorAdvice"})
                no_hits_text = (
                        "Leider wurden keine Titel zu Ihrer Suchanfrage gefunden."
                        in search_response.text
                )

                if error_advice_table or no_hits_text:
                    logger.info("Keine Treffer laut Fehlermeldung gefunden")
                    return []
                else:
                    logger.debug("Anscheinend auf Startseite - versuche POST-Request")
                    search_response = self.session.post(
                        search_url, data=params, timeout=15
                    )
                    search_response.raise_for_status()
                    logger.debug(f"POST Status Code: {search_response.status_code}")

            return self._parse_results(search_response.text)

        except requests.exceptions.RequestException as e:
            logger.error(f"Fehler beim Zugriff auf die Webseite: {e}")
            return []
        except Exception as e:
            logger.error(f"Unerwarteter Fehler: {e}", exc_info=True)
            return []

    def _prepare_search_request(
            self,
            params: Dict[str, str],
            fn: str = "QuickSearch",
            verbose: bool = False
    ) -> tuple[str, requests.Response]:
        """
        Hilfsfunktion zur Vorbereitung der Search-URL.

        Args:
            params: Parameter für die Suche
            fn: Name der Funktion in der Bibliotheks-URL
            verbose: Ausführliches Logging

        Returns:
            Tuple aus (search_url, main_response)
        """
        if verbose:
            logger.debug(f"Rufe Hauptseite auf für fn={fn}")

        main_response = self.safe_get(
            f"{self.search_url}?fn={fn}&Style=Portal3&SubStyle=&Lang=GER"
            f"&ResponseEncoding=utf-8",
            timeout=15
        )
        main_response.raise_for_status()

        if verbose:
            logger.debug(f"Hauptseite Status: {main_response.status_code}")

        soup = BeautifulSoup(main_response.text, "html.parser")
        form = soup.find("form", {"name": "ExpertSearch"})

        if form:
            action = form.get("action")
            if action:
                if verbose:
                    logger.debug(f"Form Action gefunden: {action}")
                search_url = f"{self.base_url}/alswww2.dll/{action}"
            else:
                search_url = self.search_url
        else:
            search_url = self.search_url
            logger.debug("Keine Form gefunden, verwende Standard-URL")

        if verbose:
            logger.debug(f"Verwende URL: {search_url}")
            logger.debug(f"Parameter: {params}")

        return search_url, main_response

    def _parse_results(
            self,
            html_content: str,
            verbose: bool = False
    ) -> List[Dict[str, Any]]:
        """
        Parst die HTML-Ergebnisse und extrahiert die Informationen.

        Args:
            html_content: HTML-Inhalt der Ergebnisseite
            verbose: Ausführliches Logging

        Returns:
            Liste der extrahierten Ergebnisse
        """
        soup = BeautifulSoup(html_content, "html.parser")
        results: List[Dict[str, Any]] = []

        logger.info("Starte Parsing der Suchergebnisse...")

        result_items = soup.find_all(
            "td", class_=["SummaryDataCell", "SummaryDataCellStripe"]
        )

        if verbose:
            logger.debug(
                f"Gefunden {len(result_items)} Elemente mit SummaryDataCell Klassen"
            )

        if not result_items:
            result_items = soup.find_all(
                "tr",
                class_=lambda x: x and (
                        "summary" in x.lower() or "result" in x.lower()
                )
            )
            logger.debug(
                f"Fallback 1: Gefunden {len(result_items)} TR-Elemente "
                f"mit summary/result Klassen"
            )

        if not result_items:
            tables = soup.find_all("table")
            if verbose:
                logger.debug(f"Gefunden {len(tables)} Tabellen")

            for i, table in enumerate(tables):
                rows = table.find_all("tr")
                if verbose:
                    logger.debug(f"Tabelle {i + 1} hat {len(rows)} Zeilen")

                for j, row in enumerate(rows):
                    links = row.find_all("a", class_="SummaryFieldLink")
                    if links:
                        if verbose:
                            logger.debug(
                                f"Zeile {j + 1} in Tabelle {i + 1} "
                                f"hat {len(links)} SummaryFieldLink-Links"
                            )
                        result_items.append(row)
                    else:
                        any_links = row.find_all("a", href=True)
                        if (any_links and len(any_links) >= 1 and
                                len(row.get_text(strip=True)) > 20):
                            result_items.append(row)

        logger.info(
            f"Insgesamt {len(result_items)} potentielle Ergebnis-Elemente gefunden"
        )

        for i, item in enumerate(result_items):
            try:
                logger.debug(f"Verarbeite Element {i + 1}...")
                result_data = self._extract_item_data(item)
                if result_data:
                    if verbose:
                        logger.debug(
                            f"Element {i + 1} erfolgreich extrahiert: "
                            f"{result_data['title'][:50]}..."
                        )
                    results.append(result_data)
                else:
                    logger.debug(f"Element {i + 1} lieferte keine Daten")
            except Exception as e:
                logger.warning(f"Fehler beim Parsen von Element {i + 1}: {e}")
                continue

        return results

    def get_availability_details(
            self,
            detail_url: str,
            verbose: bool = False
    ) -> Dict[str, Any]:
        """
        Ruft die Detailseite auf und extrahiert Bestandsinformationen.

        Args:
            detail_url: URL zur Detailseite
            verbose: Ausführliches Logging

        Returns:
            Bestandsinformationen mit Standort als Key
        """
        if not detail_url or detail_url.strip().lower().startswith("javascript:"):
            logger.debug(f"Ungültige Detail-URL übersprungen: {detail_url}")
            return {}

        try:
            if verbose:
                logger.debug(f"Rufe Detailseite auf: {detail_url}")

            detail_response = self.safe_get(detail_url, timeout=10)

            if verbose:
                logger.debug(f"Detailseite Status Code: {detail_response.status_code}")
                logger.debug(f"Response URL (nach Redirects): {detail_response.url}")
                logger.debug(f"Detailseite Länge: {len(detail_response.text)} Zeichen")

            detail_response.raise_for_status()

            soup = BeautifulSoup(detail_response.text, "html.parser")
            availability_info: Dict[str, Any] = {}

            # Methode 1: Suche nach div-Elementen mit "stock_header_" ID
            stock_headers = soup.find_all("div", id=lambda x: x and "stock_header" in x)

            if verbose:
                logger.debug(f"Gefunden {len(stock_headers)} stock_header divs")

            locations = [
                "zentralbibliothek", "ehrenfeld", "kalk", "nippes",
                "rodenkirchen", "chorweiler", "mülheim", "porz"
            ]

            for header_div in stock_headers:
                location_text = header_div.get_text(strip=True)

                if verbose:
                    logger.debug(f"Stock Header: {location_text}")

                if any(loc in location_text.lower() for loc in locations):
                    next_siblings: List[str] = []
                    current = header_div.next_sibling

                    while current:
                        if hasattr(current, "get_text"):
                            text = current.get_text(strip=True)
                            if text and not (
                                    hasattr(current, "get") and
                                    current.get("id") and
                                    "stock_header" in current.get("id")
                            ):
                                if (
                                        "documentManager" in text or
                                        "StockUpdateRequest" in text
                                ):
                                    if verbose:
                                        logger.debug(f"Ignoriere Script-Text: {text}")
                                else:
                                    next_siblings.append(text)
                            elif (
                                    hasattr(current, "get") and
                                    current.get("id") and
                                    "stock_header" in current.get("id")
                            ):
                                break
                        elif isinstance(current, str) and current.strip():
                            next_siblings.append(current.strip())
                        current = current.next_sibling

                    if next_siblings:
                        availability_info[location_text] = next_siblings
                        logger.debug(
                            f"Für {location_text} gefunden: {next_siblings}"
                        )

            # Methode 2: Falls Methode 1 nicht funktioniert, suche nach Tabellen
            if not availability_info:
                print("DEBUG: Fallback - suche nach Tabellen mit Bestandsinfo")
                tables = soup.find_all("table")
                for table in tables:
                    rows = table.find_all("tr")
                    current_location = None

                    for row in rows:
                        cells = row.find_all(["td", "th"])
                        for cell in cells:
                            cell_text = cell.get_text(strip=True)

                            # Prüfe, ob es ein Standort-Header ist
                            if any(loc in cell_text.lower() for loc in ["zentralbibliothek", "ehrenfeld", "kalk", "nippes"]):
                                current_location = cell_text
                                availability_info[current_location] = []
                                print(f"DEBUG: Tabellen-Standort gefunden: {current_location}")

                            # Sammle Informationen für aktuellen Standort
                            elif current_location and cell_text and len(cell_text) > 10:
                                availability_info[current_location].append(cell_text)
                                print(f"DEBUG: Info für {current_location}: {cell_text}")

            # Methode 3: Suche nach allem was nach "Bestand" Header kommt
            if not availability_info:
                print("DEBUG: Fallback - suche nach Bestand-Text")
                bestand_headers = soup.find_all(string=lambda text: text and "bestand" in text.lower())

                for header in bestand_headers:
                    parent = header.parent
                    if parent:
                        # Finde alle nachfolgenden Elemente
                        next_elements = parent.find_all_next(["div", "td", "p", "span"])[:20]  # Limitiere auf 20 Elemente

                        current_location = None
                        for elem in next_elements:
                            elem_text = elem.get_text(strip=True)

                            # print("Methode 3: elem_text", elem_text)

                            if any(loc in elem_text.lower() for loc in ["zentralbibliothek", "ehrenfeld"]):
                                current_location = elem_text
                                availability_info[current_location] = []
                                print(f"DEBUG: Bestand-Standort gefunden: {current_location}")
                            elif current_location and elem_text and len(elem_text) > 5:
                                # Stoppe bei nächstem Standort
                                if not any(loc in elem_text.lower() for loc in ["zentralbibliothek", "ehrenfeld"]):
                                    availability_info[current_location].append(elem_text)
                                    print(f"DEBUG: Bestand-Info für {current_location}: {elem_text[:50]}...")

            if verbose:
                logger.debug(f"Finale availability_info: {availability_info}")

            return availability_info

        except Exception as e:
            logger.error(f"Fehler beim Abrufen der Detailseite: {e}", exc_info=True)
            return {}

    def get_zentralbibliothek_info(self, detail_url: str) -> str:
        """
        Extrahiert speziell die Informationen für die Zentralbibliothek.

        Args:
            detail_url: URL zur Detailseite

        Returns:
            Bestandsinformation der Zentralbibliothek oder leerer String
        """
        availability = self.get_availability_details(detail_url)

        for location, info in availability.items():
            if "zentralbibliothek" in location.lower():
                if isinstance(info, list):
                    return " ".join(info)
                else:
                    return str(info)

        return ""

    def _extract_item_data(
            self,
            item: Any,
            verbose: bool = False
    ) -> Optional[Dict[str, Any]]:
        """
        Extrahiert Daten aus einem einzelnen Suchergebnis.

        Args:
            item: BeautifulSoup-Element eines Suchergebnisses
            verbose: Ausführliches Logging

        Returns:
            Extrahierte Daten oder None
        """
        title_elem = item.find("a", class_="SummaryFieldLink")
        if not title_elem:
            title_elem = item.find("a", href=True)

        title = title_elem.get_text(strip=True) if title_elem else ""
        link = ""

        if title_elem and title_elem.get("href"):
            href = title_elem["href"]

            if href.strip().lower().startswith("javascript:"):
                logger.debug(f"Überspringe ungültigen Link: {href}")
                link = ""
            else:
                if "APS_PRESENT_BIB" in href and "alswww2.dll" not in href:
                    href = "/alswww2.dll/" + href.lstrip("/")

                if href.startswith("/"):
                    link = self.base_url + href
                elif not href.startswith("http"):
                    link = self.base_url + "/" + href
                else:
                    link = href

                if verbose:
                    logger.debug(f"Extrahierter Detail-Link: {link}")

        author = ""
        year = ""
        material_type = ""
        availability = "Unbekannt"

        field_cells = item.find_all("td", class_="SummaryFieldData")
        for cell in field_cells:
            text = cell.get_text(strip=True)
            if text:
                if "," in text and len(text.split()) <= 4:
                    if not author:
                        author = text

                year_match = re.search(r"\b(19|20)\d{2}\b", text)
                if year_match and not year:
                    year = year_match.group()

        material_elem = item.find("td", class_="SummaryMaterialTypeField")
        if material_elem:
            material_type = material_elem.get_text(strip=True)

        avail_elem = item.find("div", class_=["SummaryActionBox", "SummaryActionLink"])
        if avail_elem:
            avail_text = avail_elem.get_text(strip=True)
            if any(
                    word in avail_text.lower()
                    for word in ["verfügbar", "ausleihbar", "vorbestellung"]
            ):
                availability = avail_text

        if title:
            zentralbibliothek_info = self.get_zentralbibliothek_info(link)

            return {
                "title": title,
                "author": author,
                "year": year,
                "material_type": material_type,
                "link": link,
                "availability": availability,
                "zentralbibliothek_info": zentralbibliothek_info,
            }

        return None

    @staticmethod
    def display_results(results: List[Dict[str, Any]]) -> None:
        """
        Zeigt die Suchergebnisse formatiert an.

        Args:
            results: Liste der Suchergebnisse
        """
        if not results:
            logger.info("Keine Ergebnisse gefunden.")
            return

        logger.info(f"\n{len(results)} Ergebnisse gefunden:\n")
        print("-" * 100)

        for i, result in enumerate(results, 1):
            print(f"{i}. {result['title']}")
            if result["author"]:
                print(f"   Autor: {result['author']}")
            if result["year"]:
                print(f"   Jahr: {result['year']}")
            if result["material_type"]:
                print(f"   Medientyp: {result['material_type']}")
            if result["availability"] != "Unbekannt":
                print(f"   Status: {result['availability']}")
            if result.get("zentralbibliothek_info"):
                print(f"   Zentralbibliothek: {result['zentralbibliothek_info']}")
            if result["link"]:
                print(f"   Link: {result['link']}")
            print("-" * 100)
            