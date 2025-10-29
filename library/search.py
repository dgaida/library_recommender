#!/usr/bin/env python3
"""
Stadtbibliothek Köln Katalog Suche
Programm zur Suche im Online-Katalog der Stadtbibliothek Köln
"""

import requests
from bs4 import BeautifulSoup
import urllib.parse
import re
from difflib import SequenceMatcher
import time
import random
from typing import Dict, List, Optional, Any, Tuple
from utils.logging_config import get_logger

logger = get_logger(__name__)


def normalize_name(name: str) -> str:
    """
    Normalisiert einen Namen für besseren Vergleich.

    Args:
        name: Zu normalisierender Name

    Returns:
        Normalisierter Name (lowercase, ohne Sonderzeichen)

    Example:
        >>> normalize_name("Coppola, Francis Ford")
        'francis ford coppola'
    """
    if not name:
        return ""

    # Entferne Kommas und Reihenfolge umkehren
    # "Mühlhoff, Rainer" -> "Rainer Mühlhoff"
    if "," in name:
        parts = name.split(",", 1)
        name = f"{parts[1].strip()} {parts[0].strip()}"

    # Lowercase und Sonderzeichen entfernen
    name = name.lower().strip()
    name = re.sub(r"[^\w\s]", " ", name)
    name = re.sub(r"\s+", " ", name)

    return name


def calculate_name_similarity(name1: str, name2: str) -> float:
    """
    Berechnet Ähnlichkeit zwischen zwei Namen.

    ERWEITERT: Besseres Handling für Abkürzungen und kurze Namen.

    Args:
        name1: Erster Name (normalisiert)
        name2: Zweiter Name (normalisiert)

    Returns:
        Ähnlichkeits-Score (0.0 bis 1.0)
    """
    if not name1 or not name2:
        return 0.0

    # Exakte Übereinstimmung
    if name1 == name2:
        return 1.0

    # SequenceMatcher für Gesamtähnlichkeit
    sequence_score = SequenceMatcher(None, name1, name2).ratio()

    # Wort-basierter Vergleich
    words1_list = name1.split()
    words2_list = name2.split()

    words1 = set(words1_list)
    words2 = set(words2_list)

    if not words1 or not words2:
        return sequence_score

    # Jaccard-Ähnlichkeit
    intersection = len(words1.intersection(words2))
    union = len(words1.union(words2))
    word_score = intersection / union if union > 0 else 0.0

    # Substring-Match
    substring_score = 0.0
    if name2 in name1 or name1 in name2:
        substring_score = 0.9

    # Nachnamen-Match (letztes Wort)
    lastname1 = words1_list[-1] if words1_list else ""
    lastname2 = words2_list[-1] if words2_list else ""

    lastname_score = 0.0
    if lastname1 and lastname2 and lastname1 == lastname2:
        lastname_score = 0.95

    # NEUE: Abkürzungs-Erkennung
    abbreviation_score = 0.0

    # Prüfe ob name2 eine Abkürzung ist (z.B. "S." für "Stephen")
    if len(words2_list) >= 1:
        lastname_part = words2_list[-1]
        abbrev_part = words2_list[0] if len(words2) > 1 else ""

        # Ist es eine Abkürzung? (endet mit ".")
        if abbrev_part and abbrev_part.endswith("."):
            # Prüfe ob Nachname übereinstimmt
            if lastname1 and lastname1 == lastname_part:
                # Bei Abkürzungen: Reduziere Score (zu unsicher)
                abbreviation_score = 0.6  # Niedriger Score für Abkürzungen

    # Kombiniere Scores
    if abbreviation_score > 0:
        # Bei Abkürzungen: Verwende reduzierten Score
        final_score = abbreviation_score
    else:
        # Normal: Verwende gewichteten Durchschnitt
        final_score = max(sequence_score * 0.3 + word_score * 0.4 + substring_score * 0.3, lastname_score, substring_score)

    return final_score


