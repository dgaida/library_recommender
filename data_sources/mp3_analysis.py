#!/usr/bin/env python3
"""
MP3-Archiv Analyse - Findet weitere Alben deiner Lieblingskünstler

Analysiert dein MP3-Archiv, zählt Titel pro Interpret und sucht in der
Bibliothek nach weiteren Alben deiner Top-Interpreten.

QUELLEN-TRACKING:
Alle Medien sollten eine "source" Eigenschaft haben:
- "Oscar (Bester Film)"
- "Oscar (Beste Filmmusik)"
- "FBW Prädikat besonders wertvoll"
- "BBC 100 Greatest Films of the 21st Century"
- "New York Times Kanon des 21. Jahrhunderts"
- "Radio Eins Top 100 Alben 2019"
- "Interessant für dich (Top-Interpret: [Name])"
"""

import os
import json
from collections import Counter
from library.search import KoelnLibrarySearch
from utils.io import DATA_DIR

ALBUMS_FILE = os.path.join(DATA_DIR, "albums.json")


def analyze_mp3_archive(archive_path):
    """
    Analysiert das MP3-Archiv und zählt Songs pro Interpret.

    Args:
        archive_path (str): Pfad zum MP3-Archiv

    Returns:
        Counter: Anzahl Songs pro Interpret
    """
    if not os.path.exists(archive_path):
        print(f"WARNUNG: MP3-Archiv nicht gefunden: {archive_path}")
        return Counter()

    print(f"DEBUG: Analysiere MP3-Archiv (Songs): {archive_path}")

    artist_counter = Counter()

    # Durchsuche alle Unterordner nach MP3-Dateien
    for root, _, files in os.walk(archive_path):
        for file_name in files:
            if not file_name.lower().endswith(".mp3"):
                continue

            # Format: "Artist - Titel.mp3"
            if " - " in file_name:
                artist = file_name.split(" - ")[0].strip()
            else:
                # Falls Format abweicht, überspringen
                continue

            # Ignoriere systemische oder unklare Künstlernamen
            if artist.startswith('.') or artist.lower() in ['various', 'compilations', 'soundtracks']:
                continue

            artist_counter[artist] += 1

    print(f"DEBUG: {len(artist_counter)} verschiedene Interpreten gefunden")
    print(f"DEBUG: Gesamt {sum(artist_counter.values())} Songs")

    return artist_counter


def get_top_artists(artist_counter, top_n=10):
    """
    Gibt die Top N Interpreten zurück.
    
    Args:
        artist_counter (Counter): Anzahl Alben pro Interpret
        top_n (int): Anzahl der Top-Interpreten
    
    Returns:
        list[tuple]: Liste von (Interpret, Anzahl) Tupeln
    """
    return artist_counter.most_common(top_n)


def search_artist_albums_in_library(artist_name, max_results=10):
    """
    Sucht alle Alben eines Interpreten in der Bibliothek.
    
    Args:
        artist_name (str): Name des Interpreten
        max_results (int): Maximale Anzahl Ergebnisse
    
    Returns:
        list[dict]: Gefundene Alben mit Titel, Interpret, Verfügbarkeit
    """
    search_engine = KoelnLibrarySearch()
    
    # Suche nach "Interpret CD"
    query = f"{artist_name} CD"
    print(f"DEBUG: Suche nach Alben von '{artist_name}'...")
    
    results = search_engine.search(query)
    
    albums = []
    for result in results[:max_results]:
        # print("***", result, "***")
        # Filtere nur CDs/Alben
        if result.get('title'):  # result.get('material_type'):  # and 'cd' in result['material_type'].lower():
            album = {
                "title": result['title'],
                "author": artist_name,
                "type": "CD",
                "source": f"Interessant für dich (Top-Interpret: {artist_name})",
                "bib_availability": result.get('zentralbibliothek_info', 'Unbekannt')
            }
            albums.append(album)
    
    print(f"DEBUG: {len(albums)} Alben von '{artist_name}' gefunden")
    return albums


