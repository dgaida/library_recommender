#!/usr/bin/env python3
"""
Unit Tests für das Artist-Blacklist System
"""

import pytest
import os
import json
import tempfile
from datetime import datetime, timedelta
from unittest.mock import patch, MagicMock
from collections import Counter
from utils.artist_blacklist import (
    ArtistBlacklist,
    get_filtered_top_artists,
    update_artist_blacklist_from_search_results,
    get_artist_blacklist,
)


class TestArtistBlacklist:
    """Tests für die ArtistBlacklist-Klasse."""

    @pytest.fixture
    def temp_blacklist_file(self):
        """Erstellt temporäre Blacklist-Datei für Tests."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            json.dump({}, f)
            temp_path = f.name

        yield temp_path

        # Cleanup
        if os.path.exists(temp_path):
            os.remove(temp_path)

    @pytest.fixture
    def artist_blacklist(self, temp_blacklist_file):
        """Erstellt ArtistBlacklist-Instanz mit temporärer Datei."""
        with patch("utils.artist_blacklist.ARTIST_BLACKLIST_FILE", temp_blacklist_file):
            return ArtistBlacklist()

    def test_init_empty_blacklist(self, artist_blacklist):
        """Test: Initialisierung mit leerer Blacklist."""
        assert len(artist_blacklist.blacklist) == 0
        assert isinstance(artist_blacklist.blacklist, dict)

    def test_add_to_blacklist(self, artist_blacklist):
        """Test: Künstler zur Blacklist hinzufügen."""
        artist_blacklist.add_to_blacklist("Radiohead", 42, "Keine neuen CDs gefunden")

        assert len(artist_blacklist.blacklist) == 1
        assert "radiohead" in artist_blacklist.blacklist

        entry = artist_blacklist.blacklist["radiohead"]
        assert entry["artist_name"] == "Radiohead"
        assert entry["song_count"] == 42
        assert entry["reason"] == "Keine neuen CDs gefunden"
        assert "added_at" in entry
        assert "last_checked" in entry
        assert entry["check_count"] == 1

    def test_is_blacklisted_fresh_entry(self, artist_blacklist):
        """Test: Prüfung eines frisch geblacklisteten Künstlers."""
        artist_blacklist.add_to_blacklist("Pink Floyd", 38)

        assert artist_blacklist.is_blacklisted("Pink Floyd") is True
        assert artist_blacklist.is_blacklisted("pink floyd") is True
        assert artist_blacklist.is_blacklisted("PINK FLOYD") is True

    def test_is_blacklisted_old_entry(self, artist_blacklist):
        """Test: Prüfung eines alten Eintrags (> 1 Jahr)."""
        # Füge Künstler mit altem Datum hinzu
        old_date = (datetime.now() - timedelta(days=400)).isoformat()

        artist_blacklist.blacklist["beatles"] = {
            "artist_name": "The Beatles",
            "song_count": 50,
            "reason": "Test",
            "added_at": old_date,
            "last_checked": old_date,
            "check_count": 1,
        }

        # Sollte False zurückgeben (Re-Check fällig)
        assert artist_blacklist.is_blacklisted("The Beatles") is False

    def test_is_blacklisted_recent_entry(self, artist_blacklist):
        """Test: Prüfung eines kürzlichen Eintrags (< 1 Jahr)."""
        # Füge Künstler mit kürzlichem Datum hinzu
        recent_date = (datetime.now() - timedelta(days=100)).isoformat()

        artist_blacklist.blacklist["queen"] = {
            "artist_name": "Queen",
            "song_count": 35,
            "reason": "Test",
            "added_at": recent_date,
            "last_checked": recent_date,
            "check_count": 1,
        }

        # Sollte True zurückgeben (noch nicht Re-Check fällig)
        assert artist_blacklist.is_blacklisted("Queen") is True

    def test_remove_from_blacklist(self, artist_blacklist):
        """Test: Künstler von Blacklist entfernen."""
        artist_blacklist.add_to_blacklist("U2", 28)

        assert artist_blacklist.is_blacklisted("U2") is True

        removed = artist_blacklist.remove_from_blacklist("U2")

        assert removed is True
        assert artist_blacklist.is_blacklisted("U2") is False
        assert len(artist_blacklist.blacklist) == 0

    def test_remove_nonexistent_artist(self, artist_blacklist):
        """Test: Entfernen eines nicht existierenden Künstlers."""
        removed = artist_blacklist.remove_from_blacklist("Nonexistent Band")

        assert removed is False

    def test_get_artists_due_for_recheck(self, artist_blacklist):
        """Test: Ermittlung von Künstlern fällig für Re-Check."""
        # Füge alte und neue Einträge hinzu
        old_date = (datetime.now() - timedelta(days=400)).isoformat()
        recent_date = (datetime.now() - timedelta(days=100)).isoformat()

        artist_blacklist.blacklist["old_artist"] = {
            "artist_name": "Old Artist",
            "song_count": 20,
            "added_at": old_date,
            "last_checked": old_date,
            "check_count": 1,
        }

        artist_blacklist.blacklist["recent_artist"] = {
            "artist_name": "Recent Artist",
            "song_count": 25,
            "added_at": recent_date,
            "last_checked": recent_date,
            "check_count": 1,
        }

        due_artists = artist_blacklist.get_artists_due_for_recheck()

        assert len(due_artists) == 1
        assert due_artists[0]["artist_name"] == "Old Artist"
        assert due_artists[0]["days_since_check"] >= 365

    def test_get_stats(self, artist_blacklist):
        """Test: Statistiken der Blacklist."""
        # Füge mehrere Künstler hinzu
        artist_blacklist.add_to_blacklist("Artist 1", 30)
        artist_blacklist.add_to_blacklist("Artist 2", 25)

        # Simuliere mehrfache Checks
        artist_blacklist.blacklist["artist 1"]["check_count"] = 5
        artist_blacklist.blacklist["artist 2"]["check_count"] = 3

        stats = artist_blacklist.get_stats()

        assert stats["total_artists"] == 2
        assert len(stats["most_checked"]) == 2
        assert stats["most_checked"][0][0] == "Artist 1"
        assert stats["most_checked"][0][1] == 5

    def test_clear_old_entries(self, artist_blacklist):
        """Test: Entfernen alter Einträge."""
        # Füge alte und neue Einträge hinzu
        very_old_date = (datetime.now() - timedelta(days=800)).isoformat()
        recent_date = (datetime.now() - timedelta(days=100)).isoformat()

        artist_blacklist.blacklist["very_old"] = {
            "artist_name": "Very Old Artist",
            "song_count": 15,
            "added_at": very_old_date,
            "last_checked": very_old_date,
            "check_count": 1,
        }

        artist_blacklist.blacklist["recent"] = {
            "artist_name": "Recent Artist",
            "song_count": 20,
            "added_at": recent_date,
            "last_checked": recent_date,
            "check_count": 1,
        }

        removed_count = artist_blacklist.clear_old_entries(days=730)

        assert removed_count == 1
        assert "very_old" not in artist_blacklist.blacklist
        assert "recent" in artist_blacklist.blacklist

    def test_update_last_checked_on_duplicate_add(self, artist_blacklist):
        """Test: Aktualisierung des Datums bei erneutem Hinzufügen."""
        artist_blacklist.add_to_blacklist("Duplicate Artist", 30)

        original_date = artist_blacklist.blacklist["duplicate artist"]["last_checked"]

        # Warte kurz
        import time

        time.sleep(0.1)

        # Füge erneut hinzu
        artist_blacklist.add_to_blacklist("Duplicate Artist", 30)

        new_date = artist_blacklist.blacklist["duplicate artist"]["last_checked"]
        check_count = artist_blacklist.blacklist["duplicate artist"]["check_count"]

        assert new_date >= original_date
        assert check_count == 2


class TestFilteredTopArtists:
    """Tests für get_filtered_top_artists Funktion."""

    @pytest.fixture
    def sample_counter(self):
        """Erstellt Counter mit Sample-Daten."""
        return Counter(
            {
                "Artist A": 100,
                "Artist B": 90,
                "Artist C": 80,
                "Artist D": 70,
                "Artist E": 60,
                "Artist F": 50,
            }
        )

    @pytest.fixture
    def artist_blacklist(self, temp_blacklist_file):
        """Erstellt ArtistBlacklist-Instanz."""
        with patch("utils.artist_blacklist.ARTIST_BLACKLIST_FILE", temp_blacklist_file):
            return ArtistBlacklist()

    @pytest.fixture
    def temp_blacklist_file(self):
        """Temporäre Blacklist-Datei."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            json.dump({}, f)
            temp_path = f.name
        yield temp_path
        if os.path.exists(temp_path):
            os.remove(temp_path)

    def test_get_filtered_top_artists_no_blacklist(self, sample_counter, artist_blacklist):
        """Test: Gefilterte Top-Künstler ohne Blacklist-Einträge."""
        top_artists = get_filtered_top_artists(sample_counter, artist_blacklist, top_n=3)

        assert len(top_artists) == 3
        assert top_artists[0][0] == "Artist A"
        assert top_artists[1][0] == "Artist B"
        assert top_artists[2][0] == "Artist C"

    def test_get_filtered_top_artists_with_blacklist(self, sample_counter, artist_blacklist):
        """Test: Gefilterte Top-Künstler mit geblacklisteten Einträgen."""
        # Blackliste Artist B und C
        artist_blacklist.add_to_blacklist("Artist B", 90)
        artist_blacklist.add_to_blacklist("Artist C", 80)

        top_artists = get_filtered_top_artists(sample_counter, artist_blacklist, top_n=3)

        # Sollte A, D, E zurückgeben (B und C übersprungen)
        assert len(top_artists) == 3
        assert top_artists[0][0] == "Artist A"
        assert top_artists[1][0] == "Artist D"
        assert top_artists[2][0] == "Artist E"

    def test_get_filtered_top_artists_max_total_limit(self, sample_counter, artist_blacklist):
        """Test: max_total Limit wird respektiert."""
        # Blackliste alle außer letzten
        for artist in ["Artist A", "Artist B", "Artist C", "Artist D"]:
            artist_blacklist.add_to_blacklist(artist, 50)

        # Frage 3 an, aber prüfe maximal 4
        top_artists = get_filtered_top_artists(sample_counter, artist_blacklist, top_n=3, max_total=4)

        # Sollte nur Artist E und F finden (innerhalb max_total=4)
        assert len(top_artists) <= 2