def extract_person_field(availability_text: str) -> List[str]:
    """
    Extrahiert ALLE Personen aus dem Person(en)-Feld.

    WICHTIG: Gibt Liste zurück, da mehrere Personen möglich!
    Entfernt Rollen-Angaben wie [Regisseur], [Schauspieler], etc.

    Args:
        availability_text: Verfügbarkeitstext aus Bibliothek

    Returns:
        Liste von bereinigten Personen-Namen

    Example:
        >>> text = "Person(en): Radford, Michael Regisseur ; Burton, Richard Schauspieler"
        >>> extract_person_field(text)
        ['Radford, Michael', 'Burton, Richard']
    """
    if not availability_text:
        logger.debug("    ⚠️ Kein Verfügbarkeitstext vorhanden")
        return []

    # GEFIXT: Pattern muss auch mit Leerzeichen statt Zeilenumbrüchen funktionieren
    # Suche nach "Person(en) :" bis zum nächsten großgeschriebenen Feld
    pattern = r"Person\(en\)\s*:\s*(.+?)(?:\s+(?:Erschienen|Umfang|Ausgabe|Anmerkungen|Original|FSK|Sprachen|ISMN|EAN|Notation|Bestand)|$)"
    match = re.search(pattern, availability_text, re.IGNORECASE | re.DOTALL)

    if not match:
        logger.debug("    ⚠️ Person(en)-Feld nicht im Text gefunden")
        logger.debug(f"    Text-Anfang (200 Zeichen): '{availability_text[:200]}'")
        return []

    persons_text = match.group(1).strip()
    logger.debug(f"    ✓ Person(en) Rohtext gefunden ({len(persons_text)} Zeichen): '{persons_text[:150]}'")

    # WICHTIG: Ersetze alle Whitespace-Kombinationen durch einzelnes Leerzeichen
    persons_text = re.sub(r"\s+", " ", persons_text)
    logger.debug(f"    Normalisiert: '{persons_text[:150]}'")

    # Teile bei Semikolon (mehrere Personen)
    parts = persons_text.split(";")
    logger.debug(f"    Aufgeteilt in {len(parts)} Teil(e)")

    persons = []
    for idx, person_part in enumerate(parts, 1):
        # Entferne Rollen-Angaben
        roles = [
            "Regisseur",
            "Schauspieler",
            "Darsteller",
            "Komponist",
            "Interpret",
            "Verfasser",
            "Autor",
            "Herausgeber",
            "Sonstige",
            "Mitwirkende",
            "Mitwirkender",
        ]

        person = person_part.strip()
        original = person

        # Entferne alle Rollen-Angaben
        for role in roles:
            person = re.sub(rf"\s+{role}\s*", "", person, flags=re.IGNORECASE)

        # Entferne auch eckige Klammern
        person = re.sub(r"\[.*?\]", "", person).strip()
        person = person.strip(" ,;")

        if person:
            persons.append(person)
            logger.debug(f"    Person {idx}: '{original}' -> '{person}'")
        else:
            logger.debug(f"    Person {idx}: '{original}' -> LEER (übersprungen)")

    logger.debug(f"    ✓ Extrahiert: {len(persons)} Person(en): {persons}")
    return persons


