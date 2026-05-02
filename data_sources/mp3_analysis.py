import os
import json
import time

from typing import List, Dict, Any, Set
from collections import Counter
from library.search import KoelnLibrarySearch
from utils.logging_config import get_logger
from utils.artist_blacklist import (
    get_artist_blacklist,
    ArtistBlacklist,
    get_filtered_top_artists,
    update_artist_blacklist_from_search_results,
)
from utils.io import DATA_DIR

logger = get_logger(__name__)

ALBUMS_FILE = os.path.join(DATA_DIR, "albums.json")


def analyze_mp3_archive(archive_path: str) -> Counter:
    """
    Analysiert das MP3-Archiv und zählt Titel pro Interpret.

    Args:
        archive_path: Pfad zum MP3-Archiv

    Returns:
        Counter-Objekt mit Artist-Counts
    """
    artist_counter: Counter = Counter()

    if not os.path.exists(archive_path):
        logger.error(f"Archiv-Pfad nicht gefunden: {archive_path}")
        return artist_counter

    logger.info(f"Analysiere MP3-Archiv: {archive_path}")

    # Rekursive Suche nach MP3/Flac/M4a Dateien
    extensions = {".mp3", ".flac", ".m4a", ".wav"}

    for root, _, files in os.walk(archive_path):
        for file in files:
            if any(file.lower().endswith(ext) for ext in extensions):
                # Extrahiere Interpret
                relative_path = os.path.relpath(root, archive_path)
                path_parts = relative_path.split(os.sep)

                artist = ""
                if path_parts and path_parts[0] != ".":
                    # Fall: Archiv/Artist/Album/Title.mp3
                    artist = path_parts[0].strip()
                elif " - " in file:
                    # Fall: Archiv/Artist - Title.mp3
                    artist = file.split(" - ")[0].strip()

                if artist:
                    artist_counter[artist] += 1

    logger.info(f"Analyse abgeschlossen. {len(artist_counter)} Interpreten gefunden.")
    return artist_counter


def search_artist_albums_in_library(artist_name: str, max_results: int = 15) -> List[Dict[str, Any]]:
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
                    "bib_availability": result.get("zentralbibliothek_info", "Unbekannt"),
                }
                albums.append(album)

        logger.info(f"{len(albums)} Alben von '{artist_name}' gefunden")
        return albums

    except Exception as e:
        logger.error(f"Fehler bei der Suche nach '{artist_name}': {e}", exc_info=True)
        return []


def get_top_artists_from_archive(archive_path: str, top_n: int = 30, use_blacklist: bool = True) -> List[str]:
    """
    Identifiziert die Top-Interpreten aus dem MP3-Archiv.

    Args:
        archive_path: Pfad zum MP3-Archiv
        top_n: Anzahl der Top-Interpreten (default: 30)
        use_blacklist: Ob Artist-Blacklist verwendet werden soll

    Returns:
        Liste der Künstlernamen
    """
    artist_counter: Counter = analyze_mp3_archive(archive_path)
    if not artist_counter:
        return []

    top_artists_tuples = _get_filtered_artists(artist_counter, top_n, use_blacklist)
    return [artist for artist, count in top_artists_tuples]


def find_new_albums_for_top_artists(archive_path: str, top_n: int = 30, use_blacklist: bool = True) -> List[Dict[str, Any]]:
    """
    Findet neue Alben für deine Top-Interpreten in der Bibliothek.

    Integriert Artist-Blacklist, um wiederholte erfolglose Suchen zu vermeiden.

    Args:
        archive_path: Pfad zum MP3-Archiv
        top_n: Anzahl der Top-Interpreten (default: 30)
        use_blacklist: Ob Artist-Blacklist verwendet werden soll

    Returns:
        Liste neuer Album-Empfehlungen
    """
    # Analysiere Archiv
    artist_counter: Counter = analyze_mp3_archive(archive_path)

    if not artist_counter:
        logger.warning("Keine Interpreten im Archiv gefunden")
        return []

    existing_albums = _get_existing_albums(archive_path)

    # Suche in Stufen: erst top_n (default 30), dann 40, dann 50 falls nichts gefunden wurde
    all_new_albums = []
    searched_artists = set()

    for n in [top_n, 40, 50]:
        if n < top_n and n != top_n:
            continue

        top_artists = _get_filtered_artists(artist_counter, n, use_blacklist)

        # Nur neue Künstler suchen, die wir noch nicht geprüft haben
        new_candidates = [a for a in top_artists if a[0] not in searched_artists]

        if new_candidates:
            logger.info(f"Suche nach Alben für {len(new_candidates)} neue Interpreten (Stufe bis Top {n})...")
            new_albums = _search_library_for_artists(new_candidates, existing_albums, use_blacklist)
            all_new_albums.extend(new_albums)

            for artist, _ in new_candidates:
                searched_artists.add(artist)

        if all_new_albums:
            return all_new_albums

        if n >= 50:
            break

        logger.info(f"Keine Alben in den Top {n} gefunden, erweitere Suche...")

    return []