class TestUpdateArtistBlacklist:
    """Tests für update_artist_blacklist_from_search_results."""

    @pytest.fixture
    def artist_blacklist(self, temp_blacklist_file):
        """Erstellt ArtistBlacklist-Instanz."""
        with patch("utils.artist_blacklist.ARTIST_BLACKLIST_FILE", temp_blacklist_file):
            return ArtistBlacklist()

    @pytest.fixture
    def temp_blacklist_file(self):
        """Temporäre Blacklist-Datei."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            json.dump({}, f)
            temp_path = f.name
        yield temp_path
        if os.path.exists(temp_path):
            os.remove(temp_path)

    def test_update_no_albums_found(self, artist_blacklist):
        """Test: Keine Alben gefunden - auf Blacklist setzen."""
        update_artist_blacklist_from_search_results(
            "New Artist", 50, found_new_albums=False, artist_blacklist=artist_blacklist
        )

        assert artist_blacklist.is_blacklisted("New Artist") is True

    def test_update_albums_found_not_blacklisted(self, artist_blacklist):
        """Test: Alben gefunden - nicht auf Blacklist setzen."""
        update_artist_blacklist_from_search_results(
            "Popular Artist", 40, found_new_albums=True, artist_blacklist=artist_blacklist
        )

        assert artist_blacklist.is_blacklisted("Popular Artist") is False

    def test_update_albums_found_remove_from_blacklist(self, artist_blacklist):
        """Test: Alben gefunden - von Blacklist entfernen."""
        # Erst auf Blacklist setzen
        artist_blacklist.add_to_blacklist("Previously Blacklisted", 35)

        assert artist_blacklist.is_blacklisted("Previously Blacklisted") is True

        # Neue Alben gefunden
        update_artist_blacklist_from_search_results(
            "Previously Blacklisted", 35, found_new_albums=True, artist_blacklist=artist_blacklist
        )

        assert artist_blacklist.is_blacklisted("Previously Blacklisted") is False


class TestSingleton:
    """Tests für Singleton-Pattern."""

    def test_get_artist_blacklist_singleton(self):
        """Test: get_artist_blacklist gibt immer dieselbe Instanz zurück."""
        instance1 = get_artist_blacklist()
        instance2 = get_artist_blacklist()

        assert instance1 is instance2


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
