#!/usr/bin/env python3
"""
MP3-Archiv Analyse mit Artist-Blacklist Integration

Analysiert MP3-Archiv und sucht nach neuen Alben deiner Top-Interpreten,
unter Berücksichtigung der Artist-Blacklist.
"""

import os
import json
import time
from collections import Counter
from typing import List, Dict, Any, Tuple, Set
from library.search import KoelnLibrarySearch
from utils.io import DATA_DIR
from utils.logging_config import get_logger
from utils.artist_blacklist import (
    ArtistBlacklist,
    get_artist_blacklist,
    get_filtered_top_artists,
    update_artist_blacklist_from_search_results
)

logger = get_logger(__name__)

ALBUMS_FILE: str = os.path.join(DATA_DIR, "albums.json")


def analyze_mp3_archive(archive_path: str) -> Counter:
    """
    Analysiert das MP3-Archiv und zählt Songs pro Interpret.

    Args:
        archive_path: Pfad zum MP3-Archiv

    Returns:
        Counter mit Anzahl Songs pro Interpret
    """
    if not os.path.exists(archive_path):
        logger.warning(f"MP3-Archiv nicht gefunden: {archive_path}")
        return Counter()

    logger.info(f"Analysiere MP3-Archiv (Songs): {archive_path}")

    artist_counter: Counter = Counter()

    try:
        for root, _, files in os.walk(archive_path):
            for file_name in files:
                if not file_name.lower().endswith(".mp3"):
                    continue

                # Format: "Artist - Titel.mp3"
                if " - " in file_name:
                    artist: str = file_name.split(" - ")[0].strip()
                else:
                    continue

                # Ignoriere systemische oder unklare Künstlernamen
                if artist.startswith(".") or artist.lower() in [
                    "various", "compilations", "soundtracks"
                ]:
                    continue

                artist_counter[artist] += 1

        logger.info(
            f"{len(artist_counter)} verschiedene Interpreten gefunden, "
            f"{sum(artist_counter.values())} Songs gesamt"
        )

    except Exception as e:
        logger.error(f"Fehler beim Durchsuchen des Archivs: {e}", exc_info=True)

    return artist_counter


def search_artist_albums_in_library(
        artist_name: str,
        max_results: int = 15
) -> List[Dict[str, Any]]:
    """
    Sucht alle Alben eines Interpreten in der Bibliothek.

    Args:
        artist_name: Name des Interpreten
        max_results: Maximale Anzahl Ergebnisse

    Returns:
        Liste gefundener Alben mit Titel, Interpret, Verfügbarkeit
    """
    search_engine: KoelnLibrarySearch = KoelnLibrarySearch()

    query: str = f"{artist_name} CD"
    logger.info(f"Suche nach Alben von '{artist_name}'...")

    try:
        results: List[Dict[str, Any]] = search_engine.search(query)

        albums: List[Dict[str, Any]] = []
        for result in results[:max_results]:
            if result.get("title"):
                album: Dict[str, Any] = {
                    "title": result["title"],
                    "author": artist_name,
                    "type": "CD",
                    "source": f"Interessant für dich (Top-Interpret: {artist_name})",
                    "bib_availability": result.get(
                        "zentralbibliothek_info",
                        "Unbekannt"
                    ),
                }
                albums.append(album)

        logger.info(f"{len(albums)} Alben von '{artist_name}' gefunden")
        return albums

    except Exception as e:
        logger.error(
            f"Fehler bei der Suche nach '{artist_name}': {e}",
            exc_info=True
        )
        return []


