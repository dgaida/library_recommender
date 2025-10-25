#!/usr/bin/env python3
"""
Stadtbibliothek Köln Katalog Suche
Programm zur Suche im Online-Katalog der Stadtbibliothek Köln
"""

import os
from library.parsers import fuzzy_match, create_search_variants


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

    # Jedes Album in der Liste prüfen
    for el in albums:
        band, album = el["author"], el["title"]
        if verbose:
            print(f"\nSuche nach: '{band} - {album}'")

        # Verschiedene Suchvarianten erstellen
        search_variants = create_search_variants(band, album)
        if verbose:
            print(f"  Suchvarianten: {search_variants[:3]}...")

        found = False
        # matched_folder = None

        # 1. Exakte Suche mit allen Varianten
        for variant in search_variants:
            if variant in existing_folders:
                found = True
                # matched_folder = variant
                found_albums.append((band, album, variant))
                if verbose:
                    print(f"  ✓ EXAKT GEFUNDEN: '{variant}'")
                break

        # 2. Fuzzy-Suche falls keine exakte Übereinstimmung
        if not found:
            for existing_folder in existing_folders:
                if fuzzy_match(search_variants, existing_folder, band, album):
                    found = True
                    # matched_folder = existing_folder
                    found_albums.append((band, album, existing_folder))
                    if verbose:
                        print(f"  ✓ FUZZY GEFUNDEN: '{existing_folder}'")
                    break

        if not found:
            # WICHTIG: Original-Element mit ALLEN Eigenschaften übernehmen
            filtered_albums.append(el)  # NEU: el statt neues Dict
            if verbose:
                print("  ✗ NICHT GEFUNDEN")

    _logging_filter_existing_albums(albums, found_albums, filtered_albums, verbose)

    return filtered_albums


def _logging_filter_existing_albums(albums, found_albums, filtered_albums, verbose):
    # Zusammenfassung
    print(f"\n{'=' * 50}")
    print("ZUSAMMENFASSUNG")
    print(f"{'=' * 50}")
    print(f"Ursprüngliche Liste: {len(albums)} Alben")
    print(f"Bereits vorhanden: {len(found_albums)} Alben")
    print(f"Noch zu besorgen: {len(filtered_albums)} Alben")

    if found_albums:
        print("\nBEREITS VORHANDENE ALBEN:")
        for band, album, folder_name in found_albums:
            print(f"  ✓ {band} - {album}")
            print(f"    → Ordner: '{folder_name}'")

    if filtered_albums and verbose:
        print("\nFEHLENDE ALBEN:")
        for el in filtered_albums:
            band, album = el["author"], el["title"]
            print(f"  ✗ {band} - {album}")


def _get_existing_folders(base_path: str):
    print(f"Durchsuche {base_path} nach vorhandenen Alben...")
    print("Normalisierung aktiv: Ignoriere Füllwörter wie 'the', 'a', 'of', etc.")

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
