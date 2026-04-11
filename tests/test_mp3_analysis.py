#!/usr/bin/env python3
"""Unit tests for mp3_analysis.py."""
import pytest
import os
from collections import Counter
from data_sources.mp3_analysis import analyze_mp3_archive, search_artist_albums_in_library, find_new_albums_for_top_artists, perform_artist_blacklist_maintenance

def test_analyze_mp3_archive(mocker):
    """Test analyzing a mock MP3 archive."""
    # Mock os.path.exists and os.walk
    mocker.patch("os.path.exists", return_value=True)
    mocker.patch("os.walk", return_value=[
        ("/archive", ["Radiohead"], ["Radiohead - Karma Police.mp3", "Radiohead - Creep.mp3"]),
        ("/archive/Radiohead", [], ["Radiohead - Paranoid Android.mp3"]),
        ("/archive/Other", [], ["Invalid.txt", "Various - Title.mp3"])
    ])

    counts = analyze_mp3_archive("/archive")
    assert counts["Radiohead"] == 3
    assert "Various" not in counts
    assert "Invalid" not in counts

def test_search_artist_albums_in_library(mocker):
    """Test searching artist albums in library."""
    mock_search = mocker.patch("data_sources.mp3_analysis.KoelnLibrarySearch")
    mock_instance = mock_search.return_value
    mock_instance.search.return_value = [
        {"title": "OK Computer", "zentralbibliothek_info": "Verfügbar"}
    ]

    albums = search_artist_albums_in_library("Radiohead")
    assert len(albums) == 1
    assert albums[0]["title"] == "OK Computer"
    assert albums[0]["author"] == "Radiohead"
    assert albums[0]["source"] == "Interessant für dich (Top-Interpret: Radiohead)"

def test_find_new_albums_for_top_artists(mocker):
    """Test finding new albums for top artists."""
    mocker.patch("data_sources.mp3_analysis.analyze_mp3_archive", return_value=Counter({"Radiohead": 10}))
    mocker.patch("data_sources.mp3_analysis._get_existing_albums", return_value={"radiohead - ok computer"})
    mocker.patch("data_sources.mp3_analysis.search_artist_albums_in_library", return_value=[
        {"title": "OK Computer", "author": "Radiohead"},
        {"title": "Kid A", "author": "Radiohead"}
    ])
    mocker.patch("time.sleep")

    new_albums = find_new_albums_for_top_artists("/archive", top_n=1, use_blacklist=False)

    assert len(new_albums) == 1
    assert new_albums[0]["title"] == "Kid A"

def test_perform_artist_blacklist_maintenance(mocker):
    """Test artist blacklist maintenance."""
    mock_blacklist = mocker.patch("data_sources.mp3_analysis.get_artist_blacklist").return_value
    mock_blacklist.clear_old_entries.return_value = 5
    mock_blacklist.get_artists_due_for_recheck.return_value = [{"artist_name": "Artist", "days_since_check": 100}]

    perform_artist_blacklist_maintenance()

    mock_blacklist.clear_old_entries.assert_called_once()
