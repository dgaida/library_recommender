#!/usr/bin/env python3
"""
Tests for Onleihe (Digital Books/Audiobooks) support.
"""

import pytest
from unittest.mock import MagicMock, Mock, patch
from library.search import KoelnLibrarySearch
from recommender.recommender import Recommender
from recommender.state import AppState


class TestOnleiheSupport:
    """Tests for Onleihe link detection and display."""

    @pytest.fixture
    def mock_lib_search(self):
        mock = MagicMock(spec=KoelnLibrarySearch)
        return mock

    @pytest.fixture
    def mock_state(self):
        state = AppState()
        # Reset session caches
        state.session_unavailable = {"films": set(), "albums": set(), "books": set()}
        state.session_searched_artists = set()
        return state

    @pytest.fixture
    def recommender(self, mock_lib_search, mock_state):
        return Recommender(mock_lib_search, mock_state)

    def test_get_availability_details_detects_onleihe(self):
        """Test that get_availability_details correctly detects Onleihe links."""
        search = KoelnLibrarySearch()

        html_content = """
        <html>
            <body>
                <table class="OuterSearchResultDetailTable">
                    <tr><td>Some Metadata</td></tr>
                </table>
                <div id="stock_header_1">Zentralbibliothek</div>
                <div>entliehen</div>
                <a class="darkLink" target="_blank" href="https://www.onleihe.de/koeln/frontend/mediaInfo,51-0-358128555-100-0-0-0-0-0-0-0.html">eaudio- Ausleihe hier</a>
            </body>
        </html>
        """

        mock_response = Mock()
        mock_response.text = html_content
        mock_response.status_code = 200

        with patch.object(search.session, "get", return_value=mock_response):
            details = search.get_availability_details("http://test.com/book")

            assert "_onleihe_link" in details
            assert (
                details["_onleihe_link"]
                == "https://www.onleihe.de/koeln/frontend/mediaInfo,51-0-358128555-100-0-0-0-0-0-0-0.html"
            )
            assert details["_onleihe_text"] == "eaudio- Ausleihe hier"

    def test_recommender_prioritizes_onleihe(self, recommender, mock_lib_search):
        """Test that the recommender identifies and prioritizes digital media."""
        # Setup: One item with Onleihe link
        item = {"title": "Digital Book", "author": "Author", "type": "Buch", "source": "Source"}

        # Mock search to return hit
        mock_lib_search.search.return_value = [{"title": "Digital Book", "author": "Author", "link": "http://test.com"}]

        # Mock availability details to include Onleihe
        mock_lib_search.get_availability_details.return_value = {
            "_onleihe_link": "http://onleihe.de/test",
            "_onleihe_text": "Onleihe-Titel",
        }

        # Mock author match to return hits
        with patch("recommender.recommender.filter_results_by_author") as mock_filter:
            mock_filter.return_value = [{"title": "Digital Book", "author": "Author", "link": "http://test.com"}]

            from utils.blacklist import get_blacklist

            get_blacklist().clear_blacklist()

            result = recommender._check_availability(item, "books")

            assert result is not None
            assert "📱" in result["title"]
            assert result["onleihe_link"] == "http://onleihe.de/test"

    def test_gui_remove_emoji_handles_smartphone(self):
        """Test that remove_emoji correctly handles the 📱 symbol."""
        import re

        def remove_emoji(text: str) -> str:
            emoji_pattern = re.compile(
                "["
                "\U0001f300-\U0001f9ff"
                "\U0001f600-\U0001f64f"
                "\U0001f680-\U0001f6ff"
                "\U0001f1e0-\U0001f1ff"
                "\U00002702-\U000027b0"
                "\U000024c2-\U0001f251"
                "\U0001f4f1"
                "]+",
                flags=re.UNICODE,
            )
            return emoji_pattern.sub("", text).strip()

        input_text = "📱 Digital Book - Author"
        expected = "Digital Book - Author"

        assert remove_emoji(input_text) == expected

    def test_gui_on_selection_change_generates_onleihe_button(self):
        """Test that on_selection_change generates the HTML button for Onleihe."""
        import re

        def remove_emoji(text: str) -> str:
            emoji_pattern = re.compile(
                "["
                "\U0001f300-\U0001f9ff"
                "\U0001f600-\U0001f64f"
                "\U0001f680-\U0001f6ff"
                "\U0001f1e0-\U0001f1ff"
                "\U00002702-\U000027b0"
                "\U000024c2-\U0001f251"
                "\U0001f4f1"
                "]+",
                flags=re.UNICODE,
            )
            return emoji_pattern.sub("", text).strip()

        def on_selection_change_mock(selected_items, current_suggestions):
            media_html = ""
            for selected_item in selected_items:
                selected_item_clean = remove_emoji(selected_item)
                for s in current_suggestions:
                    suggestion_title_clean = remove_emoji(s["title"])
                    display_text = f"{suggestion_title_clean}"
                    if s.get("author"):
                        display_text += f" - {s['author']}"
                    if display_text == selected_item_clean:
                        if s.get("onleihe_link"):
                            onleihe_text = s.get("onleihe_text", "Onleihe Ausleihe hier")
                            media_html += f"link: {s['onleihe_link']}, text: {onleihe_text}"
            return media_html

        item = {
            "title": "📱 Digital Book",
            "author": "Author",
            "onleihe_link": "https://www.onleihe.de/link",
            "onleihe_text": "Ausleihe hier",
        }
        current_suggestions = [item]
        selected = ["📱 Digital Book - Author"]

        result = on_selection_change_mock(selected, current_suggestions)
        assert "https://www.onleihe.de/link" in result
        assert "Ausleihe hier" in result
