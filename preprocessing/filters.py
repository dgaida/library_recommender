#!/usr/bin/env python3
"""
Stadtbibliothek Köln Katalog Suche
Programm zur Suche im Online-Katalog der Stadtbibliothek Köln
Filter-Funktionen mit robuster Album-Erkennung
"""

import os
import re
from library.parsers import fuzzy_match, create_search_variants


def normalize_album_title(title, artist=""):
    """
    Normalisiert Album-Titel für besseren Vergleich.

    Entfernt:
    - Medientyp-Kennzeichnungen: [Tonträger], CD, DVD, etc.
    - Sonderzeichen und Klammern
    - Unterschiedliche Ellipsen-Arten
    - Jahresangaben in Klammern
    - Mehrfache Leerzeichen

    Args:
        title: Album-Titel
        artist: Künstlername (optional)

    Returns:
        Normalisierter String
    """
    # Kombiniere Titel und Künstler
    combined = f"{artist} {title}".strip()

    # Konvertiere zu Lowercase
    text = combined.lower()

    # Entferne Medientyp-Kennzeichnungen
    media_patterns = [
        r"\[tonträger\]",
        r"\[cd\]",
        r"\[dvd\]",
        r"\[vinyl\]",
        r"\bcd\b",
        r"\bdvd\b",
        r"\bvinyl\b",
        r"\blp\b",
    ]
    for pattern in media_patterns:
        text = re.sub(pattern, "", text, flags=re.IGNORECASE)

    # Normalisiere verschiedene Ellipsen-Arten
    text = text.replace("…", "...")  # Unicode-Ellipse zu drei Punkten
    text = text.replace("...", " ")  # Ellipse entfernen
    text = text.replace("..", " ")  # Doppelpunkte entfernen

    # Entferne Inhalt in Klammern (z.B. Jahresangaben, Zusätze)
    text = re.sub(r"\([^)]*\)", "", text)
    text = re.sub(r"\[[^\]]*\]", "", text)
    text = re.sub(r"\{[^}]*\}", "", text)

    # Entferne Sonderzeichen (behalte nur Buchstaben, Zahlen, Leerzeichen)
    text = re.sub(r"[^\w\s]", " ", text)

    # Entferne mehrfache Leerzeichen
    text = re.sub(r"\s+", " ", text)

    # Trim
    text = text.strip()

    return text


def extract_year_from_title(title):
    """
    Extrahiert Jahreszahl aus Titel (z.B. "bis neulich 2014" -> 2014).

    Args:
        title: Titel-String

    Returns:
        Jahr als String oder None
    """
    # Suche nach 4-stelliger Jahreszahl
    match = re.search(r"\b(19|20)\d{2}\b", title)
    if match:
        return match.group(0)
    return None


def albums_are_similar(album1, album2, threshold=0.8):
    """
    Prüft ob zwei Alben ähnlich genug sind, um als Duplikat zu gelten.

    Verwendet mehrere Heuristiken:
    - Normalisierte Titel-Ähnlichkeit
    - Künstler-Übereinstimmung
    - Jahr-Übereinstimmung (falls vorhanden)

    Args:
        album1: Dict mit 'title' und 'author'
        album2: Dict mit 'title' und 'author'
        threshold: Ähnlichkeits-Schwellwert (0.0 bis 1.0)

    Returns:
        True wenn Alben als gleich gelten
    """
    # Normalisiere beide Alben
    norm1 = normalize_album_title(album1.get("title", ""), album1.get("author", ""))
    norm2 = normalize_album_title(album2.get("title", ""), album2.get("author", ""))

    # Exakte Übereinstimmung nach Normalisierung
    if norm1 == norm2:
        return True

    # Prüfe ob ein String im anderen enthalten ist (für kürzere Titel)
    if norm1 and norm2:
        if norm1 in norm2 or norm2 in norm1:
            # Zusätzlich: Künstler muss übereinstimmen
            artist1 = album1.get("author", "").lower().strip()
            artist2 = album2.get("author", "").lower().strip()

            if artist1 and artist2:
                # Prüfe ob Künstler übereinstimmen oder enthalten sind
                if artist1 == artist2 or artist1 in artist2 or artist2 in artist1:
                    return True

    # Wort-basierte Ähnlichkeit
    words1 = set(norm1.split())
    words2 = set(norm2.split())

    if not words1 or not words2:
        return False

    # Jaccard-Ähnlichkeit
    intersection = len(words1.intersection(words2))
    union = len(words1.union(words2))

    if union == 0:
        return False

    similarity = intersection / union

    # Wenn sehr ähnlich, prüfe zusätzlich Künstler
    if similarity >= threshold:
        artist1 = album1.get("author", "").lower().strip()
        artist2 = album2.get("author", "").lower().strip()

        if artist1 and artist2:
            # Künstler müssen zumindest teilweise übereinstimmen
            artist_words1 = set(artist1.split())
            artist_words2 = set(artist2.split())

            artist_intersection = len(artist_words1.intersection(artist_words2))

            if artist_intersection > 0:
                return True

    return False


