#!/usr/bin/env python3
"""
Album-Datenquelle: Radio Eins Top 100 Alben 2019

Lädt und verarbeitet Albumempfehlungen von Radio Eins.
"""

import requests
from bs4 import BeautifulSoup
import time
from typing import List, Tuple, Dict, Any

from library.search import KoelnLibrarySearch
from utils.io import save_results_to_markdown
from preprocessing.filters import filter_existing_albums
from utils.logging_config import get_logger

logger = get_logger(__name__)


def fetch_radioeins_albums() -> List[Tuple[str, str]]:
    """
    Lädt die Liste der besten Musik-Alben von der Radioeins-Seite.

    Holt die 'Die 100 besten Alben 2019' von radioeins.de und gibt
    eine Liste von (Band, Album) Tupeln zurück.

    Returns:
        Liste von Tupeln im Format (Band, Album)

    Raises:
        requests.RequestException: Bei Netzwerkproblemen

    Example:
        >>> albums = fetch_radioeins_albums()
        >>> print(albums[0])
        ('Radiohead', 'OK Computer')
    """
    url = "https://www.radioeins.de/musik/top_100/die-100-besten-2019/alben/alben---die-top-100.html"
    logger.info(f"Hole Radioeins-Seite: {url}")

    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/122.0.0.0 Safari/537.36"
    }

    try:
        response = requests.get(url, headers=headers, timeout=15)
        response.raise_for_status()
    except requests.RequestException as e:
        logger.error(f"Fehler beim Laden der Seite: {e}")
        raise

    soup = BeautifulSoup(response.text, "html.parser")
    albums: List[Tuple[str, str]] = []

    # Die Tabelle steckt im Div mit class="table layoutstandard"
    container = soup.find("div", class_="table layoutstandard")
    if not container:
        logger.error("Container <div class='table layoutstandard'> nicht gefunden.")
        return []

    table = container.find("table")
    if not table:
        logger.error("Keine <table> im Container gefunden.")
        return []

    rows = table.find_all("tr")
    for row in rows:
        cells = row.find_all("td")
        if len(cells) >= 3:
            band: str = cells[1].get_text(strip=True)
            album: str = cells[2].get_text(strip=True)
            if band and album:
                albums.append((band, album))

    logger.info(f"Insgesamt {len(albums)} Alben extrahiert")
    return albums


def search_radioeins_albums_in_library(limit: int = 10) -> None:
    """
    Holt alle Radioeins-Alben und sucht sie im Bibliothekskatalog.

    Lädt die Top-100-Alben von Radio Eins, filtert bereits vorhandene Alben
    aus dem lokalen MP3-Archiv heraus und durchsucht die Stadtbibliothek Köln
    nach den verbleibenden Titeln.

    Args:
        limit: Maximale Anzahl Alben, die durchsucht werden sollen (default: 10)

    Returns:
        None: Ergebnisse werden in Markdown-Datei gespeichert

    Raises:
        requests.RequestException: Bei Netzwerkproblemen

    Example:
        >>> search_radioeins_albums_in_library(limit=5)
        # Sucht die ersten 5 gefilterten Alben
    """
    search_engine = KoelnLibrarySearch()
    albums = fetch_radioeins_albums()

    filtered = filter_existing_albums(albums, "H:\\MP3 Archiv")

    all_results: Dict[str, List[Dict[str, Any]]] = {}

    for i, (band, album) in enumerate(filtered, 1):
        if i > limit:
            break

        search_term: str = f"{band} {album} CD"
        logger.info(f"Suche {i}/{len(filtered)}: {search_term}")

        results = search_engine.search(search_term)
        search_engine.display_results(results)
        all_results[search_term] = results

        time.sleep(5)  # Pause, um den Server nicht zu überlasten

    save_results_to_markdown(all_results, "radioeins_alben_results.md")