def find_new_albums_for_top_artists(
        archive_path: str,
        top_n: int = 10,
        use_blacklist: bool = True
) -> List[Dict[str, Any]]:
    """
    Findet neue Alben für deine Top-Interpreten in der Bibliothek.

    Integriert Artist-Blacklist, um wiederholte erfolglose Suchen zu vermeiden.

    Args:
        archive_path: Pfad zum MP3-Archiv
        top_n: Anzahl der Top-Interpreten
        use_blacklist: Ob Artist-Blacklist verwendet werden soll

    Returns:
        Liste neuer Album-Empfehlungen
    """
    # Analysiere Archiv
    artist_counter: Counter = analyze_mp3_archive(archive_path)

    if not artist_counter:
        logger.warning("Keine Interpreten im Archiv gefunden")
        return []

    # Lade Artist-Blacklist
    artist_blacklist: ArtistBlacklist = get_artist_blacklist()

    # Hole gefilterte Top-Interpreten (ohne geblacklistete)
    if use_blacklist:
        top_artists: List[Tuple[str, int]] = get_filtered_top_artists(
            artist_counter,
            artist_blacklist,
            top_n=top_n,
            max_total=top_n * 3  # Prüfe bis zu 3x so viele Kandidaten
        )
    else:
        top_artists = artist_counter.most_common(top_n)
        logger.info("Artist-Blacklist deaktiviert - prüfe alle Top-Künstler")

    logger.info("=" * 60)
    logger.info("🎵 DEINE TOP-INTERPRETEN:")
    logger.info("=" * 60)
    for i, (artist, count) in enumerate(top_artists, 1):
        blacklist_status: str = (
            " [NEU-CHECK]"
            if not artist_blacklist.is_blacklisted(artist)
            else ""
        )
        logger.info(f"{i:2d}. {artist:40s} ({count:2d} Titel){blacklist_status}")
    logger.info("=" * 60)

    # Sammle alle vorhandenen Alben (für Duplikatsprüfung)
    existing_albums: Set[str] = set()
    for root, dirs, files in os.walk(archive_path):
        for dir_name in dirs:
            existing_albums.add(dir_name.lower().strip())

    # Suche neue Alben in Bibliothek
    all_new_albums: List[Dict[str, Any]] = []

    for artist, song_count in top_artists:
        logger.info(f"\n🔍 Suche neue Alben von '{artist}'...")

        library_albums: List[Dict[str, Any]] = search_artist_albums_in_library(
            artist,
            max_results=15
        )

        # Zähle gefundene neue Alben
        new_albums_count: int = 0

        # Filtere bereits vorhandene Alben
        for album in library_albums:
            album_title_lower: str = album["title"].lower().strip()

            # Prüfe ob Album schon vorhanden
            is_duplicate: bool = False
            for existing in existing_albums:
                if artist.lower() in existing and album_title_lower in existing:
                    is_duplicate = True
                    logger.debug(f"  Duplikat übersprungen: {album['title']}")
                    break

            if not is_duplicate:
                all_new_albums.append(album)
                new_albums_count += 1
                logger.info(f"  ✅ Neu: {album['title']}")

        # Aktualisiere Artist-Blacklist basierend auf Ergebnis
        if use_blacklist:
            found_new_albums: bool = new_albums_count > 0
            update_artist_blacklist_from_search_results(
                artist,
                song_count,
                found_new_albums,
                artist_blacklist
            )

        # Pause zwischen Anfragen
        time.sleep(2)

    logger.info(
        f"\n✅ {len(all_new_albums)} neue Alben für deine "
        f"Top-Interpreten gefunden!"
    )

    # Zeige Blacklist-Statistiken
    if use_blacklist:
        logger.info("\n📊 Artist-Blacklist Status:")
        stats: Dict[str, Any] = artist_blacklist.get_stats()
        logger.info(
            f"  - Gesamt geblacklistet: {stats['total_artists']} Künstler"
        )
        logger.info(
            f"  - Fällig für Re-Check: {stats['due_for_recheck']} Künstler"
        )

    return all_new_albums


