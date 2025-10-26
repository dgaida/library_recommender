#!/usr/bin/env python3
"""
Oscar Beste Filmmusik - Extraktion der Gewinner

Diese Datei lädt die Liste der Oscar-Gewinner für "Beste Filmmusik" von Wikipedia
und fügt sie der albums.json hinzu.
"""

import requests
from bs4 import BeautifulSoup
import json
import os
from typing import List, Dict, Any

from utils.io import DATA_DIR
from utils.sources import SOURCE_OSCAR_BEST_SCORE
from utils.logging_config import get_logger

logger = get_logger(__name__)

ALBUMS_FILE = os.path.join(DATA_DIR, "albums.json")
WIKI_URL = "https://de.wikipedia.org/wiki/Oscar/Beste_Filmmusik"


def fetch_oscar_music_winners() -> List[Dict[str, Any]]:
    """
    Ruft alle Gewinner des Oscars für "Beste Filmmusik" von Wikipedia ab.

    Parst die Wikipedia-Seite und extrahiert Jahr, Komponist(en) und Filmtitel
    für alle Oscar-Gewinner der Kategorie "Beste Filmmusik".

    Returns:
        Liste von Alben mit Schlüsseln:
            - title: Filmtitel (Soundtrack)
            - author: Komponist(en)
            - type: Immer "CD"
            - year: Jahr der Verleihung
            - source: Quellen-Bezeichnung

    Raises:
        requests.RequestException: Bei Netzwerkproblemen

    Example:
        >>> winners = fetch_oscar_music_winners()
        >>> print(winners[0]['title'])
        'Titanic (Soundtrack)'
        >>> print(winners[0]['author'])
        'James Horner'
    """
    headers = {
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) " "AppleWebKit/537.36 (KHTML, like Gecko) " "Chrome/130.0 Safari/537.36"
        )
    }

    logger.info(f"Lade Oscar-Filmmusik-Seite: {WIKI_URL}")

    try:
        resp = requests.get(WIKI_URL, headers=headers, timeout=15)
        resp.raise_for_status()
    except requests.exceptions.RequestException as e:
        logger.error(f"Fehler beim Laden der Seite: {e}")
        return []

    soup = BeautifulSoup(resp.text, "html.parser")
    results: List[Dict[str, Any]] = []

    # Finde alle Tabellen mit der Klasse "wikitable"
    tables = soup.find_all("table", class_="wikitable")
    logger.info(f"{len(tables)} Tabellen gefunden")

    for table_idx, table in enumerate(tables):
        rows = table.find_all("tr")[1:]  # Erste Zeile (Header) überspringen

        current_year: str = ""  # Jahr merken für Zeilen mit rowspan

        for row in rows:
            cols = row.find_all("td")

            # Prüfe ob genug Spalten vorhanden sind
            if len(cols) < 3:
                continue

            # Bestimme Jahr-Spalte
            first_cell = cols[0]
            year_link = first_cell.find("a", href=lambda x: x and "Oscarverleihung" in x)

            if year_link:
                # Neue Jahr-Zeile (mit rowspan)
                current_year = year_link.text.strip()
                year_offset = 0
            else:
                # Fortsetzungs-Zeile (Jahr fehlt wegen rowspan)
                year_offset = -1

            # Spalten-Indizes anpassen
            composer_idx = 1 + year_offset
            film_idx = 2 + year_offset

            # Sicherheitsprüfung
            if composer_idx < 0 or film_idx >= len(cols):
                continue

            # Komponist(en) extrahieren
            composer_cell = cols[composer_idx]
            composers_text: str = composer_cell.get_text(strip=True)

            # Entferne Kategorie-Präfix (z.B. "Drama:", "Musical/Komödie:")
            if ":" in composers_text:
                composers_text = composers_text.split(":", 1)[1].strip()

            # Entferne Studio-Department-Info
            if "Studio Music Department" in composers_text:
                composers = composers_text.split("Studio Music Department")[0].strip()
            else:
                composers = composers_text

            # Bereinige mehrfache Kommas und &-Zeichen
            composers = composers.replace(" & ", ", ").strip()
            composers = " ".join(composers.split())

            # Film extrahieren
            film_cell = cols[film_idx]
            film_link = film_cell.find("a")

            if not film_link:
                continue

            film_title: str = film_link.get("title", film_link.text.strip())

            # Verwende current_year falls verfügbar
            year_value: str = current_year if current_year else "Unbekannt"

            # Erstelle Eintrag
            entry: Dict[str, Any] = {
                "title": f"{film_title} (Soundtrack)",
                "author": composers,
                "type": "CD",
                "year": year_value,
                "source": SOURCE_OSCAR_BEST_SCORE,
            }

            results.append(entry)

    logger.info(f"{len(results)} Oscar-Filmmusik-Gewinner gefunden")
    return results


def add_oscar_music_to_albums() -> None:
    """
    Lädt Oscar-Filmmusik-Gewinner und fügt sie zu albums.json hinzu.

    Die finale Liste wird alphabetisch nach Titel sortiert und Duplikate
    werden entfernt (case-insensitive).

    Raises:
        IOError: Bei Schreibproblemen
        json.JSONDecodeError: Bei fehlerhafter JSON-Datei

    Example:
        >>> add_oscar_music_to_albums()
        # INFO: 150 Alben in 'data/albums.json' gespeichert
        #       - 100 bestehende Alben
        #       - 50 neue Oscar-Filmmusik-Einträge
    """
    # Lade bestehende Alben
    existing_albums: List[Dict[str, Any]] = []
    if os.path.exists(ALBUMS_FILE):
        try:
            with open(ALBUMS_FILE, "r", encoding="utf-8") as f:
                existing_albums = json.load(f)
            logger.info(f"{len(existing_albums)} bestehende Alben geladen")
        except json.JSONDecodeError as e:
            logger.warning(f"Fehler beim Laden von albums.json: {e}")
            existing_albums = []

    # Lade Oscar-Gewinner
    oscar_albums = fetch_oscar_music_winners()

    if not oscar_albums:
        logger.warning("Keine Oscar-Filmmusik gefunden, breche ab")
        return

    # Kombiniere Listen
    combined = existing_albums + oscar_albums

    # Entferne Duplikate basierend auf Titel (case-insensitive)
    unique_albums: Dict[str, Dict[str, Any]] = {}
    for album in combined:
        title_key: str = album["title"].lower().strip()

        if title_key not in unique_albums:
            unique_albums[title_key] = album
        else:
            # Bevorzuge Einträge mit Jahr-Information
            if album.get("year") and not unique_albums[title_key].get("year"):
                unique_albums[title_key] = album

    # Sortiere alphabetisch nach Titel
    sorted_albums = sorted(unique_albums.values(), key=lambda x: x["title"].lower())

    # Speichere in albums.json
    try:
        os.makedirs(DATA_DIR, exist_ok=True)
        with open(ALBUMS_FILE, "w", encoding="utf-8") as f:
            json.dump(sorted_albums, f, ensure_ascii=False, indent=2)

        logger.info(f"✅ {len(sorted_albums)} Alben in '{ALBUMS_FILE}' gespeichert")
        logger.info(f"   - {len(existing_albums)} bestehende Alben")
        logger.info(f"   - {len(oscar_albums)} neue Oscar-Filmmusik-Einträge")
        logger.info(f"   - {len(sorted_albums)} finale Alben (nach Bereinigung und Sortierung)")

    except IOError as e:
        logger.error(f"Fehler beim Speichern in {ALBUMS_FILE}: {e}")
        raise


if __name__ == "__main__":
    add_oscar_music_to_albums()
