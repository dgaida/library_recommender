#!/usr/bin/env python3
"""
Stadtbibliothek Köln Katalog Suche
Programm zur Suche im Online-Katalog der Stadtbibliothek Köln
"""

import re


def normalize_text(text):
    """
    Normalisiert Text für bessere Vergleiche durch Entfernung häufiger Füllwörter

    Args:
        text (str): Zu normalisierender Text

    Returns:
        str: Normalisierter Text
    """
    if not text:
        return ""

    # Liste der zu entfernenden Wörter (case-insensitive)
    stop_words = {
        "the",
        "a",
        "an",
        "and",
        "&",
        "of",
        "in",
        "on",
        "at",
        "to",
        "for",
        "with",
        "by",
        "from",
        "up",
        "about",
        "into",
        "through",
        "during",
        "before",
        "after",
        "above",
        "below",
        "between",
        "among",
        "der",
        "die",
        "das",
        "ein",
        "eine",
        "und",
        "le",
        "la",
        "les",
        "un",
        "une",
        "et",
    }

    # Entferne Sonderzeichen aber behalte Leerzeichen
    # Klammern, Fragezeichen, Ausrufezeichen, etc. entfernen
    text_cleaned = re.sub(r"[^\w\s]", " ", text)

    # Text in Wörter aufteilen
    words = text_cleaned.lower().split()

    # Füllwörter entfernen, aber mindestens ein Wort behalten
    filtered_words = [word for word in words if word not in stop_words and word.strip()]

    # Falls alle Wörter entfernt wurden, ursprünglichen Text zurückgeben
    if not filtered_words:
        return re.sub(r"[^\w\s]", " ", text.lower()).strip()

    return " ".join(filtered_words)


def create_search_variants(band, album):
    """
    Erstellt verschiedene Suchvarianten für Band und Album

    Args:
        band (str): Bandname
        album (str): Albumname

    Returns:
        list: Liste von Suchvarianten
    """
    variants = []

    # Original
    original = f"{band} {album}".lower()
    variants.append(original)

    # Normalisiert (ohne Füllwörter)
    normalized_band = normalize_text(band)
    normalized_album = normalize_text(album)
    normalized = f"{normalized_band} {normalized_album}"
    variants.append(normalized)

    # Nur Album normalisiert
    album_normalized = f"{band.lower()} {normalized_album}"
    variants.append(album_normalized)

    # Nur Band normalisiert
    band_normalized = f"{normalized_band} {album.lower()}"
    variants.append(band_normalized)

    # Verschiedene Sonderzeichen-Behandlungen
    # 1. Alle Sonderzeichen entfernen
    no_special = re.sub(r"[^\w\s]", " ", original)
    no_special = " ".join(no_special.split())  # Mehrfache Leerzeichen entfernen
    variants.append(no_special)

    # 2. Normalisiert + keine Sonderzeichen
    no_special_norm = re.sub(r"[^\w\s]", " ", normalized)
    no_special_norm = " ".join(no_special_norm.split())
    variants.append(no_special_norm)

    # 3. Nur Klammern entfernen (für Fälle wie "(What's The Story)")
    no_brackets = re.sub(r"[()[\]{}]", " ", original)
    no_brackets = " ".join(no_brackets.split())
    variants.append(no_brackets)

    # 4. Nur Klammern entfernen + normalisiert
    no_brackets_norm = re.sub(r"[()[\]{}]", " ", normalized)
    no_brackets_norm = " ".join(no_brackets_norm.split())
    variants.append(no_brackets_norm)

    # 5. Nur Satzzeichen entfernen (?, !, ., etc.)
    no_punctuation = re.sub(r"[?!.,;:]", "", original)
    variants.append(no_punctuation)

    # 6. & und "and" Varianten
    variants.append(original.replace("&", "and"))
    variants.append(original.replace(" and ", " & "))
    variants.append(normalized.replace("&", "and"))
    variants.append(normalized.replace(" and ", " & "))

    # 7. Spezielle Behandlung für Klammern-Inhalte
    # Extrahiere Text in Klammern und erstelle Varianten ohne diesen
    bracket_pattern = r"\([^)]*\)"
    without_brackets = re.sub(bracket_pattern, "", original).strip()
    if without_brackets != original:
        variants.append(without_brackets)
        variants.append(" ".join(without_brackets.split()))  # Mehrfache Leerzeichen

    # Entferne Duplikate und leere Strings, behalte Reihenfolge
    seen = set()
    unique_variants = []
    for v in variants:
        v_clean = " ".join(v.split()).strip()  # Normalisiere Leerzeichen
        if v_clean and v_clean not in seen:
            seen.add(v_clean)
            unique_variants.append(v_clean)

    return unique_variants


def fuzzy_match(search_terms, existing_folder, band, album) -> bool:
    """
    Prüft, ob ein Ordner eine Fuzzy-Übereinstimmung mit den Suchbegriffen hat

    Args:
        search_terms (list): Liste der normalisierten Suchbegriffe
        existing_folder (str): Vorhandener Ordnername
        band (str): Ursprünglicher Bandname
        album (str): Ursprünglicher Albumname

    Returns:
        bool: True wenn Übereinstimmung gefunden
    """
    folder_lower = existing_folder.lower()
    folder_normalized = normalize_text(existing_folder)
    folder_no_special = re.sub(r"[^\w\s]", " ", folder_lower)
    folder_no_special = " ".join(folder_no_special.split())

    # Band und Album Varianten für Fuzzy-Matching
    band_variants = [band.lower(), normalize_text(band), re.sub(r"[^\w\s]", " ", band.lower()).strip()]

    album_variants = [
        album.lower(),
        normalize_text(album),
        re.sub(r"[^\w\s]", " ", album.lower()).strip(),
        re.sub(r"[()[\]{}]", " ", album.lower()).strip(),  # Ohne Klammern
        re.sub(r"\([^)]*\)", "", album.lower()).strip(),  # Klammer-Inhalt entfernen
    ]

    # Entferne leere Strings
    band_variants = [v.strip() for v in band_variants if v.strip()]
    album_variants = [v.strip() for v in album_variants if v.strip()]

    folder_versions = [folder_lower, folder_normalized, folder_no_special]

    # Band muss in einer der Ordner-Versionen gefunden werden
    band_found = any(
        any(band_variant in folder_version for folder_version in folder_versions) for band_variant in band_variants
    )

    # Album muss in einer der Ordner-Versionen gefunden werden
    album_found = any(
        any(album_variant in folder_version for folder_version in folder_versions) for album_variant in album_variants
    )

    if band_found and album_found:
        # Zusätzliche Plausibilitätsprüfung: Ordner sollte nicht zu lang sein
        max_expected_length = len(f"{band} {album}") * 2
        if len(existing_folder) <= max_expected_length:
            return True

    return False
