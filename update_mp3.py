import sys

content = open('data_sources/mp3_analysis.py', 'r').read()

search_text = """def find_new_albums_for_top_artists(archive_path: str, top_n: int = 30, use_blacklist: bool = True) -> List[Dict[str, Any]]:
    \"\"\"
    Findet neue Alben für deine Top-Interpreten in der Bibliothek.

    Integriert Artist-Blacklist, um wiederholte erfolglose Suchen zu vermeiden.

    Args:
        archive_path: Pfad zum MP3-Archiv
        top_n: Anzahl der Top-Interpreten (default: 30)
        use_blacklist: Ob Artist-Blacklist verwendet werden soll

    Returns:
        Liste neuer Album-Empfehlungen
    \"\"\"
    # Analysiere Archiv"""

replace_text = """def get_top_artists_from_archive(archive_path: str, top_n: int = 30, use_blacklist: bool = True) -> List[str]:
    \"\"\"
    Identifiziert die Top-Interpreten aus dem MP3-Archiv.

    Args:
        archive_path: Pfad zum MP3-Archiv
        top_n: Anzahl der Top-Interpreten (default: 30)
        use_blacklist: Ob Artist-Blacklist verwendet werden soll

    Returns:
        Liste der Künstlernamen
    \"\"\"
    artist_counter: Counter = analyze_mp3_archive(archive_path)
    if not artist_counter:
        return []

    top_artists_tuples = _get_filtered_artists(artist_counter, top_n, use_blacklist)
    return [artist for artist, count in top_artists_tuples]


def find_new_albums_for_top_artists(archive_path: str, top_n: int = 30, use_blacklist: bool = True) -> List[Dict[str, Any]]:
    \"\"\"
    Findet neue Alben für deine Top-Interpreten in der Bibliothek.

    Integriert Artist-Blacklist, um wiederholte erfolglose Suchen zu vermeiden.

    Args:
        archive_path: Pfad zum MP3-Archiv
        top_n: Anzahl der Top-Interpreten (default: 30)
        use_blacklist: Ob Artist-Blacklist verwendet werden soll

    Returns:
        Liste neuer Album-Empfehlungen
    \"\"\"
    # Analysiere Archiv"""

if search_text in content:
    new_content = content.replace(search_text, replace_text)
    with open('data_sources/mp3_analysis.py', 'w') as f:
        f.write(new_content)
    print("Successfully updated data_sources/mp3_analysis.py")
else:
    print("Search text not found")
    sys.exit(1)