def check_author_match(result: Dict[str, Any], expected_author: str, threshold: float = 0.7) -> Tuple[bool, float, str]:
    """
    Prüft ob ein Suchergebnis zum erwarteten Autor/Künstler/Regisseur passt.

    FIXED: Prüft nun ALLE Personen im Person(en)-Feld.

    Args:
        result: Suchergebnis-Dictionary
        expected_author: Erwarteter Autor/Künstler/Regisseur
        threshold: Mindest-Ähnlichkeit (default: 0.7)

    Returns:
        Tuple mit (match_found, similarity_score, matched_field)

    Example:
        >>> result = {
        ...     "zentralbibliothek_info":
        ...     "Person(en): Radford, Michael Regisseur ; Burton, Richard Schauspieler"
        ... }
        >>> check_author_match(result, "Michael Radford")
        (True, 1.0, 'person_field')
    """
    if not expected_author:
        return (True, 1.0, "no_author_specified")

    expected_norm = normalize_name(expected_author)
    availability_text = result.get("zentralbibliothek_info", "")
    title = result.get("title", "")

    logger.debug("\n  🔍 Check Author Match")
    logger.debug(f"  Erwarteter Autor: '{expected_author}'")
    logger.debug(f"  Normalisiert: '{expected_norm}'")
    logger.debug(f"  Titel: '{title}'")
    logger.debug(f"  Verfügbarkeitstext vorhanden: {len(availability_text)} Zeichen")

    # Strategie 1: Person(en)-Feld - ALLE Personen prüfen
    logger.debug("  📋 Strategie 1: Person(en)-Feld")
    # Strategie 1: Person(en)-Feld - ALLE Personen prüfen
    persons = extract_person_field(availability_text)

    if persons:
        logger.debug(f"  ➡️ {len(persons)} Person(en) gefunden")
        best_person_score = 0.0
        best_person_name = None

        for person in persons:
            person_norm = normalize_name(person)
            similarity = calculate_name_similarity(expected_norm, person_norm)

            logger.debug(f"    • '{person}'")
            logger.debug(f"      Normalisiert: '{person_norm}'")
            logger.debug(f"      Score: {similarity:.3f}")

            if similarity > best_person_score:
                best_person_score = similarity
                best_person_name = person

        logger.info(f"  🏆 Bester Match: '{best_person_name}' (Score: {best_person_score:.3f})")

        if best_person_score >= threshold:
            logger.debug(f"  ✅ MATCH über Person(en)-Feld! (Score {best_person_score:.3f} >= {threshold})")
            return (True, best_person_score, "person_field")
        else:
            logger.debug(f"  ❌ Person(en)-Feld Score zu niedrig ({best_person_score:.3f} < {threshold})")
    else:
        logger.debug("  ❌ Keine Personen im Person(en)-Feld gefunden")

        # Strategie 2: Gesamter Verfügbarkeitstext
    logger.debug("  📋 Strategie 2: Volltext-Suche")
    if availability_text:
        # Suche nach Namen-Pattern
        name_pattern = r"\b([A-ZÄÖÜ][a-zäöüß]+(?:\s+[A-ZÄÖÜ][a-zäöüß]+)*)\b"
        potential_names = re.findall(name_pattern, availability_text)

        logger.debug(f"  ➡️ {len(potential_names)} potentielle Namen gefunden")

        best_similarity = 0.0
        best_match = None

        for potential_name in potential_names[:10]:  # Nur erste 10 zeigen
            potential_norm = normalize_name(potential_name)
            similarity = calculate_name_similarity(expected_norm, potential_norm)

            if similarity > 0.3:  # Nur relevante zeigen
                logger.debug(f"    • '{potential_name}' -> Score: {similarity:.3f}")

            if similarity > best_similarity:
                best_similarity = similarity
                best_match = potential_name

        if best_similarity >= threshold:
            logger.debug(f"  ✅ MATCH über Volltext: '{best_match}' (Score: {best_similarity:.3f})")
            return (True, best_similarity, "full_text")
        else:
            logger.debug(f"  ❌ Volltext Score zu niedrig ({best_similarity:.3f} < {threshold})")

    # Strategie 3: Titel-Feld
    logger.debug("  📋 Strategie 3: Titel-Feld")
    if title:
        title_norm = normalize_name(title)
        similarity = calculate_name_similarity(expected_norm, title_norm)

        logger.debug(f"  Titel normalisiert: '{title_norm}'")
        logger.debug(f"  Score: {similarity:.3f}")

        if similarity >= threshold:
            logger.debug("  ✅ MATCH über Titel-Feld!")
            return (True, similarity, "title_field")
        else:
            logger.debug("  ❌ Titel Score zu niedrig")

    logger.info(f"  ❌ KEIN MATCH gefunden (Schwellwert: {threshold})\n")
    return (False, 0.0, "no_match")


