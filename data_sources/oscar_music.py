#!/usr/bin/env python3
"""
Oscar Beste Filmmusik - Extraktion der Gewinner

Diese Datei lädt die Liste der Oscar-Gewinner für "Beste Filmmusik" von Wikipedia
und fügt sie der albums.json hinzu.

VERWENDUNG IN gui/app.py:
    Fügen Sie in load_or_fetch_albums() ein:

    from data_sources.oscar_music import add_oscar_music_to_albums

    if not os.path.exists(ALBUMS_FILE):
        # ... bestehender Code zum Laden von Radioeins ...

        # Oscar-Filmmusik hinzufügen
        add_oscar_music_to_albums()
"""

import requests
from bs4 import BeautifulSoup
import json
import os
import time

from utils.io import DATA_DIR

ALBUMS_FILE = os.path.join(DATA_DIR, "albums.json")
WIKI_URL = "https://de.wikipedia.org/wiki/Oscar/Beste_Filmmusik"


def fetch_oscar_music_winners():
    """
    Ruft alle Gewinner des Oscars für "Beste Filmmusik" von Wikipedia ab.

    Returns:
        list[dict]: Liste von Alben mit Schlüsseln:
            - "title" (str): Filmtitel
            - "author" (str): Komponist(en)
            - "type" (str): Immer "CD"
            - "year" (str): Jahr der Verleihung
    """
    headers = {
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/130.0 Safari/537.36"
        )
    }

    print(f"DEBUG: Lade Oscar-Filmmusik-Seite: {WIKI_URL}")

    try:
        resp = requests.get(WIKI_URL, headers=headers, timeout=15)
        resp.raise_for_status()
    except requests.exceptions.RequestException as e:
        print(f"FEHLER beim Laden der Seite: {e}")
        return []

    soup = BeautifulSoup(resp.text, "html.parser")
    results = []

    # Finde alle Tabellen mit der Klasse "wikitable"
    tables = soup.find_all("table", class_="wikitable")
    print(f"DEBUG: {len(tables)} Tabellen gefunden")

    for table_idx, table in enumerate(tables):
        rows = table.find_all("tr")[1:]  # Erste Zeile (Header) überspringen

        current_year = None  # Jahr merken für Zeilen mit rowspan

        for row in rows:
            cols = row.find_all("td")

            # Prüfe ob genug Spalten vorhanden sind
            if len(cols) < 3:
                continue

            # Bestimme Jahr-Spalte
            # Falls erste Spalte ein Jahr-Link enthält, ist es eine neue Jahr-Zeile
            first_cell = cols[0]
            year_link = first_cell.find("a", href=lambda x: x and "Oscarverleihung" in x)

            if year_link:
                # Neue Jahr-Zeile (mit rowspan)
                current_year = year_link.text.strip()
                year_offset = 0  # Jahr ist in Spalte 0
            else:
                # Fortsetzungs-Zeile (Jahr fehlt wegen rowspan)
                year_offset = -1  # Spalten sind um 1 nach links verschoben

            # Spalten-Indizes anpassen
            composer_idx = 1 + year_offset
            film_idx = 2 + year_offset

            # Sicherheitsprüfung
            if composer_idx < 0 or film_idx >= len(cols):
                continue

            # Komponist(en) extrahieren
            composer_cell = cols[composer_idx]
            composers_text = composer_cell.get_text(strip=True)

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
            # Entferne Zeilenumbrüche
            composers = " ".join(composers.split())

            # Film extrahieren
            film_cell = cols[film_idx]
            film_link = film_cell.find("a")

            if not film_link:
                continue

            film_title = film_link.get("title", film_link.text.strip())

            # Verwende current_year falls verfügbar
            year_value = current_year if current_year else "Unbekannt"

            # Erstelle Eintrag
            entry = {
                "title": f"{film_title} (Soundtrack)",
                "author": composers,
                "type": "CD",
                "year": year_value
            }

            results.append(entry)

    print(f"DEBUG: {len(results)} Oscar-Filmmusik-Gewinner gefunden")
    return results


def add_oscar_music_to_albums():
    """
    Lädt Oscar-Filmmusik-Gewinner und fügt sie zu albums.json hinzu.
    Die finale Liste wird alphabetisch nach Titel sortiert.
    """
    # Lade bestehende Alben
    existing_albums = []
    if os.path.exists(ALBUMS_FILE):
        try:
            with open(ALBUMS_FILE, "r", encoding="utf-8") as f:
                existing_albums = json.load(f)
            print(f"DEBUG: {len(existing_albums)} bestehende Alben geladen")
        except json.JSONDecodeError as e:
            print(f"WARNUNG: Fehler beim Laden von albums.json: {e}")
            existing_albums = []

    # Lade Oscar-Gewinner
    oscar_albums = fetch_oscar_music_winners()

    if not oscar_albums:
        print("WARNUNG: Keine Oscar-Filmmusik gefunden, breche ab")
        return

    # Kombiniere Listen
    combined = existing_albums + oscar_albums

    # Entferne Duplikate basierend auf Titel (case-insensitive)
    unique_albums = {}
    for album in combined:
        title_key = album["title"].lower().strip()
        # Falls Titel schon existiert, behalte den mit mehr Infos
        if title_key not in unique_albums:
            unique_albums[title_key] = album
        else:
            # Bevorzuge Einträge mit Jahr-Information
            if album.get("year") and not unique_albums[title_key].get("year"):
                unique_albums[title_key] = album

    # Sortiere alphabetisch nach Titel
    sorted_albums = sorted(unique_albums.values(), key=lambda x: x["title"].lower())

    # Speichere in albums.json
    os.makedirs(DATA_DIR, exist_ok=True)
    with open(ALBUMS_FILE, "w", encoding="utf-8") as f:
        json.dump(sorted_albums, f, ensure_ascii=False, indent=2)

    print(f"✅ {len(sorted_albums)} Alben in '{ALBUMS_FILE}' gespeichert")
    print(f"   - {len(existing_albums)} bestehende Alben")
    print(f"   - {len(oscar_albums)} neue Oscar-Filmmusik-Einträge")
    print(f"   - {len(sorted_albums)} finale Alben (nach Bereinigung und Sortierung)")


if __name__ == "__main__":
    add_oscar_music_to_albums()
