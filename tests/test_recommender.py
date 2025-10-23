#!/usr/bin/env python3
"""
Unit Tests für die Bibliothek-Empfehlungs-App

Installation:
    pip install pytest pytest-cov pytest-mock

Ausführen:
    pytest tests/
    pytest tests/ -v                    # Verbose
    pytest tests/ --cov=.              # Mit Coverage
    pytest tests/test_filters.py       # Einzelne Datei
"""

import pytest
from unittest.mock import Mock, patch


# ============================================================================
# tests/test_recommender.py
# ============================================================================


class TestRecommender:
    """Tests für recommender/recommender.py"""

    @pytest.fixture
    def mock_library_search(self):
        """Mock für KoelnLibrarySearch"""
        mock = Mock()
        mock.search = Mock(
            return_value=[
                {"title": "Test Film", "author": "Test Director", "zentralbibliothek_info": "verfügbar in Zentralbibliothek"}
            ]
        )
        return mock

    @pytest.fixture
    def mock_state(self):
        """Mock für AppState"""
        from recommender.state import AppState

        with patch("recommender.state.STATE_FILE", "/tmp/test_state.json"):
            return AppState()

    @pytest.fixture
    def mock_blacklist(self):
        """Mock für Blacklist"""
        mock = Mock()
        mock.is_blacklisted = Mock(return_value=False)
        mock.add_to_blacklist = Mock()
        return mock

    def test_suggest_films_with_available_items(self, mock_library_search, mock_state, mock_blacklist):
        """Test suggest_films mit verfügbaren Items"""
        from recommender.recommender import Recommender

        with patch("recommender.recommender.get_blacklist", return_value=mock_blacklist):
            recommender = Recommender(mock_library_search, mock_state)

            films = [{"title": "Test Film", "author": "Test Director", "type": "DVD"}]

            results = recommender.suggest_films(films, n=1)

            assert len(results) == 1
            assert results[0]["title"] == "Test Film"
            assert "bib_number" in results[0]

    def test_suggest_films_blacklisted_items(self, mock_library_search, mock_state, mock_blacklist):
        """Test suggest_films mit geblacklisteten Items"""
        from recommender.recommender import Recommender

        mock_blacklist.is_blacklisted = Mock(return_value=True)

        with patch("recommender.recommender.get_blacklist", return_value=mock_blacklist):
            recommender = Recommender(mock_library_search, mock_state)

            films = [{"title": "Blacklisted Film", "author": "Director", "type": "DVD"}]

            results = recommender.suggest_films(films, n=1)

            # Sollte leer sein, da geblacklistet
            assert len(results) == 0

    def test_suggest_films_no_hits_adds_to_blacklist(self, mock_library_search, mock_state, mock_blacklist):
        """Test dass Items ohne Treffer zur Blacklist hinzugefügt werden"""
        from recommender.recommender import Recommender

        mock_library_search.search = Mock(return_value=[])  # Keine Treffer

        with patch("recommender.recommender.get_blacklist", return_value=mock_blacklist):
            recommender = Recommender(mock_library_search, mock_state)

            films = [{"title": "Unknown Film", "author": "Unknown", "type": "DVD"}]

            results = recommender.suggest_films(films, n=1)

            # Sollte zur Blacklist hinzugefügt worden sein
            mock_blacklist.add_to_blacklist.assert_called_once()
            assert len(results) == 0

    def test_suggest_albums(self, mock_library_search, mock_state, mock_blacklist):
        """Test suggest_albums"""
        from recommender.recommender import Recommender

        with patch("recommender.recommender.get_blacklist", return_value=mock_blacklist):
            recommender = Recommender(mock_library_search, mock_state)

            albums = [{"title": "Test Album", "author": "Test Artist", "type": "CD"}]

            results = recommender.suggest_albums(albums, n=1)

            assert len(results) == 1
            assert results[0]["title"] == "Test Album"

    def test_suggest_books(self, mock_library_search, mock_state, mock_blacklist):
        """Test suggest_books"""
        from recommender.recommender import Recommender

        with patch("recommender.recommender.get_blacklist", return_value=mock_blacklist):
            recommender = Recommender(mock_library_search, mock_state)

            books = [{"title": "Test Book", "author": "Test Author", "type": "Buch"}]

            results = recommender.suggest_books(books, n=1)

            assert len(results) == 1
            assert results[0]["title"] == "Test Book"


# ============================================================================
# Pytest Configuration
# ============================================================================

if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