def find_new_albums_for_top_artists(archive_path, top_n=10):
    """
    Findet neue Alben für deine Top-Interpreten in der Bibliothek.
    
    Args:
        archive_path (str): Pfad zum MP3-Archiv
        top_n (int): Anzahl der Top-Interpreten
    
    Returns:
        list[dict]: Liste neuer Album-Empfehlungen
    """
    # Analysiere Archiv
    artist_counter = analyze_mp3_archive(archive_path)
    
    if not artist_counter:
        print("WARNUNG: Keine Interpreten im Archiv gefunden")
        return []
    
    # Hole Top-Interpreten
    top_artists = get_top_artists(artist_counter, top_n)
    
    print("\n" + "=" * 60)
    print("🎵 DEINE TOP-INTERPRETEN:")
    print("=" * 60)
    for i, (artist, count) in enumerate(top_artists, 1):
        print(f"{i:2d}. {artist:40s} ({count:2d} Titel)")
    print("=" * 60 + "\n")
    
    # Sammle alle vorhandenen Alben (für Duplikatsprüfung)
    existing_albums = set()
    for root, dirs, files in os.walk(archive_path):
        for dir_name in dirs:
            existing_albums.add(dir_name.lower().strip())
    
    # Suche neue Alben in Bibliothek
    all_new_albums = []
    
    for artist, count in top_artists:
        print(f"\n🔍 Suche neue Alben von '{artist}'...")
        
        library_albums = search_artist_albums_in_library(artist, max_results=15)
        
        # Filtere bereits vorhandene Alben
        for album in library_albums:
            album_title_lower = album['title'].lower().strip()
            
            # Prüfe ob Album schon vorhanden
            is_duplicate = False
            for existing in existing_albums:
                if artist.lower() in existing and album_title_lower in existing:
                    is_duplicate = True
                    break
            
            if not is_duplicate:
                all_new_albums.append(album)
                print(f"  ✅ Neu: {album['title']}")
        
        # Pause zwischen Anfragen
        import time
        time.sleep(2)
    
    print(f"\n✅ {len(all_new_albums)} neue Alben für deine Top-Interpreten gefunden!")
    return all_new_albums


def add_top_artist_albums_to_collection(archive_path="H:\\MP3 Archiv", top_n=10):
    """
    Findet neue Alben für Top-Interpreten und fügt sie zu albums.json hinzu.
    
    Args:
        archive_path (str): Pfad zum MP3-Archiv
        top_n (int): Anzahl der Top-Interpreten
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
    
    # Finde neue Alben
    new_albums = find_new_albums_for_top_artists(archive_path, top_n)
    
    if not new_albums:
        print("INFO: Keine neuen Alben gefunden")
        return
    
    # Kombiniere Listen
    combined = existing_albums + new_albums
    
    # Entferne Duplikate basierend auf Titel (case-insensitive)
    unique_albums = {}
    for album in combined:
        title_key = album["title"].lower().strip()
        if title_key not in unique_albums:
            unique_albums[title_key] = album
        else:
            # Bevorzuge Einträge mit "Interessant für dich" Quelle
            if "Interessant für dich" in album.get("source", ""):
                unique_albums[title_key] = album
    
    # Sortiere alphabetisch nach Titel
    sorted_albums = sorted(unique_albums.values(), key=lambda x: x["title"].lower())
    
    # Speichere in albums.json
    os.makedirs(DATA_DIR, exist_ok=True)
    with open(ALBUMS_FILE, "w", encoding="utf-8") as f:
        json.dump(sorted_albums, f, ensure_ascii=False, indent=2)
    
    print(f"\n✅ {len(sorted_albums)} Alben in '{ALBUMS_FILE}' gespeichert")
    print(f"   - {len(existing_albums)} bestehende Alben")
    print(f"   - {len(new_albums)} neue 'Interessant für dich' Empfehlungen")
    print(f"   - {len(sorted_albums)} finale Alben (nach Bereinigung und Sortierung)")


if __name__ == "__main__":
    add_top_artist_albums_to_collection()
