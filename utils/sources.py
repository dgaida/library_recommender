#!/usr/bin/env python3
"""
Quellen-Konstanten für Medien-Empfehlungen

Definiert standardisierte Quellen-Bezeichnungen für alle Medientypen.
"""

# Film-Quellen
SOURCE_OSCAR_BEST_PICTURE = "Oscar (Bester Film)"
SOURCE_FBW_EXCEPTIONAL = "FBW Prädikat besonders wertvoll"
SOURCE_BBC_100_FILMS = "BBC 100 Greatest Films of the 21st Century"

# Musik-Quellen
SOURCE_OSCAR_BEST_SCORE = "Oscar (Beste Filmmusik)"
SOURCE_RADIO_EINS_TOP_100 = "Radio Eins Top 100 Alben 2019"

# Buch-Quellen
SOURCE_NYT_CANON = "New York Times Kanon des 21. Jahrhunderts"
SOURCE_BEST_GUIDES = "Die besten Ratgeber des 21. Jahrhunderts"


# Personalisierte Empfehlungen
def SOURCE_TOP_ARTIST(artist_name: str):
    """
    Generiert Quellen-String für Top-Interpreten.

    Erstellt einen standardisierten Quellen-String für personalisierte
    Musikempfehlungen basierend auf MP3-Archiv-Analyse.

    Args:
        artist_name (str): Name des Interpreten

    Returns:
        str: Formatierter Quellen-String

    Example:
        >>> SOURCE_TOP_ARTIST("Radiohead")
        'Interessant für dich (Top-Interpret: Radiohead)'
    """
    return f"Interessant für dich (Top-Interpret: {artist_name})"


# Quellen-Emojis für GUI
SOURCE_EMOJIS = {
    SOURCE_OSCAR_BEST_PICTURE: "🏆",
    SOURCE_OSCAR_BEST_SCORE: "🎵",
    SOURCE_FBW_EXCEPTIONAL: "⭐",
    SOURCE_BBC_100_FILMS: "🎬",
    SOURCE_RADIO_EINS_TOP_100: "📻",
    SOURCE_NYT_CANON: "📚",
    SOURCE_BEST_GUIDES: "📖",
}


def get_source_emoji(source):
    """
    Gibt das passende Emoji für eine Quelle zurück.

    Args:
        source (str): Quellen-String

    Returns:
        str: Emoji oder leerer String
    """
    # Exakte Übereinstimmung
    if source in SOURCE_EMOJIS:
        return SOURCE_EMOJIS[source]

    # Prüfe auf "Interessant für dich"
    if source and "Interessant für dich" in source:
        return "💎"

    return ""


def format_source_for_display(source):
    """
    Formatiert eine Quelle für die Anzeige mit Emoji.

    Args:
        source (str): Quellen-String

    Returns:
        str: Formatierter String mit Emoji
    """
    emoji = get_source_emoji(source)
    if emoji:
        return f"{emoji} {source}"
    return source
