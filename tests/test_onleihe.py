import pytest
from unittest.mock import MagicMock, patch
from recommender.recommender import Recommender

class TestOnleiheSupport:
    @pytest.fixture
    def mock_lib_search(self):
        mock = MagicMock()
        return mock

    @pytest.fixture
    def mock_state(self):
        from recommender.state import AppState
        state = AppState()
        # Reset session caches
        state.session_unavailable = {"films": set(), "albums": set(), "books": set()}
        state.session_searched_artists = set()
        return state

    @pytest.fixture
    def recommender(self, mock_lib_search, mock_state):
        return Recommender(mock_lib_search, mock_state)

    def test_recommender_prioritizes_onleihe(self, recommender, mock_lib_search):
        # Setup: One item with Onleihe link
        item = {"title": "Digital Book", "author": "Author", "type": "Buch", "source": "Source"}

        # Mock search to return hit
        mock_lib_search.search.return_value = [{"title": "Digital Book", "author": "Author", "link": "http://test.com"}]

        # Mock availability details to include Onleihe
        # This is what _check_all_bibs calls via get_availability_details
        mock_lib_search.get_availability_details.return_value = {
            "_onleihe_link": "http://onleihe.de/test",
            "_onleihe_text": "Onleihe-Titel"
        }

        # Mock author match to return hits
        with patch("recommender.recommender.filter_results_by_author") as mock_filter:
            mock_filter.return_value = [{"title": "Digital Book", "author": "Author", "link": "http://test.com"}]

            # The test failed because the previous blacklist was persisting in some way
            # or the mock was not correctly returning from _check_availability.
            # Let's ensure the blacklist is empty.
            from utils.blacklist import get_blacklist
            get_blacklist().clear_blacklist()

            result = recommender._check_availability(item, "books")

            assert result is not None
            assert "📱" in result["title"]
            assert result["onleihe_link"] == "http://onleihe.de/test"
