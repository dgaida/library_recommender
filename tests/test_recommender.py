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
from unittest.mock import Mock, patch, MagicMock
from collections import defaultdict


# ============================================================================
# tests/test_recommender.py - Aktualisierungen
# ============================================================================


class TestRecommender:
    """Tests für recommender/recommender.py"""

    @pytest.fixture
    def mock_library_search(self):
        """Mock für KoelnLibrarySearch mit UV-Kürzel für Filme."""
        mock = Mock()
        # WICHTIG: Füge "Uv" zum zentralbibliothek_info hinzu für Filme
        mock.search = Mock(
            return_value=[
                {
                    "title": "Test Film",
                    "author": "Test Director",
                    "zentralbibliothek_info": "Uv *Drama* verfügbar in Zentralbibliothek",
                }
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

    @pytest.fixture
    def mock_borrowed_blacklist(self):
        """Mock für BorrowedBlacklist"""
        mock = Mock()
        mock.is_blacklisted = Mock(return_value=False)
        mock.add_to_blacklist = Mock()
        return mock

    def test_suggest_films_with_available_items(
        self, mock_library_search, mock_state, mock_blacklist, mock_borrowed_blacklist
    ):
        """Test suggest_films mit verfügbaren Items (inkl. UV-Kürzel)"""
        from recommender.recommender import Recommender

        with patch("recommender.recommender.get_blacklist", return_value=mock_blacklist):
            with patch("recommender.recommender.get_borrowed_blacklist", return_value=mock_borrowed_blacklist):
                recommender = Recommender(mock_library_search, mock_state)

                films = [{"title": "Test Film", "author": "Test Director", "type": "DVD", "source": "Test Source"}]

                results = recommender.suggest_films(films, items_per_source=4)

                # Sollte 1 Film zurückgeben (hat UV-Kürzel)
                assert len(results) == 1
                assert results[0]["title"] == "Test Film"
                assert "bib_number" in results[0]

    def test_suggest_films_without_uv_filtered(self, mock_state, mock_blacklist, mock_borrowed_blacklist):
        """Test dass Filme ohne UV-Kürzel herausgefiltert werden"""
        from recommender.recommender import Recommender

        # Mock ohne UV-Kürzel
        mock_library_search = Mock()
        mock_library_search.search = Mock(
            return_value=[
                {
                    "title": "Not a Film",
                    "author": "Author",
                    "zentralbibliothek_info": "verfügbar in Zentralbibliothek",  # Kein "Uv"!
                }
            ]
        )

        with patch("recommender.recommender.get_blacklist", return_value=mock_blacklist):
            with patch("recommender.recommender.get_borrowed_blacklist", return_value=mock_borrowed_blacklist):
                recommender = Recommender(mock_library_search, mock_state)

                films = [{"title": "Not a Film", "author": "Author", "type": "DVD", "source": "Test Source"}]

                results = recommender.suggest_films(films, items_per_source=4)

                # Sollte leer sein (kein UV-Kürzel)
                assert len(results) == 0
                # Sollte auf Blacklist gesetzt werden
                mock_blacklist.add_to_blacklist.assert_called()

    def test_suggest_films_blacklisted_items(self, mock_library_search, mock_state, mock_borrowed_blacklist):
        """Test suggest_films mit geblacklisteten Items"""
        from recommender.recommender import Recommender

        mock_blacklist = Mock()
        mock_blacklist.is_blacklisted = Mock(return_value=True)

        with patch("recommender.recommender.get_blacklist", return_value=mock_blacklist):
            with patch("recommender.recommender.get_borrowed_blacklist", return_value=mock_borrowed_blacklist):
                recommender = Recommender(mock_library_search, mock_state)

                films = [{"title": "Blacklisted Film", "author": "Director", "type": "DVD", "source": "Test Source"}]

                results = recommender.suggest_films(films, items_per_source=4)

                # Sollte leer sein, da geblacklistet
                assert len(results) == 0

    def test_suggest_films_no_hits_adds_to_blacklist(self, mock_state, mock_blacklist, mock_borrowed_blacklist):
        """Test dass Items ohne Treffer zur Blacklist hinzugefügt werden"""
        from recommender.recommender import Recommender

        mock_library_search = Mock()
        mock_library_search.search = Mock(return_value=[])  # Keine Treffer

        with patch("recommender.recommender.get_blacklist", return_value=mock_blacklist):
            with patch("recommender.recommender.get_borrowed_blacklist", return_value=mock_borrowed_blacklist):
                recommender = Recommender(mock_library_search, mock_state)

                films = [{"title": "Unknown Film", "author": "Unknown", "type": "DVD", "source": "Test Source"}]

                results = recommender.suggest_films(films, items_per_source=4)

                # Sollte zur Blacklist hinzugefügt worden sein
                mock_blacklist.add_to_blacklist.assert_called_once()
                assert len(results) == 0

    def test_suggest_films_borrowed_items(self, mock_state, mock_blacklist, mock_borrowed_blacklist):
        """Test dass entliehene Filme auf Entleih-Blacklist kommen"""
        from recommender.recommender import Recommender

        # Mock mit entliehenem Film (mit UV!)
        mock_library_search = Mock()
        mock_library_search.search = Mock(
            return_value=[
                {
                    "title": "Borrowed Film",
                    "author": "Director",
                    "zentralbibliothek_info": "Uv *Drama* Entliehen, voraussichtlich bis 15/12/2025",
                }
            ]
        )

        with patch("recommender.recommender.get_blacklist", return_value=mock_blacklist):
            with patch("recommender.recommender.get_borrowed_blacklist", return_value=mock_borrowed_blacklist):
                recommender = Recommender(mock_library_search, mock_state)

                films = [{"title": "Borrowed Film", "author": "Director", "type": "DVD", "source": "Test Source"}]

                results = recommender.suggest_films(films, items_per_source=4)

                # Sollte leer sein (entliehen)
                assert len(results) == 0
                # Sollte auf Entleih-Blacklist gesetzt werden
                mock_borrowed_blacklist.add_to_blacklist.assert_called()

    def test_suggest_albums(self, mock_library_search, mock_state, mock_blacklist, mock_borrowed_blacklist):
        """Test suggest_albums (keine UV-Filterung für Alben)"""
        from recommender.recommender import Recommender

        with patch("recommender.recommender.get_blacklist", return_value=mock_blacklist):
            with patch("recommender.recommender.get_borrowed_blacklist", return_value=mock_borrowed_blacklist):
                recommender = Recommender(mock_library_search, mock_state)

                albums = [{"title": "Test Album", "author": "Test Artist", "type": "CD", "source": "Test Source"}]

                results = recommender.suggest_albums(albums, items_per_source=4)

                # Sollte 1 Album zurückgeben
                assert len(results) == 1
                assert results[0]["title"] == "Test Album"

    def test_suggest_books(self, mock_library_search, mock_state, mock_blacklist, mock_borrowed_blacklist):
        """Test suggest_books (keine UV-Filterung für Bücher)"""
        from recommender.recommender import Recommender

        with patch("recommender.recommender.get_blacklist", return_value=mock_blacklist):
            with patch("recommender.recommender.get_borrowed_blacklist", return_value=mock_borrowed_blacklist):
                recommender = Recommender(mock_library_search, mock_state)

                books = [{"title": "Test Book", "author": "Test Author", "type": "Buch", "source": "Test Source"}]

                results = recommender.suggest_books(books, items_per_source=4)

                # Sollte 1 Buch zurückgeben
                assert len(results) == 1
                assert results[0]["title"] == "Test Book"


# ============================================================================
# Pytest Configuration
# ============================================================================

if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
