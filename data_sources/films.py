#!/usr/bin/env python3
"""
Film-Datenquelle: BBC Culture's 100 Greatest Films of the 21st Century

Lädt und verarbeitet Filmempfehlungen von der BBC Culture Wikipedia-Seite.
"""

import requests
from bs4 import BeautifulSoup
import time
from typing import List, Dict, Any

from utils.sources import SOURCE_BBC_100_FILMS
from library.search import KoelnLibrarySearch
from utils.io import save_results_to_markdown
from utils.logging_config import get_logger

logger = get_logger(__name__)


def fetch_wikipedia_titles() -> List[Dict[str, str]]:
    """
    Lädt die deutschen Filmtitel von der Wikipedia-Seite.

    Holt die BBC Culture's 100 Greatest Films of the 21st Century
    von der Wikipedia-Seite und extrahiert deutsche Titel und Regisseure.

    Returns:
        Liste von Dictionaries mit Schlüsseln:
            - title: Deutscher Filmtitel
            - regie: Name des Regisseurs
            - source: Quellen-Bezeichnung

    Raises:
        requests.RequestException: Bei Netzwerkproblemen

    Example:
        >>> films = fetch_wikipedia_titles()
        >>> print(films[0]['title'])
        'Mulholland Drive'
        >>> print(films[0]['regie'])
        'David Lynch'
    """
    url = "https://de.wikipedia.org/wiki/BBC_Culture%E2%80%99s_100_Greatest_Films_of_the_21st_Century"
    logger.info(f"Hole Wikipedia-Seite: {url}")

    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/122.0.0.0 Safari/537.36"
    }

    try:
        response = requests.get(url, headers=headers, timeout=15)
        response.raise_for_status()
    except requests.RequestException as e:
        logger.error(f"Fehler beim Laden der Wikipedia-Seite: {e}")
        raise

    soup = BeautifulSoup(response.text, "html.parser")
    titles: List[Dict[str, str]] = []

    # Finde die Überschrift „Liste der häufigsten Nennungen"
    heading = soup.find(lambda tag: tag.name in ["h2", "h3", "h4"] and "Liste der häufigsten Nennungen" in tag.text)
    if not heading:
        logger.warning("Überschrift 'Liste der häufigsten Nennungen' nicht gefunden, nehme erste passende Tabelle.")
        table = soup.find("table", class_="wikitable")
    else:
        table = heading.find_next("table", class_="wikitable")

    if not table:
        logger.error("Keine passende Tabelle gefunden.")
        return []

    rows = table.find_all("tr")

    # Kopfzeile identifizieren
    header_cells = [th.get_text(strip=True) for th in rows[0].find_all(["th", "td"])]

    try:
        idx_deutscher_titel = header_cells.index("Deutscher Titel")
    except ValueError:
        logger.warning(f"Spalte 'Deutscher Titel' nicht gefunden in Kopfzeile {header_cells}")
        idx_deutscher_titel = 2

    # Durch alle Zeilen gehen
    for row in rows[1:]:
        cells = row.find_all("td")
        if len(cells) > idx_deutscher_titel:
            german_title: str = cells[idx_deutscher_titel - 1].get_text(strip=True)
            regisseur: str = cells[idx_deutscher_titel].get_text(strip=True)
            if german_title:
                titles.append({"title": german_title, "regie": regisseur, "source": SOURCE_BBC_100_FILMS})

    logger.info(f"Insgesamt {len(titles)} deutsche Titel extrahiert")
    return titles


def search_wikipedia_titles_in_library() -> None:
    """
    Holt alle Wikipedia-Titel und sucht sie im Bibliothekskatalog.

    Lädt die BBC Culture Liste der 100 besten Filme des 21. Jahrhunderts
    von Wikipedia und durchsucht die Stadtbibliothek Köln nach jedem Titel.
    Ergebnisse werden in einer Markdown-Datei gespeichert.

    Returns:
        None: Ergebnisse werden in 'results.md' gespeichert

    Raises:
        requests.RequestException: Bei Netzwerkproblemen

    Note:
        Zwischen Anfragen wird eine 5-Sekunden-Pause eingelegt, um den
        Server nicht zu überlasten.

    Example:
        >>> search_wikipedia_titles_in_library()
        # INFO: Suche 1/100: Mulholland Drive
        # [Ergebnisse werden angezeigt]
    """
    search_engine = KoelnLibrarySearch()
    titles = fetch_wikipedia_titles()

    all_results: Dict[str, List[Dict[str, Any]]] = {}

    for i, title_dict in enumerate(titles, 1):
        logger.info(f"Suche {i}/{len(titles)}: {title_dict['title']}")

        results = search_engine.advanced_search(title_dict["title"], author=title_dict["regie"])
        search_engine.display_results(results)
        all_results[title_dict["title"]] = results

        logger.debug("Warte 5 Sekunden, um Server nicht zu überlasten...")
        time.sleep(5)

    save_results_to_markdown(all_results, "results.md")