def filter_existing_albums(albums, base_path="H:\\MP3 Archiv", verbose=False):
    """
    Filtert bereits existierende Alben aus einer Liste von dict-Objekten.
    Verwendet erweiterte Normalisierung um Füllwörter wie "the" zu ignorieren.

    Args:
        albums (list): Liste von Dicts in der Form [{'author': ..., 'title': ..., 'source': ...}]
        base_path (str): Basispfad zum MP3-Archiv
        verbose (bool): Debug-Ausgaben

    Returns:
        list: Gefilterte Liste ohne bereits vorhandene Alben (mit allen Properties)
    """

    if not albums:
        return []

    # Prüfen, ob der Basispfad existiert
    if not os.path.exists(base_path):
        print(f"WARNUNG: Basispfad '{base_path}' existiert nicht.")
        return albums

    filtered_albums = []
    found_albums = []

    existing_folders = _get_existing_folders(base_path)

    if existing_folders is None:
        return albums

    existing_album_objects = _extract_existing_album_objects(existing_folders)

    # Jedes Album in der Liste prüfen
    for album in albums:
        artist = album.get("author", "")
        title = album.get("title", "")

        if verbose:
            print(f"\n🔍 Prüfe: '{artist} - {title}'")
            print(f"   Normalisiert: '{normalize_album_title(title, artist)}'")

        found = False

        # Methode 1: Vergleich mit normalisierten Album-Objekten
        for existing_album in existing_album_objects:
            if albums_are_similar(album, existing_album):
                found = True
                matched_text = f"{existing_album.get('author', '')} - {existing_album.get('title', '')}".strip(" -")
                found_albums.append((artist, title, matched_text))
                if verbose:
                    print(f"   ✅ GEFUNDEN (Ähnlichkeit): '{matched_text}'")
                break

        # Methode 2: Alte Fuzzy-Match Methode als Fallback
        if not found:
            search_variants = create_search_variants(artist, title)

            for variant in search_variants:
                if variant in existing_folders:
                    found = True
                    found_albums.append((artist, title, variant))
                    if verbose:
                        print(f"   ✅ GEFUNDEN (Exakt): '{variant}'")
                    break

            if not found:
                for existing_folder in existing_folders:
                    if fuzzy_match(search_variants, existing_folder, artist, title):
                        found = True
                        found_albums.append((artist, title, existing_folder))
                        if verbose:
                            print(f"   ✅ GEFUNDEN (Fuzzy): '{existing_folder}'")
                        break

        if not found:
            filtered_albums.append(album)
            if verbose:
                print("   ❌ NICHT GEFUNDEN - wird behalten")

    _logging_filter_existing_albums(albums, found_albums, filtered_albums, verbose)

    return filtered_albums


