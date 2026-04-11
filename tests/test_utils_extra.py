#!/usr/bin/env python3
"""Unit tests for search_utils.py and favorites.py."""

import pytest
from utils.search_utils import (
    search_itunes_cover,
    search_youtube_trailer,
    search_cover_image,
    extract_title_and_author,
    search_media_info,
)
from utils.favorites import FavoritesManager


def test_search_itunes_cover(requests_mock):
    """Test searching iTunes for album cover."""
    mock_response = {"resultCount": 1, "results": [{"artworkUrl100": "http://example.com/100x100bb.jpg"}]}
    requests_mock.get("https://itunes.apple.com/search", json=mock_response)

    url = search_itunes_cover("OK Computer", "Radiohead")
    assert url == "http://example.com/600x600bb.jpg"


def test_search_youtube_trailer(mocker):
    """Test searching YouTube for trailer."""
    mock_ddgs = mocker.patch("utils.search_utils.DDGS")
    mock_instance = mock_ddgs.return_value.__enter__.return_value
    mock_instance.text.return_value = [{"href": "https://www.youtube.com/watch?v=dQw4w9WgXcQ"}]

    video_id = search_youtube_trailer("The Godfather")
    assert video_id == "dQw4w9WgXcQ"


def test_extract_title_and_author():
    """Test extracting title and author from display text."""
    assert extract_title_and_author("Der Pate - Francis Ford Coppola") == ("Der Pate", "Francis Ford Coppola")
    assert extract_title_and_author("Standalone Movie") == ("Standalone Movie", None)


class TestFavoritesManager:
    """Tests for FavoritesManager."""

    @pytest.fixture
    def manager(self, mocker, tmp_path):
        """Fixture for FavoritesManager with mocked file path."""
        data_dir = tmp_path / "data"
        data_dir.mkdir()
        mocker.patch("utils.favorites.DATA_DIR", str(data_dir))
        mocker.patch("utils.favorites.FAVORITES_FILE", str(data_dir / "favoriten.json"))
        return FavoritesManager()

    def test_add_remove_favorite(self, manager):
        """Test adding and removing favorites."""
        assert manager.add_favorite("films", "Inception", "Christopher Nolan") is True
        assert manager._is_favorite("films", "Inception", "Christopher Nolan") is True
        assert manager.add_favorite("films", "Inception", "Christopher Nolan") is False  # Duplicate

        assert manager.remove_favorite("films", "Inception", "Christopher Nolan") is True
        assert manager._is_favorite("films", "Inception", "Christopher Nolan") is False

    def test_get_stats(self, manager):
        """Test getting stats."""
        manager.add_favorite("films", "Inception", "Christopher Nolan")
        manager.add_favorite("albums", "OK Computer", "Radiohead")

        stats = manager.get_stats()
        assert stats["total_favorites"] == 2
        assert stats["by_category"]["films"] == 1
        assert stats["by_category"]["albums"] == 1


def test_search_media_info(mocker):
    """Test searching media info with DDG."""
    mock_ddgs = mocker.patch("utils.search_utils.DDGS")
    mock_instance = mock_ddgs.return_value.__enter__.return_value
    mock_instance.text.return_value = [{"title": "Result", "body": "Body", "href": "http://example.com"}]

    results = search_media_info("Inception", media_type="film")
    assert len(results) == 1
    assert results[0]["title"] == "Result"


def test_summarize_with_groq(mocker):
    """Test summarizing with Groq API."""
    mocker.patch("os.getenv", return_value="fake_key")
    mock_groq = mocker.patch("utils.search_utils.Groq")
    mock_client = mock_groq.return_value
    mock_client.chat.completions.create.return_value.choices[0].message.content = "This is a summary."

    from utils.search_utils import summarize_with_groq

    summary = summarize_with_groq([{"title": "T", "body": "B"}], "Title")
    assert summary == "This is a summary."


def test_get_media_summary(mocker):
    """Test get_media_summary combined function."""
    mocker.patch("utils.search_utils.search_media_info", return_value=[{"title": "T", "body": "B"}])
    mocker.patch("utils.search_utils.summarize_with_groq", return_value="Summary")
    mocker.patch("utils.search_utils.search_youtube_trailer", return_value="vid123")
    mocker.patch("utils.search_utils.search_cover_image", return_value="http://img.jpg")

    from utils.search_utils import get_media_summary

    res = get_media_summary("Title", media_type="film")
    assert res["summary"] == "Summary"
    assert res["youtube_id"] == "vid123"
    assert res["cover_url"] == "http://img.jpg"


def test_favorites_manager_persistence(tmp_path, mocker):
    """Test FavoritesManager file I/O."""
    data_dir = tmp_path / "data"
    data_dir.mkdir()
    fav_file = data_dir / "favoriten.json"
    mocker.patch("utils.favorites.DATA_DIR", str(data_dir))
    mocker.patch("utils.favorites.FAVORITES_FILE", str(fav_file))

    from utils.favorites import FavoritesManager

    manager = FavoritesManager()
    manager.add_favorite("films", "Title", "Author")

    # New instance should load from file
    manager2 = FavoritesManager()
    assert manager2._is_favorite("films", "Title", "Author") is True
