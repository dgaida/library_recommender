#!/usr/bin/env python3
"""
Stadtbibliothek Köln Katalog Suche
Programm zur Suche im Online-Katalog der Stadtbibliothek Köln
"""

import requests
from bs4 import BeautifulSoup
import time

from library.search import KoelnLibrarySearch
from utils.io import save_results_to_markdown
from preprocessing.filters import filter_existing_albums


def fetch_radioeins_albums():
    """
    Lädt die Liste der besten Musik-Alben von der Radioeins-Seite
    'Die 100 besten Alben 2019' und gibt eine Liste von (Band, Album) zurück.
    """
    url = "https://www.radioeins.de/musik/top_100/die-100-besten-2019/alben/alben---die-top-100.html"
    print(f"DEBUG: Hole Radioeins-Seite: {url}")

    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/122.0.0.0 Safari/537.36"
    }
    response = requests.get(url, headers=headers, timeout=15)
    response.raise_for_status()

    soup = BeautifulSoup(response.text, "html.parser")
    albums = []

    # Die Tabelle steckt im Div mit class="table layoutstandard"
    container = soup.find("div", class_="table layoutstandard")
    if not container:
        print("ERROR: Container <div class='table layoutstandard'> nicht gefunden.")
        return []

    table = container.find("table")
    if not table:
        print("ERROR: Keine <table> im Container gefunden.")
        return []

    rows = table.find_all("tr")
    for row in rows:
        cells = row.find_all("td")
        if len(cells) >= 3:
            band = cells[1].get_text(strip=True)
            album = cells[2].get_text(strip=True)
            if band and album:
                albums.append((band, album))

    print(f"DEBUG: Insgesamt {len(albums)} Alben extrahiert.")
    return albums


def search_radioeins_albums_in_library(limit=10):
    """
    Holt alle Radioeins-Alben und sucht sie im Bibliothekskatalog.

    Lädt die Top-100-Alben von Radio Eins, filtert bereits vorhandene Alben
    aus dem lokalen MP3-Archiv heraus und durchsucht die Stadtbibliothek Köln
    nach den verbleibenden Titeln.

    Args:
        limit (int): Maximale Anzahl Alben, die durchsucht werden sollen.
            Standard: 10

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

    # Statistiken anzeigen
    # stats = get_album_statistics(albums, "H:\\MP3 Archiv")
    # print(f"\nStatistiken:")
    # print(f"  Gefunden: {stats['found_count']} ({stats['found_percentage']:.1f}%)")
    # print(f"  Fehlend: {stats['missing_count']}")

    all_results = {}

    for i, (band, album) in enumerate(filtered, 1):
        if i > limit:  # Begrenzung (z. B. nur die ersten 10)
            break
        search_term = f"{band} {album} CD"
        print(f"\n### Suche {i}/{len(filtered)}: {search_term} ###")
        # results = search_engine.advanced_search(album, author=band)
        results = search_engine.search(search_term)
        search_engine.display_results(results)
        all_results[search_term] = results
        time.sleep(5)  # Pause, um den Server nicht zu überlasten

    save_results_to_markdown(all_results, "radioeins_alben_results.md")