def _extract_existing_album_objects(existing_folders):
    # Konvertiere Ordner-Namen in Album-Objekte für besseren Vergleich
    existing_album_objects = []
    for folder in existing_folders:
        # Versuche Künstler und Titel aus Ordnernamen zu extrahieren
        # Format könnte sein: "Künstler - Album" oder "Album"
        if " - " in folder:
            parts = folder.split(" - ", 1)
            existing_album_objects.append({"author": parts[0].strip(), "title": parts[1].strip()})
        else:
            existing_album_objects.append({"author": "", "title": folder.strip()})

    return existing_album_objects


def _logging_filter_existing_albums(albums, found_albums, filtered_albums, verbose):
    """Gibt Zusammenfassung der Filterung aus."""
    # Zusammenfassung
    print(f"\n{'=' * 50}")
    print("ZUSAMMENFASSUNG - ALBUM-FILTERUNG")
    print(f"{'=' * 50}")
    print(f"Ursprüngliche Liste: {len(albums)} Alben")
    print(f"Bereits vorhanden: {len(found_albums)} Alben")
    print(f"Noch zu besorgen: {len(filtered_albums)} Alben")

    if found_albums:
        print("\n✅ BEREITS VORHANDENE ALBEN:")
        for artist, title, folder_name in found_albums[:10]:  # Zeige max. 10
            print(f"   • {artist} - {title}")
            print(f"     ↳ Ordner: '{folder_name}'")

        if len(found_albums) > 10:
            print(f"   ... und {len(found_albums) - 10} weitere")

    if filtered_albums and verbose:
        print("\n❌ FEHLENDE ALBEN (werden empfohlen):")
        for album in filtered_albums[:10]:  # Zeige max. 10
            artist = album.get("author", "")
            title = album.get("title", "")
            print(f"   • {artist} - {title}")

        if len(filtered_albums) > 10:
            print(f"   ... und {len(filtered_albums) - 10} weitere")


def _get_existing_folders(base_path: str):
    """Sammelt alle Ordner im MP3-Archiv."""
    print(f"Durchsuche {base_path} nach vorhandenen Alben...")
    print("Normalisierung aktiv: Ignoriere Füllwörter, Medientypen, Sonderzeichen")

    # Alle Ordner im Archiv sammeln (rekursiv)
    existing_folders = set()
    try:
        for root, dirs, files in os.walk(base_path):
            for dir_name in dirs:
                # Ordnername in lowercase für besseren Vergleich
                existing_folders.add(dir_name.lower())
    except Exception as e:
        print(f"FEHLER beim Durchsuchen des Archivs: {e}")
        return None

    print(f"Gefunden: {len(existing_folders)} Ordner im Archiv")

    return existing_folders


def get_album_statistics(albums, base_path="H:\\MP3 Archiv"):
    """
    Erstellt Statistiken über vorhandene vs. fehlende Alben.

    Analysiert eine Album-Liste und vergleicht sie mit dem lokalen
    MP3-Archiv, um Statistiken zu generieren.

    Args:
        albums (list): Liste von Tupeln in der Form (band, album)
        base_path (str): Basispfad zum MP3-Archiv

    Returns:
        dict: Statistiken mit folgenden Schlüsseln:
            - "original_count" (int): Anzahl ursprünglicher Alben
            - "found_count" (int): Anzahl vorhandener Alben
            - "missing_count" (int): Anzahl fehlender Alben
            - "found_percentage" (float): Prozentsatz vorhandener Alben
            - "missing_albums" (list): Liste der fehlenden Alben

    Example:
        >>> stats = get_album_statistics(albums, "H:\\MP3 Archiv")
        >>> print(f"Vorhanden: {stats['found_percentage']:.1f}%")
        Vorhanden: 42.5%
    """

    original_count = len(albums)
    filtered_albums = filter_existing_albums(albums, base_path)
    filtered_count = len(filtered_albums)
    found_count = original_count - filtered_count

    return {
        "original_count": original_count,
        "found_count": found_count,
        "missing_count": filtered_count,
        "found_percentage": (found_count / original_count * 100) if original_count > 0 else 0,
        "missing_albums": filtered_albums,
    }