def add_top_artist_albums_to_collection(
        archive_path: str = "H:\\MP3 Archiv",
        top_n: int = 10,
        use_blacklist: bool = True
) -> None:
    """
    Findet neue Alben für Top-Interpreten und fügt sie zu albums.json hinzu.

    Integriert Artist-Blacklist für effiziente Suche.

    Args:
        archive_path: Pfad zum MP3-Archiv
        top_n: Anzahl der Top-Interpreten
        use_blacklist: Ob Artist-Blacklist verwendet werden soll
    """
    logger.info("=" * 60)
    logger.info("🎵 STARTE PERSONALISIERTE ALBUM-EMPFEHLUNGEN")
    logger.info("=" * 60)

    # Lade bestehende Alben
    existing_albums: List[Dict[str, Any]] = []
    if os.path.exists(ALBUMS_FILE):
        try:
            with open(ALBUMS_FILE, "r", encoding="utf-8") as f:
                existing_albums = json.load(f)
            logger.info(f"{len(existing_albums)} bestehende Alben geladen")
        except json.JSONDecodeError as e:
            logger.error(f"Fehler beim Laden von albums.json: {e}")
            existing_albums = []

    # Finde neue Alben (mit Blacklist-Integration)
    new_albums: List[Dict[str, Any]] = find_new_albums_for_top_artists(
        archive_path,
        top_n,
        use_blacklist
    )

    if not new_albums:
        logger.info("ℹ️  Keine neuen Alben gefunden")
        return

    # Kombiniere Listen
    combined: List[Dict[str, Any]] = existing_albums + new_albums

    # Entferne Duplikate basierend auf Titel (case-insensitive)
    unique_albums: Dict[str, Dict[str, Any]] = {}
    for album in combined:
        title_key: str = album["title"].lower().strip()
        if title_key not in unique_albums:
            unique_albums[title_key] = album
        else:
            # Bevorzuge Einträge mit "Interessant für dich" Quelle
            if "Interessant für dich" in album.get("source", ""):
                unique_albums[title_key] = album

    # Sortiere alphabetisch nach Titel
    sorted_albums: List[Dict[str, Any]] = sorted(
        unique_albums.values(),
        key=lambda x: x["title"].lower()
    )

    # Speichere in albums.json
    try:
        os.makedirs(DATA_DIR, exist_ok=True)
        with open(ALBUMS_FILE, "w", encoding="utf-8") as f:
            json.dump(sorted_albums, f, ensure_ascii=False, indent=2)

        logger.info("\n" + "=" * 60)
        logger.info("✅ ALBEN ERFOLGREICH GESPEICHERT")
        logger.info("=" * 60)
        logger.info(f"Datei: '{ALBUMS_FILE}'")
        logger.info(f"  - {len(existing_albums)} bestehende Alben")
        logger.info(f"  - {len(new_albums)} neue 'Interessant für dich' Empfehlungen")
        logger.info(
            f"  - {len(sorted_albums)} finale Alben "
            f"(nach Bereinigung und Sortierung)"
        )

    except IOError as e:
        logger.error(f"Fehler beim Speichern: {e}", exc_info=True)


def perform_artist_blacklist_maintenance() -> None:
    """
    Führt Wartungsarbeiten an der Artist-Blacklist durch.

    - Entfernt alte Einträge (> 2 Jahre)
    - Zeigt Statistiken
    - Listet Künstler für Re-Check auf
    """
    logger.info("🔧 Starte Artist-Blacklist Wartung...")

    artist_blacklist: ArtistBlacklist = get_artist_blacklist()

    # Entferne sehr alte Einträge
    removed: int = artist_blacklist.clear_old_entries(days=730)  # 2 Jahre

    if removed > 0:
        logger.info(f"🗑️  {removed} alte Einträge entfernt (> 2 Jahre)")

    # Zeige Statistiken
    artist_blacklist.print_stats()

    # Liste Künstler für Re-Check
    due_artists: List[Dict[str, Any]] = artist_blacklist.get_artists_due_for_recheck()

    if due_artists:
        logger.info("\n📅 Künstler fällig für Re-Check:")
        for artist_info in due_artists:
            logger.info(
                f"  - {artist_info['artist_name']}: "
                f"{artist_info['days_since_check']} Tage seit letztem Check"
            )
    else:
        logger.info("ℹ️  Keine Künstler fällig für Re-Check")


if __name__ == "__main__":
    # Wartung durchführen
    perform_artist_blacklist_maintenance()

    # Alben-Empfehlungen erstellen
    add_top_artist_albums_to_collection(
        archive_path="H:\\MP3 Archiv",
        top_n=10,
        use_blacklist=True
    )
    