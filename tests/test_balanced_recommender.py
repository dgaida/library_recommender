#!/usr/bin/env python3
"""
Unit Tests für das balancierte Recommender-System

Testet die Funktionalität zur gleichmäßigen Verteilung von Empfehlungen
aus verschiedenen Datenquellen.
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
from collections import defaultdict
from recommender.recommender import Recommender
from recommender.state import AppState


class TestBalancedRecommender:
    """Tests für balancierte Empfehlungs-Verteilung."""

    @pytest.fixture
    def mock_library_search(self):
        """Mock für KoelnLibrarySearch mit verfügbaren Items."""
        mock = Mock()
        mock.search = Mock(
            return_value=[
                {"title": "Test Film", "author": "Test Director", "zentralbibliothek_info": "verfügbar in Zentralbibliothek"}
            ]
        )
        return mock

    @pytest.fixture
    def mock_state(self):
        """Mock für AppState."""
        with patch("recommender.state.STATE_FILE", "/tmp/test_state.json"):
            return AppState()

    @pytest.fixture
    def mock_blacklist(self):
        """Mock für Blacklist."""
        mock = Mock()
        mock.is_blacklisted = Mock(return_value=False)
        mock.add_to_blacklist = Mock()
        return mock

    @pytest.fixture
    def sample_films(self):
        """Erstellt Sample-Filme aus verschiedenen Quellen."""
        films = []

        # 10 BBC Filme
        for i in range(10):
            films.append(
                {
                    "title": f"BBC Film {i + 1}",
                    "author": f"BBC Director {i + 1}",
                    "type": "DVD",
                    "source": "BBC 100 Greatest Films of the 21st Century",
                }
            )

        # 10 FBW Filme
        for i in range(10):
            films.append(
                {
                    "title": f"FBW Film {i + 1}",
                    "author": f"FBW Director {i + 1}",
                    "type": "DVD",
                    "source": "FBW Prädikat besonders wertvoll",
                }
            )

        # 10 Oscar Filme
        for i in range(10):
            films.append(
                {
                    "title": f"Oscar Film {i + 1}",
                    "author": f"Oscar Director {i + 1}",
                    "type": "DVD",
                    "source": "Oscar (Bester Film)",
                }
            )

        return films

    @pytest.fixture
    def sample_albums(self):
        """Erstellt Sample-Alben aus verschiedenen Quellen."""
        albums = []

        # 10 Radio Eins Alben
        for i in range(10):
            albums.append(
                {
                    "title": f"Radio Album {i + 1}",
                    "author": f"Radio Artist {i + 1}",
                    "type": "CD",
                    "source": "Radio Eins Top 100 Alben 2019",
                }
            )

        # 10 Oscar Filmmusik
        for i in range(10):
            albums.append(
                {
                    "title": f"Oscar Soundtrack {i + 1}",
                    "author": f"Composer {i + 1}",
                    "type": "CD",
                    "source": "Oscar (Beste Filmmusik)",
                }
            )

        # 10 Personalisierte
        for i in range(10):
            albums.append(
                {
                    "title": f"Personal Album {i + 1}",
                    "author": f"Top Artist {i + 1}",
                    "type": "CD",
                    "source": f"Interessant für dich (Top-Interpret: Artist {i + 1})",
                }
            )

        return albums

    def test_get_items_by_source(self, mock_library_search, mock_state, mock_blacklist, sample_films):
        """Test: Gruppierung von Items nach Quelle."""
        with patch("recommender.recommender.get_blacklist", return_value=mock_blacklist):
            recommender = Recommender(mock_library_search, mock_state)

            items_by_source = recommender._get_items_by_source(sample_films)

            # Sollte 3 Quellen haben
            assert len(items_by_source) == 3

            # Jede Quelle sollte 10 Items haben
            assert len(items_by_source["BBC 100 Greatest Films of the 21st Century"]) == 10
            assert len(items_by_source["FBW Prädikat besonders wertvoll"]) == 10
            assert len(items_by_source["Oscar (Bester Film)"]) == 10

    def test_balanced_film_recommendations(self, mock_library_search, mock_state, mock_blacklist, sample_films):
        """Test: Balancierte Filmempfehlungen (4 pro Quelle)."""
        with patch("recommender.recommender.get_blacklist", return_value=mock_blacklist):
            recommender = Recommender(mock_library_search, mock_state)

            results = recommender.suggest_films(sample_films, n=12, items_per_source=4)

            # Sollte 12 Filme zurückgeben
            assert len(results) == 12

            # Zähle Filme pro Quelle
            source_counts = defaultdict(int)
            for film in results:
                source = film.get("source", "Unbekannt")
                source_counts[source] += 1

            # Jede Quelle sollte 4 Filme beigetragen haben
            assert source_counts["BBC 100 Greatest Films of the 21st Century"] == 4
            assert source_counts["FBW Prädikat besonders wertvoll"] == 4
            assert source_counts["Oscar (Bester Film)"] == 4

    def test_balanced_album_recommendations(self, mock_library_search, mock_state, mock_blacklist, sample_albums):
        """Test: Balancierte Album-Empfehlungen (4 pro Quelle)."""
        with patch("recommender.recommender.get_blacklist", return_value=mock_blacklist):
            recommender = Recommender(mock_library_search, mock_state)

            results = recommender.suggest_albums(sample_albums, n=12, items_per_source=4)

            # Sollte 12 Alben zurückgeben
            assert len(results) == 12

            # Zähle Alben pro Quelle (mit Normalisierung für personalisierte)
            source_counts = defaultdict(int)
            for album in results:
                source = album.get("source", "Unbekannt")
                # Normalisiere personalisierte Empfehlungen
                if "Interessant für dich" in source:
                    source = "Personalisiert"
                source_counts[source] += 1

            # Jede Quelle sollte 4 Alben beigetragen haben
            assert source_counts["Radio Eins Top 100 Alben 2019"] == 4
            assert source_counts["Oscar (Beste Filmmusik)"] == 4
            assert source_counts["Personalisiert"] == 4

    def test_exhausted_sources(self, mock_library_search, mock_state, mock_blacklist):
        """Test: Verhalten wenn Quellen erschöpft sind."""
        # Nur 2 Filme von einer Quelle
        limited_films = [
            {
                "title": f"Film {i}",
                "author": f"Director {i}",
                "type": "DVD",
                "source": "BBC 100 Greatest Films of the 21st Century",
            }
            for i in range(2)
        ]

        with patch("recommender.recommender.get_blacklist", return_value=mock_blacklist):
            recommender = Recommender(mock_library_search, mock_state)

            # Frage 12 Filme an, aber nur 2 verfügbar
            results = recommender.suggest_films(limited_films, n=12, items_per_source=4)

            # Sollte maximal 2 zurückgeben
            assert len(results) <= 2

    def test_personalized_source_normalization(self, mock_library_search, mock_state, mock_blacklist):
        """Test: Normalisierung personalisierter Quellen."""
        albums_with_different_artists = [
            {
                "title": f"Album {i}",
                "author": f"Artist {i}",
                "type": "CD",
                "source": f"Interessant für dich (Top-Interpret: Artist {i})",
            }
            for i in range(10)
        ]

        with patch("recommender.recommender.get_blacklist", return_value=mock_blacklist):
            recommender = Recommender(mock_library_search, mock_state)

            items_by_source = recommender._get_items_by_source(albums_with_different_artists)

            # Alle personalisierten Empfehlungen sollten unter "Personalisiert" sein
            assert "Personalisiert" in items_by_source
            assert len(items_by_source["Personalisiert"]) == 10

    def test_skip_already_suggested(self, mock_library_search, mock_state, mock_blacklist, sample_films):
        """Test: Bereits vorgeschlagene Items werden übersprungen."""
        with patch("recommender.recommender.get_blacklist", return_value=mock_blacklist):
            recommender = Recommender(mock_library_search, mock_state)

            # Markiere ersten Film als bereits vorgeschlagen
            mock_state.mark_suggested("films", sample_films[0])

            results = recommender.suggest_films(sample_films, n=12, items_per_source=4)

            # Erster Film sollte nicht in Ergebnissen sein
            result_titles = [film["title"] for film in results]
            assert sample_films[0]["title"] not in result_titles


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