def filter_results_by_author(
    results: List[Dict[str, Any]],
    expected_author: str,
    expected_title: Optional[str] = None,  # NEU: Optional Titel-Parameter
    threshold: float = 0.7,
) -> List[Dict[str, Any]]:
    """
    Filtert Suchergebnisse nach Autor/Künstler/Regisseur und optional Titel.

    Args:
        results: Liste von Suchergebnissen
        expected_author: Erwarteter Autor/Künstler/Regisseur
        expected_title: Erwarteter Titel (optional, für besseres Ranking)
        threshold: Mindest-Ähnlichkeit (default: 0.7)

    Returns:
        Gefilterte Liste mit passenden Ergebnissen, sortiert nach Gesamt-Score
    """
    if not expected_author:
        logger.debug("Kein Autor zum Filtern angegeben - gebe alle Ergebnisse zurück")
        return results

    logger.info(f"=== STARTE AUTOR-FILTERUNG für '{expected_author}' ===")
    if expected_title:
        logger.info(f"Mit Titel-Matching für: '{expected_title}'")
    logger.info(f"Zu prüfen: {len(results)} Ergebnisse")

    filtered_results = []

    for i, result in enumerate(results, 1):
        logger.info(f"\n--- Ergebnis {i}/{len(results)} ---")
        logger.info(f"Titel: '{result.get('title', 'KEIN TITEL')}'")

        # Autor-Match prüfen
        match_found, author_similarity, matched_field = check_author_match(result, expected_author, threshold)

        # NEU: Titel-Match prüfen (falls Titel angegeben)
        title_similarity = 0.0
        if expected_title and result.get("title"):
            result_title_norm = normalize_name(result["title"])
            expected_title_norm = normalize_name(expected_title)
            title_similarity = calculate_name_similarity(expected_title_norm, result_title_norm)
            logger.info(f"📝 Titel-Match: '{result['title']}' -> Score: {title_similarity:.2f}")

        # NEU: Kombinierter Score
        if expected_title:
            # Gewichte: 60% Autor, 40% Titel
            combined_score = (author_similarity * 0.6) + (title_similarity * 0.4)
            logger.info(
                f"🎯 Kombinierter Score: {combined_score:.2f} (Autor: {author_similarity:.2f} × 0.6 + Titel: {title_similarity:.2f} × 0.4)"
            )

            # Akzeptiere wenn kombinierter Score über Threshold ODER perfekter Titel-Match
            if combined_score >= threshold or title_similarity >= 0.95:
                result["author_match_score"] = author_similarity
                result["title_match_score"] = title_similarity
                result["combined_score"] = combined_score
                result["author_match_field"] = matched_field
                filtered_results.append(result)
                logger.info(f"✅ AKZEPTIERT (Combined Score: {combined_score:.2f})")
            else:
                logger.info(f"❌ ABGELEHNT (Combined Score {combined_score:.2f} < {threshold})")
        else:
            # Nur Autor-Match (wie bisher)
            if match_found:
                result["author_match_score"] = author_similarity
                result["combined_score"] = author_similarity
                result["author_match_field"] = matched_field
                filtered_results.append(result)
                logger.info(f"✅ AKZEPTIERT (Score: {author_similarity:.2f})")
            else:
                logger.info(f"❌ ABGELEHNT (Score unter {threshold})")

    logger.info(f"\n=== FILTER-ERGEBNIS: {len(filtered_results)}/{len(results)} ===\n")

    # Sortiere nach kombiniertem Score (oder Autor-Score falls kein Titel)
    filtered_results.sort(key=lambda x: x.get("combined_score", 0.0), reverse=True)

    return filtered_results


