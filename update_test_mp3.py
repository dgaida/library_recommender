import sys

content = open('tests/test_mp3_analysis.py', 'r').read()

search_text = """    perform_artist_blacklist_maintenance,
)"""

replace_text = """    perform_artist_blacklist_maintenance,
    get_top_artists_from_archive,
)"""

content = content.replace(search_text, replace_text)

test_text = """

def test_get_top_artists_from_archive(mocker):
    \"\"\"Test identifying top artists from archive.\"\"\"
    mocker.patch("data_sources.mp3_analysis.analyze_mp3_archive", return_value=Counter({"Artist A": 10, "Artist B": 5}))
    # Mock _get_filtered_artists to avoid dealing with blacklist complexity in this simple test
    mocker.patch("data_sources.mp3_analysis._get_filtered_artists", return_value=[("Artist A", 10), ("Artist B", 5)])

    artists = get_top_artists_from_archive("/archive", top_n=2, use_blacklist=False)

    assert len(artists) == 2
    assert "Artist A" in artists
    assert "Artist B" in artists
"""

with open('tests/test_mp3_analysis.py', 'w') as f:
    f.write(content + test_text)
print("Successfully updated tests/test_mp3_analysis.py")
