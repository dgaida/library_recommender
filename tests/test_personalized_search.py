import pytest
from unittest.mock import MagicMock, patch
from recommender.recommender import Recommender

class TestPersonalizedSearch:
    @pytest.fixture
    def mock_lib_search(self):
        return MagicMock()

    @pytest.fixture
    def mock_state(self):
        state = MagicMock()
        state.is_already_suggested.return_value = False
        return state

    @pytest.fixture
    def recommender(self, mock_lib_search, mock_state):
        return Recommender(mock_lib_search, mock_state)

    def test_suggest_albums_triggers_active_search(self, recommender):
        # Setup: Empty cache for "Personalisiert"
        albums = [
            {"title": "Radio 1 Album", "author": "Artist A", "type": "CD", "source": "Radio Eins Top 100 Alben 2019"}
        ]
        top_artists = ["Madonna"]

        with patch("recommender.recommender.search_artist_albums_in_library") as mock_search_lib, \
             patch("recommender.recommender.get_artist_blacklist") as mock_get_blacklist, \
             patch("recommender.recommender.update_artist_blacklist_from_search_results") as mock_update_blacklist:

            mock_blacklist = MagicMock()
            mock_blacklist.is_blacklisted.return_value = False
            mock_get_blacklist.return_value = mock_blacklist

            mock_search_lib.return_value = [
                {"title": "Ray of Light", "author": "Madonna", "type": "CD", "source": "Interessant für dich (Top-Interpret: Madonna)"}
            ]

            recommender._check_availability = MagicMock(side_effect=lambda item, cat: item)

            suggestions = recommender.suggest_albums(albums, n=2, items_per_source=1, top_artists=top_artists)

            assert any(s["author"] == "Madonna" for s in suggestions)
            assert any(s["source"] == "Radio Eins Top 100 Alben 2019" for s in suggestions)

    def test_suggest_albums_searches_until_target_reached(self, recommender):
        # Setup: We want 2 personalized albums, none in cache
        albums = []
        top_artists = ["Artist 1", "Artist 2", "Artist 3"]

        with patch("recommender.recommender.search_artist_albums_in_library") as mock_search_lib, \
             patch("recommender.recommender.get_artist_blacklist") as mock_get_blacklist, \
             patch("recommender.recommender.update_artist_blacklist_from_search_results") as mock_update_blacklist:

            mock_blacklist = MagicMock()
            mock_blacklist.is_blacklisted.return_value = False
            mock_get_blacklist.return_value = mock_blacklist

            # Artist 1 has no albums
            # Artist 2 has 1 album
            # Artist 3 has 1 album
            mock_search_lib.side_effect = [
                [],
                [{"title": "Album 2", "author": "Artist 2", "type": "CD", "source": "Interessant für dich (Top-Interpret: Artist 2)"}],
                [{"title": "Album 3", "author": "Artist 3", "type": "CD", "source": "Interessant für dich (Top-Interpret: Artist 3)"}]
            ]

            recommender._check_availability = MagicMock(side_effect=lambda item, cat: item)

            suggestions = recommender.suggest_albums(albums, n=2, items_per_source=2, top_artists=top_artists)

            assert len(suggestions) == 2
            assert suggestions[0]["author"] == "Artist 2"
            assert suggestions[1]["author"] == "Artist 3"

    def test_suggest_albums_stops_when_target_reached(self, recommender):
        # Setup: We want 1 personalized album, none in cache
        albums = []
        top_artists = ["Artist 1", "Artist 2"]

        with patch("recommender.recommender.search_artist_albums_in_library") as mock_search_lib, \
             patch("recommender.recommender.get_artist_blacklist") as mock_get_blacklist, \
             patch("recommender.recommender.update_artist_blacklist_from_search_results") as mock_update_blacklist:

            mock_blacklist = MagicMock()
            mock_blacklist.is_blacklisted.return_value = False
            mock_get_blacklist.return_value = mock_blacklist

            mock_search_lib.return_value = [
                {"title": "Album 1", "author": "Artist 1", "type": "CD", "source": "Interessant für dich (Top-Interpret: Artist 1)"}
            ]

            recommender._check_availability = MagicMock(side_effect=lambda item, cat: item)

            suggestions = recommender.suggest_albums(albums, n=1, items_per_source=1, top_artists=top_artists)

            assert len(suggestions) == 1
            assert mock_search_lib.call_count == 1