class KoelnLibrarySearch:
    """Suchengine für die Stadtbibliothek Köln."""

    def __init__(self) -> None:
        """Initialisiert die Suchengine mit Basis-URLs und Session."""
        self.base_url: str = "https://katalog.stbib-koeln.de"
        self.search_url: str = f"{self.base_url}/alswww2.dll/APS_ZONES"
        self.session: requests.Session = requests.Session()
        self.session.headers.update(
            {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/91.0.4472.124 Safari/537.36"
            }
        )

    def advanced_search(
        self,
        title: Optional[str] = None,
        author: Optional[str] = None,
        subject: Optional[str] = None,
        year: Optional[str] = None,
        page_size: int = 20,
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

    def _advanced_search(self, query: str, page_size: int = 20, verbose: bool = False) -> List[Dict[str, Any]]:
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
            except requests.exceptions.HTTPError:
                if response.status_code in [429, 503]:
                    wait = (attempt + 1) * 5 + random.random() * 3
                    logger.warning(f"Server-Fehler {response.status_code}, " f"warte {wait:.1f} Sekunden...")
                    time.sleep(wait)
                    continue
                raise

        error_msg = f"Fehler nach 3 Versuchen für URL: {url}"
        logger.error(error_msg)
        raise Exception(error_msg)

    def search(self, search_term: str, search_type: str = "all", verbose: bool = False) -> List[Dict[str, Any]]:
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
                no_hits_text = "Leider wurden keine Titel zu Ihrer Suchanfrage gefunden." in search_response.text

                if error_advice_table or no_hits_text:
                    logger.info("Keine Treffer laut Fehlermeldung gefunden")
                    return []
                else:
                    logger.debug("Anscheinend auf Startseite - versuche POST-Request")
                    search_response = self.session.post(search_url, data=params, timeout=15)
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
        self, params: Dict[str, str], fn: str = "QuickSearch", verbose: bool = False
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
            f"{self.search_url}?fn={fn}&Style=Portal3&SubStyle=&Lang=GER" f"&ResponseEncoding=utf-8", timeout=15
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

    def _parse_results(self, html_content: str, verbose: bool = False) -> List[Dict[str, Any]]:
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

        result_items = soup.find_all("td", class_=["SummaryDataCell", "SummaryDataCellStripe"])

        if verbose:
            logger.debug(f"Gefunden {len(result_items)} Elemente mit SummaryDataCell Klassen")

        if not result_items:
            result_items = soup.find_all("tr", class_=lambda x: x and ("summary" in x.lower() or "result" in x.lower()))
            logger.debug(f"Fallback 1: Gefunden {len(result_items)} TR-Elemente " f"mit summary/result Klassen")

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
                            logger.debug(f"Zeile {j + 1} in Tabelle {i + 1} " f"hat {len(links)} SummaryFieldLink-Links")
                        result_items.append(row)
                    else:
                        any_links = row.find_all("a", href=True)
                        if any_links and len(any_links) >= 1 and len(row.get_text(strip=True)) > 20:
                            result_items.append(row)

        logger.info(f"Insgesamt {len(result_items)} potentielle Ergebnis-Elemente gefunden")

        for i, item in enumerate(result_items):
            try:
                logger.debug(f"Verarbeite Element {i + 1}...")
                result_data = self._extract_item_data(item)
                if result_data:
                    if verbose:
                        logger.debug(f"Element {i + 1} erfolgreich extrahiert: " f"{result_data['title'][:50]}...")
                    results.append(result_data)
                else:
                    logger.debug(f"Element {i + 1} lieferte keine Daten")
            except Exception as e:
                logger.warning(f"Fehler beim Parsen von Element {i + 1}: {e}")
                continue

        return results

    def get_availability_details(self, detail_url: str, verbose: bool = False) -> Dict[str, Any]:
        """
        Ruft die Detailseite auf und extrahiert Bestandsinformationen UND Metadaten.

        Args:
            detail_url: URL zur Detailseite
            verbose: Ausführliches Logging

        Returns:
            Dictionary mit zwei Keys pro Standort:
                - "{standort}": Nur Bestandsinfo (für Anzeige)
                - "{standort}_full": Metadaten + Bestandsinfo (für Author-Matching)
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

            # NEU: Extrahiere die vollständigen Metadaten (für Author-Matching)
            detail_table = soup.find("table", class_="OuterSearchResultDetailTable")

            full_metadata = ""
            if detail_table:
                rows = detail_table.find_all("tr")
                for row in rows:
                    row_text = row.get_text(separator=" ", strip=True)
                    if row_text:
                        full_metadata += row_text + "\n"

                logger.debug(f"✓ Vollständige Metadaten extrahiert: {len(full_metadata)} Zeichen")
            else:
                all_tables = soup.find_all("table")
                logger.debug(f"Kein OuterSearchResultDetailTable, suche in {len(all_tables)} Tabellen")

                for table in all_tables:
                    table_text = table.get_text(separator=" ", strip=True)
                    if "Person(en)" in table_text or "Titel" in table_text:
                        full_metadata = table_text
                        logger.debug(f"✓ Metadaten in anderer Tabelle gefunden: {len(full_metadata)} Zeichen")
                        break

                if not full_metadata:
                    full_metadata = soup.get_text(separator=" ", strip=True)
                    logger.debug(f"Fallback: Verwende Seitentext: {len(full_metadata)} Zeichen")

            # Methode 1: Suche nach div-Elementen mit "stock_header_" ID
            stock_headers = soup.find_all("div", id=lambda x: x and "stock_header" in x)

            if verbose:
                logger.debug(f"Gefunden {len(stock_headers)} stock_header divs")

            locations = ["zentralbibliothek", "ehrenfeld", "kalk", "nippes", "rodenkirchen", "chorweiler", "mülheim", "porz"]

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
                                hasattr(current, "get") and current.get("id") and "stock_header" in current.get("id")
                            ):
                                if "documentManager" in text or "StockUpdateRequest" in text:
                                    if verbose:
                                        logger.debug(f"Ignoriere Script-Text: {text}")
                                else:
                                    next_siblings.append(text)
                            elif hasattr(current, "get") and current.get("id") and "stock_header" in current.get("id"):
                                break
                        elif isinstance(current, str) and current.strip():
                            next_siblings.append(current.strip())
                        current = current.next_sibling

                    if next_siblings:
                        # Nur Bestandsinfo (für Anzeige in GUI)
                        bestand_info = " ".join(next_siblings)
                        availability_info[location_text] = bestand_info

                        # Vollständige Info mit Metadaten (für Author-Matching)
                        combined_info = full_metadata + "\n" + bestand_info
                        availability_info[f"{location_text}_full"] = combined_info

                        logger.debug(f"✓ Für {location_text}:")
                        logger.debug(f"  Bestandsinfo: {len(bestand_info)} Zeichen")
                        logger.debug(f"  Full (mit Metadaten): {len(combined_info)} Zeichen")

            # Methode 2: Fallback für Tabellen
            if not availability_info:
                logger.debug("Fallback - suche nach Tabellen mit Bestandsinfo")
                tables = soup.find_all("table")
                for table in tables:
                    rows = table.find_all("tr")
                    current_location = None
                    bestand_text = ""

                    for row in rows:
                        cells = row.find_all(["td", "th"])
                        for cell in cells:
                            cell_text = cell.get_text(strip=True)

                            if any(loc in cell_text.lower() for loc in locations):
                                current_location = cell_text
                                bestand_text = ""
                                logger.debug(f"Tabellen-Standort gefunden: {current_location}")

                            elif current_location and cell_text and len(cell_text) > 10:
                                bestand_text += " " + cell_text

                    if current_location and bestand_text:
                        availability_info[current_location] = bestand_text.strip()
                        availability_info[f"{current_location}_full"] = full_metadata + "\n" + bestand_text

            # Methode 3: Fallback für Bestand-Header
            if not availability_info:
                logger.debug("Fallback - suche nach Bestand-Text")
                bestand_headers = soup.find_all(string=lambda text: text and "bestand" in text.lower())

                for header in bestand_headers:
                    parent = header.parent
                    if parent:
                        next_elements = parent.find_all_next(["div", "td", "p", "span"])[:20]
                        current_location = None
                        bestand_text = ""

                        for elem in next_elements:
                            elem_text = elem.get_text(strip=True)

                            if any(loc in elem_text.lower() for loc in locations):
                                current_location = elem_text
                                bestand_text = ""
                                logger.debug(f"Bestand-Standort gefunden: {current_location}")
                            elif current_location and elem_text and len(elem_text) > 5:
                                if not any(loc in elem_text.lower() for loc in locations):
                                    bestand_text += " " + elem_text

                        if current_location and bestand_text:
                            availability_info[current_location] = bestand_text.strip()
                            availability_info[f"{current_location}_full"] = full_metadata + "\n" + bestand_text

            if verbose:
                logger.debug(f"Finale availability_info: {len(availability_info)} Keys")
                for key in availability_info.keys():
                    logger.debug(f"  {key}: {len(availability_info[key])} Zeichen")

            return availability_info

        except Exception as e:
            logger.error(f"Fehler beim Abrufen der Detailseite: {e}", exc_info=True)
            return {}

    def get_zentralbibliothek_info(self, detail_url: str, return_full: bool = False) -> str:
        """
        Extrahiert speziell die Informationen für die Zentralbibliothek.

        Args:
            detail_url: URL zur Detailseite
            return_full: True = Metadaten + Bestand (für Author-Matching)
                         False = Nur Bestand (für GUI-Anzeige)

        Returns:
            Bestandsinformation der Zentralbibliothek oder leerer String
        """
        availability = self.get_availability_details(detail_url)

        logger.debug(f"Verfügbarkeit für {detail_url[:50]}...: {len(availability)} Keys")

        for location_key in availability.keys():
            # Prüfe ob es ein Zentralbibliothek-Key ist (nicht "_full")
            if "zentralbibliothek" in location_key.lower() and not location_key.endswith("_full"):
                if return_full:
                    # Hole die Full-Version mit Metadaten
                    full_key = f"{location_key}_full"
                    if full_key in availability:
                        result = availability[full_key]
                        logger.debug(f"Zentralbibliothek-Info (FULL) gefunden: {len(result)} Zeichen")
                        return result
                    else:
                        # Fallback auf normale Version
                        result = availability[location_key]
                        logger.debug(f"Zentralbibliothek-Info (Fallback) gefunden: {len(result)} Zeichen")
                        return result
                else:
                    # Nur Bestandsinfo (für GUI)
                    result = availability[location_key]
                    logger.debug(f"Zentralbibliothek-Info (Bestand) gefunden: {len(result)} Zeichen")
                    return result

        logger.debug("Keine Zentralbibliothek-Info gefunden")
        return ""

    def _extract_item_data(self, item: Any, verbose: bool = False) -> Optional[Dict[str, Any]]:
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

                logger.debug(f"📎 Detail-Link für '{title}': {link}")

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
            if any(word in avail_text.lower() for word in ["verfügbar", "ausleihbar", "vorbestellung"]):
                availability = avail_text

        if title:
            logger.info(f"🔗 Rufe Detailseite auf für: '{title}'")

            # Hole beide Versionen:
            # 1. Nur Bestand (für GUI-Anzeige)
            zentralbibliothek_info = self.get_zentralbibliothek_info(link, return_full=False)
            # 2. Full mit Metadaten (für Author-Matching)
            zentralbibliothek_info_full = self.get_zentralbibliothek_info(link, return_full=True)

            logger.info(f"📦 Zentralbibliothek-Info erhalten: {len(zentralbibliothek_info)} Zeichen (Bestand)")
            logger.info(f"📦 Zentralbibliothek-Info (Full): {len(zentralbibliothek_info_full)} Zeichen")

            if zentralbibliothek_info:
                logger.debug(f"   Bestand (erste 200): '{zentralbibliothek_info[:200]}'")
            else:
                logger.warning("   ⚠️ KEINE Bestandsinfo erhalten!")

            return {
                "title": title,
                "author": author,
                "year": year,
                "material_type": material_type,
                "link": link,
                "availability": availability,
                "zentralbibliothek_info": zentralbibliothek_info_full,  # Full für Author-Matching!
                "zentralbibliothek_bestand": zentralbibliothek_info,  # Nur Bestand für Anzeige
            }

        return None

    def extract_genres_from_description(self, description: str) -> List[str]:
        """
        Extrahiert Genre-Angaben aus der Medienbeschreibung.

        Genre sind in der Bibliotheksbeschreibung durch Sternchen markiert,
        z.B. *Drama*, *Komödie*, *Thriller*.

        Args:
            description: Beschreibungstext aus dem Bibliothekskatalog

        Returns:
            Liste der gefundenen Genres

        Example:
            >>> genres = extract_genres_from_description("*Drama* *Thriller* Uv")
            >>> print(genres)
            ['Drama', 'Thriller']
        """
        if not description:
            return []

        # Pattern für *Genre*
        pattern = r"\*([^*]+)\*"
        matches = re.findall(pattern, description)

        genres = [match.strip() for match in matches if match.strip()]

        if genres:
            logger.debug(f"Genres extrahiert: {genres}")

        return genres

    def is_film_medium(self, description: str) -> bool:
        """
        Prüft, ob ein Medium anhand der Beschreibung ein Film ist.

        Filme enthalten das Kürzel "Uv" in der Beschreibung.

        Args:
            description: Beschreibungstext aus dem Bibliothekskatalog

        Returns:
            True wenn Film, sonst False

        Example:
            >>> is_film = is_film_medium("*Drama* Uv Verfügbar")
            >>> print(is_film)
            True
        """
        if not description:
            logger.debug("Keine Beschreibung vorhanden")
            return False

        # Prüfe auf "Uv" Kürzel (mit Wortgrenzen)
        has_uv = bool(re.search(r"\bUv\b", description))

        logger.debug(f"Film-Check (Uv): {has_uv}")
        return has_uv

    def truncate_description(self, description: str, max_length: int = 300) -> str:
        """
        Kürzt eine Beschreibung auf maximale Zeichenlänge.

        Args:
            description: Zu kürzende Beschreibung
            max_length: Maximale Zeichenlänge (default: 300)

        Returns:
            Gekürzte Beschreibung mit "..." falls nötig

        Example:
            >>> short = truncate_description("Eine sehr lange Beschreibung...", 20)
            >>> print(short)
            'Eine sehr lange Be...'
        """
        if not description or len(description) <= max_length:
            return description

        # Kürze auf max_length - 3 (für "...")
        truncated = description[: max_length - 3].strip() + "..."

        logger.debug(f"Beschreibung gekürzt: {len(description)} -> {len(truncated)} Zeichen")

        return truncated

    def search_with_author(
        self, search_term: str, expected_author: Optional[str] = None, search_type: str = "all", verbose: bool = False
    ) -> List[Dict[str, Any]]:
        """
        Suche mit optionalem Author-Matching.

        Diese Methode sollte die normale search() Methode ersetzen
        oder als Alternative angeboten werden.

        Args:
            search_term: Suchbegriff
            expected_author: Erwarteter Autor/Künstler/Regisseur (optional)
            search_type: Art der Suche
            verbose: Ausführliches Logging

        Returns:
            Liste (gefilterte) Suchergebnisse
        """
        # Normale Suche durchführen
        results = self.search(search_term, search_type, verbose)

        if not results:
            return []

        # Wenn Autor angegeben, filtere Ergebnisse
        if expected_author:
            logger.info(f"Filtere {len(results)} Ergebnisse nach Autor '{expected_author}'")
            results = filter_results_by_author(results, expected_author, threshold=0.7)

        return results

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
