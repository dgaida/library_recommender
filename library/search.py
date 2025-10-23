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


class KoelnLibrarySearch:
    def __init__(self):
        self.base_url = "https://katalog.stbib-koeln.de"
        self.search_url = f"{self.base_url}/alswww2.dll/APS_ZONES"
        self.session = requests.Session()
        # User-Agent setzen, um wie ein normaler Browser zu erscheinen
        self.session.headers.update(
            {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
            }
        )

    def advanced_search(self, title=None, author=None, subject=None, year=None, page_size=20):
        """
        Führt eine erweiterte Suche im Bibliothekskatalog durch.

        Args:
            title (str, optional): Titel des Mediums.
            author (str, optional): Name/Autor.
            subject (str, optional): Schlagwort.
            year (str, optional): Erscheinungsjahr.
            page_size (int): Anzahl der Ergebnisse pro Seite.

        Returns:
            list: Liste der Suchergebnisse.
        """
        query_parts = []

        if title:
            query_parts.append(f"( Titel= {title} )")
        if author:
            query_parts.append(f"( Name= {author} )")
        if subject:
            query_parts.append(f"( Schlagwort= {subject} )")
        if year:
            query_parts.append(f"( Jahr= {year} )")

        # Mit "Und" verbinden
        query_string = " Und ".join(query_parts)
        self._advanced_search(query_string, page_size)

    def _advanced_search(self, query, page_size=20, verbose=False):
        """
        Führt eine erweiterte Suche im Bibliothekskatalog durch, analog zur Webseite.
        Args:
            query (str): ExpertQuery wie "( Titel= ... ) Und ( Name= ... )"
        """
        try:
            print(f"DEBUG: Erweiterte Suche mit Query: {query}")

            # Schritt 1: Formularseite laden
            form_url = f"{self.base_url}/alswww2.dll/APS_ZONES?fn=AdvancedSearch&Style=Portal3&SubStyle=&Lang=GER&ResponseEncoding=utf-8"
            if verbose:
                print("DEBUG: Rufe zuerst die Hauptseite auf für fn=AdvancedSearch...")
            main_response = self.safe_get(form_url, timeout=15)
            main_response.raise_for_status()
            print(f"DEBUG: Hauptseite Status: {main_response.status_code}")

            soup = BeautifulSoup(main_response.text, "html.parser")
            form = soup.find("form", {"name": "AdvancedSearch"})
            if not form:
                print("DEBUG: Keine AdvancedSearch-Form gefunden, breche ab.")
                return []

            action = form.get("action")
            if not action:
                print("DEBUG: Kein Action-Link im Formular gefunden.")
                return []

            search_url = f"{self.base_url}/alswww2.dll/{action}"
            print(f"DEBUG: Verwende URL: {search_url}")

            # Schritt 2: Query per POST senden
            params = {
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
            print(f"DEBUG: Parameter: {params}")

            search_response = self.session.post(search_url, data=params, timeout=15)
            search_response.raise_for_status()

            print("DEBUG: Starte Parsing der Suchergebnisse...")
            return self._parse_results(search_response.text)

        except Exception as e:
            print(f"FEHLER in advanced_search: {e}")
            import traceback

            traceback.print_exc()
            return []

    def safe_get(self, url, **kwargs):
        """Sendet einen GET-Request mit automatischen Retries und Backoff.

        Diese Hilfsfunktion führt bis zu drei Versuche durch, um eine URL
        mit der gegebenen Session abzurufen. Falls der Server mit
        HTTP-Status 429 (Too Many Requests) oder 503 (Service Unavailable)
        antwortet, wird eine Wartezeit (exponentielles Backoff mit etwas
        Zufallsanteil) zwischen den Versuchen eingelegt.

        Args:
            url (str): Die Ziel-URL für den GET-Request.
            **kwargs: Zusätzliche Argumente, die an `session.get()` weitergegeben
                werden (z. B. `timeout`, `params`, `headers`).

        Returns:
            requests.Response: Das Response-Objekt des erfolgreichen Requests.

        Raises:
            requests.exceptions.RequestException: Wenn ein Netzwerk- oder
                HTTP-Fehler auftritt, der nicht abgefangen werden konnte.
            Exception: Wenn nach drei Versuchen kein erfolgreicher Request
                durchgeführt werden konnte.

        Example:
            >>> response = search_engine.safe_get("https://example.com", timeout=10)
        """
        for attempt in range(3):
            try:
                response = self.session.get(url, **kwargs)
                response.raise_for_status()
                return response
            except requests.exceptions.HTTPError as e:
                if response.status_code in [429, 503]:
                    wait = (attempt + 1) * 5 + random.random() * 3
                    print(f"DEBUG: Server-Fehler {response.status_code}, warte {wait:.1f} Sekunden...")
                    time.sleep(wait)
                    continue
                raise
        raise Exception(f"Fehler nach 3 Versuchen für URL: {url}")

    def search(self, search_term, search_type="all", verbose=False):
        """
        Führt eine Suche im Bibliothekskatalog durch

        Args:
            search_term (str): Der Suchbegriff
            search_type (str): Art der Suche ('all', 'title', 'author', 'subject')
            verbose (bool): If True, prints more to the console

        Returns:
            list: Liste der gefundenen Ergebnisse
        """

        # Korrigierte Parameter basierend auf der ursprünglichen HTML-Form.
        # Die Original-Form verwendet einen anderen Objektnamen
        params = {
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
            print(f"DEBUG: Suche nach: '{search_term}'...")

            search_url, _ = self._prepare_search_request(params, fn="QuickSearch")

            # Vollständige URL mit Parametern anzeigen
            full_url = f"{search_url}?" + urllib.parse.urlencode(params)
            if verbose:
                print(f"DEBUG: Vollständige URL: {full_url}")

            # Suche durchführen
            search_response = self.session.get(search_url, params=params, timeout=15)
            search_response.raise_for_status()

            if verbose:
                print(f"DEBUG: HTTP Status Code: {search_response.status_code}")
                print(f"DEBUG: Response URL: {search_response.url}")
                print(f"DEBUG: Response Content Length: {len(search_response.text)} Zeichen")

            # Prüfen ob wir auf der Ergebnisseite sind
            if "Ergebnisse" not in search_response.text:
                soup = BeautifulSoup(search_response.text, "html.parser")
                error_advice_table = soup.find("table", {"id": "ErrorAdvice"})
                no_hits_text = "Leider wurden keine Titel zu Ihrer Suchanfrage gefunden." in search_response.text

                if error_advice_table or no_hits_text:
                    print("DEBUG: Keine Treffer laut Fehlermeldung gefunden – kein POST-Request notwendig")
                    return []  # direkt abbrechen, keine Ergebnisse
                else:
                    print("DEBUG: Anscheinend wieder auf Startseite gelandet - versuche POST-Request")

                    # Versuche POST statt GET
                    search_response = self.session.post(search_url, data=params, timeout=15)
                    search_response.raise_for_status()
                    print(f"DEBUG: POST Status Code: {search_response.status_code}")

            if verbose:
                # Ersten Teil der Antwort anzeigen
                response_preview = search_response.text[:100] if len(search_response.text) > 100 else search_response.text
                print(f"DEBUG: Response Preview (erste 100 Zeichen):")
                print("-" * 50)
                print(response_preview)
                print("-" * 50)

            # Nach spezifischen Inhalten suchen
            if "keine Treffer" in search_response.text.lower() or "no results" in search_response.text.lower():
                print("DEBUG: 'Keine Treffer' Text gefunden in der Antwort")

            if "treffer" in search_response.text.lower() and "gefunden" in search_response.text.lower():
                print("DEBUG: 'Treffer gefunden' Text gefunden in der Antwort")

            # Prüfen auf Weiterleitung oder Fehlerseite
            if verbose and "error" in search_response.text.lower():
                print("DEBUG: 'Error' Text gefunden in der Antwort")

            if verbose and "login" in search_response.text.lower():
                print("DEBUG: 'Login' Text gefunden - möglicherweise Login erforderlich")

            return self._parse_results(search_response.text)

        except requests.exceptions.RequestException as e:
            print(f"FEHLER beim Zugriff auf die Webseite: {e}")
            return []
        except Exception as e:
            print(f"UNERWARTETER FEHLER: {e}")
            import traceback

            traceback.print_exc()
            return []

    def _prepare_search_request(self, params, fn="QuickSearch", verbose=False):
        """Hilfsfunktion, um die richtige Search-URL vorzubereiten.

        Args:
            params (dict): Parameter für die Suche (werden noch an GET/POST übergeben).
            fn (str): Name der Funktion in der Bibliotheks-URL, z. B. "QuickSearch" oder "AdvancedSearch".
            verbose (bool): If True, prints more to the console

        Returns:
            tuple[str, requests.Response]: (search_url, main_response)
        """
        if verbose:
            print(f"DEBUG: Rufe zuerst die Hauptseite auf für fn={fn}...")
        main_response = self.safe_get(
            f"{self.search_url}?fn={fn}&Style=Portal3&SubStyle=&Lang=GER&ResponseEncoding=utf-8", timeout=15
        )
        main_response.raise_for_status()
        if verbose:
            print(f"DEBUG: Hauptseite Status: {main_response.status_code}")

        # Suche nach dem Objektnamen in der HTML-Datei
        soup = BeautifulSoup(main_response.text, "html.parser")
        form = soup.find("form", {"name": "ExpertSearch"})
        if form:
            action = form.get("action")
            if action:
                if verbose:
                    print(f"DEBUG: Form Action gefunden: {action}")
                search_url = f"{self.base_url}/alswww2.dll/{action}"
            else:
                search_url = self.search_url
        else:
            search_url = self.search_url
            print("DEBUG: Keine Form gefunden, verwende Standard-URL")

        if verbose:
            print(f"DEBUG: Verwende URL: {search_url}")
            print(f"DEBUG: Parameter: {params}")

        return search_url, main_response

    def _parse_results(self, html_content, verbose=False):
        """
        Parst die HTML-Ergebnisse und extrahiert die Informationen

        Args:
            html_content (str): HTML-Inhalt der Ergebnisseite
            verbose (bool): If True, prints more to the console

        Returns:
            list: Liste der extrahierten Ergebnisse
        """
        soup = BeautifulSoup(html_content, "html.parser")
        results = []

        print("DEBUG: Starte Parsing der Suchergebnisse...")

        # Basierend auf der HTML-Struktur der Stadtbibliothek Köln
        # Suche nach Tabellenzellen mit Suchergebnissen
        result_items = soup.find_all("td", class_=["SummaryDataCell", "SummaryDataCellStripe"])

        if verbose:
            print(f"DEBUG: Gefunden {len(result_items)} Elemente mit SummaryDataCell Klassen")

        if not result_items:
            # Fallback: Suche nach anderen möglichen Strukturen
            result_items = soup.find_all("tr", class_=lambda x: x and ("summary" in x.lower() or "result" in x.lower()))
            print(f"DEBUG: Fallback 1: Gefunden {len(result_items)} TR-Elemente mit summary/result Klassen")

        # Wenn keine spezifischen Klassen gefunden werden, suche nach Tabellen mit Links
        if not result_items:
            tables = soup.find_all("table")
            if verbose:
                print(f"DEBUG: Gefunden {len(tables)} Tabellen")
            for i, table in enumerate(tables):
                rows = table.find_all("tr")
                if verbose:
                    print(f"DEBUG: Tabelle {i + 1} hat {len(rows)} Zeilen")
                for j, row in enumerate(rows):
                    links = row.find_all("a", class_="SummaryFieldLink")
                    if links:
                        if verbose:
                            print(f"DEBUG: Zeile {j + 1} in Tabelle {i + 1} hat {len(links)} SummaryFieldLink-Links")
                        result_items.append(row)
                    else:
                        # Suche nach beliebigen Links
                        any_links = row.find_all("a", href=True)
                        if any_links:
                            print(f"DEBUG: Zeile {j + 1} in Tabelle {i + 1} hat {len(any_links)} beliebige Links")
                            # Prüfe, ob es wie ein Suchergebnis aussieht
                            if len(any_links) >= 1 and len(row.get_text(strip=True)) > 20:
                                result_items.append(row)

        print(f"DEBUG: Insgesamt {len(result_items)} potentielle Ergebnis-Elemente gefunden")

        for i, item in enumerate(result_items):
            try:
                print(f"DEBUG: Verarbeite Element {i + 1}...")
                result_data = self._extract_item_data(item)
                if result_data:
                    if verbose:
                        print(f"DEBUG: Element {i + 1} erfolgreich extrahiert: {result_data['title'][:50]}...")
                    results.append(result_data)
                else:
                    print(f"DEBUG: Element {i + 1} lieferte keine Daten")
            except Exception as e:
                print(f"DEBUG: Fehler beim Parsen von Element {i + 1}: {e}")
                continue

        return results

    def get_availability_details(self, detail_url, verbose=False):
        """
        Ruft die Detailseite auf und extrahiert Bestandsinformationen

        Args:
            detail_url (str): URL zur Detailseite
            verbose (bool): If True, prints more to the console

        Returns:
            dict: Bestandsinformationen mit Standort als Key
        """
        if not detail_url or detail_url.strip().lower().startswith("javascript:"):
            print(f"DEBUG: Ungültige Detail-URL übersprungen: {detail_url}")
            return {}

        try:
            if verbose:
                print(f"DEBUG: Rufe Detailseite auf: {detail_url}")

            detail_response = self.safe_get(detail_url, timeout=10)

            if verbose:
                print(f"DEBUG: Detailseite Status Code: {detail_response.status_code}")
                print(f"DEBUG: Response URL (nach Redirects): {detail_response.url}")
                print(f"DEBUG: Detailseite Länge: {len(detail_response.text)} Zeichen")

            detail_response.raise_for_status()

            soup = BeautifulSoup(detail_response.text, "html.parser")
            availability_info = {}

            # Methode 1: Suche nach div-Elementen mit "stock_header_" ID
            stock_headers = soup.find_all("div", id=lambda x: x and "stock_header" in x)

            if verbose:
                print(f"DEBUG: Gefunden {len(stock_headers)} stock_header divs")

            for header_div in stock_headers:
                location_text = header_div.get_text(strip=True)

                if verbose:
                    print(f"DEBUG: Stock Header: {location_text}")

                if any(
                    loc in location_text.lower()
                    for loc in [
                        "zentralbibliothek",
                        "ehrenfeld",
                        "kalk",
                        "nippes",
                        "rodenkirchen",
                        "chorweiler",
                        "mülheim",
                        "porz",
                    ]
                ):
                    # Suche nach dem nachfolgenden Inhalt
                    next_siblings = []
                    current = header_div.next_sibling

                    # Sammle alle nachfolgenden Geschwisterelemente bis zum nächsten Header
                    while current:
                        if hasattr(current, "get_text"):
                            text = current.get_text(strip=True)
                            if text and not (
                                hasattr(current, "get") and current.get("id") and "stock_header" in current.get("id")
                            ):
                                # Filter: ignoriere JavaScript-Aufrufe
                                if "documentManager" in text or "StockUpdateRequest" in text:
                                    if verbose:
                                        print("DEBUG: Ignoriere Script-Text:", text)
                                else:
                                    next_siblings.append(text)
                            elif hasattr(current, "get") and current.get("id") and "stock_header" in current.get("id"):
                                break  # Nächster Header gefunden, stoppe
                        elif isinstance(current, str) and current.strip():
                            next_siblings.append(current.strip())
                        current = current.next_sibling

                    if next_siblings:
                        availability_info[location_text] = next_siblings
                        print(f"DEBUG: Für {location_text} gefunden: {next_siblings}")

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
                print(f"DEBUG: Finale availability_info: {availability_info}")
            return availability_info

        except Exception as e:
            print(f"DEBUG: Fehler beim Abrufen der Detailseite: {e}")
            import traceback

            traceback.print_exc()
            return {}

    def get_zentralbibliothek_info(self, detail_url):
        """
        Extrahiert speziell die Informationen für die Zentralbibliothek

        Args:
            detail_url (str): URL zur Detailseite

        Returns:
            str: Bestandsinformation der Zentralbibliothek oder leerer String
        """
        availability = self.get_availability_details(detail_url)

        # Suche nach Zentralbibliothek (verschiedene Schreibweisen)
        for location, info in availability.items():
            if "zentralbibliothek" in location.lower():
                if isinstance(info, list):
                    return " ".join(info)
                else:
                    return str(info)

        return ""

    def _extract_item_data(self, item, verbose=False):
        """
        Extrahiert Daten aus einem einzelnen Suchergebnis

        Args:
            item: BeautifulSoup-Element eines Suchergebnisses
            verbose (bool): If True, prints more to the console

        Returns:
            dict: Extrahierte Daten oder None
        """
        # Basierend auf der CSS-Klassen-Struktur der Stadtbibliothek Köln

        # Titel suchen - meist in Links mit der Klasse 'SummaryFieldLink'
        title_elem = item.find("a", class_="SummaryFieldLink")
        if not title_elem:
            # Fallback: Suche nach anderen Link-Elementen
            title_elem = item.find("a", href=True)

        title = title_elem.get_text(strip=True) if title_elem else ""
        link = ""
        if title_elem and title_elem.get("href"):
            href = title_elem["href"]

            # JavaScript-Links überspringen
            if href.strip().lower().startswith("javascript:"):
                print(f"DEBUG: Überspringe ungültigen Link: {href}")
                link = ""
            else:
                # Sicherstellen, dass /alswww2.dll/ enthalten ist
                if "APS_PRESENT_BIB" in href and "alswww2.dll" not in href:
                    href = "/alswww2.dll/" + href.lstrip("/")

                if href.startswith("/"):
                    link = self.base_url + href
                elif not href.startswith("http"):
                    link = self.base_url + "/" + href
                else:
                    link = href
                if verbose:
                    print(f"DEBUG: Extrahierter Detail-Link: {link}")

        # Autor und andere Metadaten suchen
        author = ""
        year = ""
        material_type = ""
        availability = "Unbekannt"

        # Suche nach Tabellenzellen mit Felddaten
        field_cells = item.find_all("td", class_="SummaryFieldData")
        for cell in field_cells:
            text = cell.get_text(strip=True)
            if text:
                # Heuristik zur Erkennung von Autoren (meist am Anfang, enthält Namen)
                if "," in text and len(text.split()) <= 4:
                    if not author:
                        author = text
                # Jahr erkennen (4 Ziffern)
                year_match = re.search(r"\b(19|20)\d{2}\b", text)
                if year_match and not year:
                    year = year_match.group()

        # Medientyp aus spezieller Zelle
        material_elem = item.find("td", class_="SummaryMaterialTypeField")
        if material_elem:
            material_type = material_elem.get_text(strip=True)

        # Verfügbarkeit - oft in Action-Boxen oder speziellen Zellen
        avail_elem = item.find("div", class_=["SummaryActionBox", "SummaryActionLink"])
        if avail_elem:
            avail_text = avail_elem.get_text(strip=True)
            if any(word in avail_text.lower() for word in ["verfügbar", "ausleihbar", "vorbestellung"]):
                availability = avail_text

        if title:
            zentralbibliothek_info = self.get_zentralbibliothek_info(link)
            # print("MY LOVE: " + zentralbibliothek_info)

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
    def display_results(results):
        """
        Zeigt die Suchergebnisse formatiert an

        Args:
            results (list): Liste der Suchergebnisse
        """
        if not results:
            print("Keine Ergebnisse gefunden.")
            return

        print(f"\n{len(results)} Ergebnisse gefunden:\n")
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
