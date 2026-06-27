import pytest
from unittest.mock import MagicMock, patch
from recommender.recommender import Recommender
from recommender.state import AppState


def test_no_redundant_artist_search():
    mock_lib_search = MagicMock()
    state = AppState()
    # Ensure fresh session
    state.reset_session_cache()
    recommender = Recommender(mock_lib_search, state)

    with patch("recommender.recommender.search_artist_albums_in_library") as mock_search_lib, patch(
        "recommender.recommender.get_artist_blacklist"
    ) as mock_get_blacklist, patch("recommender.recommender.update_artist_blacklist_from_search_results") as _, patch(
        "recommender.recommender.filter_existing_albums", side_effect=lambda albums, path: albums
    ):

        mock_blacklist = MagicMock()
        mock_blacklist.is_blacklisted.return_value = False
        mock_get_blacklist.return_value = mock_blacklist

        # Mock search to return empty list
        mock_search_lib.return_value = []

        albums = []
        top_artists = ["Artist 1"]

        # First call should trigger search
        recommender.suggest_albums(albums, n=1, items_per_source=1, top_artists=top_artists)
        assert mock_search_lib.call_count == 1

        # Second call should NOT trigger search
        recommender.suggest_albums(albums, n=1, items_per_source=1, top_artists=top_artists)
        assert mock_search_lib.call_count == 1


def test_no_redundant_item_search():
    mock_lib_search = MagicMock()
    state = AppState()
    state.reset_session_cache()
    recommender = Recommender(mock_lib_search, state)

    # Mock search to return something, but _check_availability will return None
    mock_lib_search.search.return_value = [{"title": "Film 1", "author": "Director 1", "link": "http://test.com"}]

    with patch.object(Recommender, "_check_availability", return_value=None) as mock_check:
        films = [{"title": "Film 1", "author": "Director 1", "type": "DVD", "source": "Source 1"}]

        # First call should trigger availability check
        recommender.suggest_films(films, n=1, items_per_source=1)
        assert mock_check.call_count == 1

        # Second call should NOT trigger check (skipped due to session_unavailable)
        recommender.suggest_films(films, n=1, items_per_source=1)
        assert mock_check.call_count == 1


if __name__ == "__main__":
    pytest.main([__file__])