def _get_filtered_artists(counter, top_n, use_blacklist):
    """Holt gefilterte Top-Interpreten (ohne geblacklistete)."""
    if use_blacklist:
        # Lade Artist-Blacklist
        blacklist: ArtistBlacklist = get_artist_blacklist()
        # Prüfe bis zu 3x so viele Kandidaten
        top_artists = get_filtered_top_artists(counter, blacklist, top_n, max_total=top_n * 3)

        logger.info("=" * 60)
        logger.info("🎵 DEINE TOP-INTERPRETEN:")
        logger.info("=" * 60)
        for i, (artist, count) in enumerate(top_artists, 1):
            blacklist_status: str = " [NEU-CHECK]" if not blacklist.is_blacklisted(artist) else ""
            logger.info(f"{i:2d}. {artist:40s} ({count:2d} Titel){blacklist_status}")
        logger.info("=" * 60)

        return top_artists
    logger.info("Artist-Blacklist deaktiviert - prüfe alle Top-Künstler")
    return counter.most_common(top_n)


def _get_existing_albums(archive_path):
    """Sammelt vorhandene Album-Ordner (für Duplikatsprüfung)."""
    existing: Set[str] = set()
    for root, dirs, _ in os.walk(archive_path):
        for dir_name in dirs:
            existing.add(dir_name.lower().strip())
    return existing


def _search_library_for_artists(top_artists, existing_albums, use_blacklist):
    """Sucht neue Alben in Bibliothek."""
    all_new_albums: List[Dict[str, Any]] = []
    blacklist = get_artist_blacklist() if use_blacklist else None

    for artist, song_count in top_artists:
        logger.info(f"\n🔍 Suche neue Alben von '{artist}'...")

        new_albums = _search_artist(artist, existing_albums)
        all_new_albums.extend(new_albums)

        if blacklist:
            update_artist_blacklist_from_search_results(artist, song_count, len(new_albums) > 0, blacklist)
        # Pause zwischen Anfragen
        time.sleep(2)

    logger.info(f"\n✅ {len(all_new_albums)} neue Alben für deine " f"Top-Interpreten gefunden!")

    # Zeige Blacklist-Statistiken
    if use_blacklist:
        logger.info("\n📊 Artist-Blacklist Status:")
        stats: Dict[str, Any] = blacklist.get_stats()
        logger.info(f"  - Gesamt geblacklistet: {stats['total_artists']} Künstler")
        logger.info(f"  - Fällig für Re-Check: {stats['due_for_recheck']} Künstler")

    return all_new_albums


def _search_artist(artist, existing_albums):
    """Sucht Alben für einen Künstler."""
    library_albums: List[Dict[str, Any]] = search_artist_albums_in_library(artist, 15)
    new_albums = []

    for album in library_albums:
        if not _is_duplicate(album, artist, existing_albums):
            new_albums.append(album)
            logger.info(f"  ✅ Neu: {album['title']}")

    return new_albums


def _is_duplicate(album, artist, existing_albums):
    """Prüft ob Album bereits vorhanden."""
    album_title_lower: str = album["title"].lower().strip()
    for existing in existing_albums:
        if artist.lower() in existing and album_title_lower in existing:
            logger.debug(f"  Duplikat übersprungen: {album['title']}")
            return True
    return False


def add_top_artist_albums_to_collection(
    archive_path: str = "H:\\MP3 Archiv", top_n: int = 30, use_blacklist: bool = True
) -> None:
    """
    Findet neue Alben für Top-Interpreten und fügt sie zu albums.json hinzu.

    Args:
        archive_path: Pfad zum MP3-Archiv
        top_n: Anzahl der Top-Interpreten (default: 30)
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
    new_albums: List[Dict[str, Any]] = find_new_albums_for_top_artists(archive_path, top_n, use_blacklist)

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
    sorted_albums: List[Dict[str, Any]] = sorted(unique_albums.values(), key=lambda x: x["title"].lower())

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
        logger.info(f"  - {len(sorted_albums)} finale Alben (nach Bereinigung und Sortierung)")

    except IOError as e:
        logger.error(f"Fehler beim Speichern: {e}", exc_info=True)


def perform_artist_blacklist_maintenance() -> None:
    """Führt Wartungsarbeiten an der Artist-Blacklist durch."""
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
            logger.info(f"  - {artist_info['artist_name']}: {artist_info['days_since_check']} Tage seit letztem Check")
    else:
        logger.info("ℹ️  Keine Künstler fällig für Re-Check")


if __name__ == "__main__":
    # Wartung durchführen
    perform_artist_blacklist_maintenance()

    # Alben-Empfehlungen erstellen
    add_top_artist_albums_to_collection(archive_path="H:\\MP3 Archiv", top_n=30, use_blacklist=True)
