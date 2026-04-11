#!/usr/bin/env python3
"""Unit tests for albums and books data sources."""

import pytest
from data_sources.albums import fetch_radioeins_albums, search_radioeins_albums_in_library
from data_sources.books import fetch_books_from_site


def test_fetch_radioeins_albums(requests_mock):
    """Test fetching albums from Radioeins."""
    mock_html = """
    <div class="table layoutstandard">
        <table>
            <tr><td>1</td><td>Radiohead</td><td>OK Computer</td></tr>
            <tr><td>2</td><td>The Beatles</td><td>Abbey Road</td></tr>
        </table>
    </div>
    """
    requests_mock.get(
        "https://www.radioeins.de/musik/top_100/die-100-besten-2019/alben/alben---die-top-100.html", text=mock_html
    )

    albums = fetch_radioeins_albums()
    assert len(albums) == 2
    assert albums[0] == ("Radiohead", "OK Computer")
    assert albums[1] == ("The Beatles", "Abbey Road")


def test_search_radioeins_albums_in_library(requests_mock, mocker):
    """Test searching Radioeins albums in library."""
    mock_html = """
    <div class="table layoutstandard">
        <table>
            <tr><td>1</td><td>Radiohead</td><td>OK Computer</td></tr>
        </table>
    </div>
    """
    requests_mock.get(
        "https://www.radioeins.de/musik/top_100/die-100-besten-2019/alben/alben---die-top-100.html", text=mock_html
    )

    # Mock filters and search engine
    mocker.patch("data_sources.albums.filter_existing_albums", return_value=[("Radiohead", "OK Computer")])
    mock_search = mocker.patch("data_sources.albums.KoelnLibrarySearch")
    mock_instance = mock_search.return_value
    mock_instance.search.return_value = [{"title": "OK Computer", "author": "Radiohead"}]

    # Mock save_results_to_markdown to avoid file I/O
    mocker.patch("data_sources.albums.save_results_to_markdown")
    mocker.patch("time.sleep")  # Speed up tests

    search_radioeins_albums_in_library(limit=1)

    mock_instance.search.assert_called_once_with("Radiohead OK Computer CD")


def test_fetch_books_from_site(requests_mock):
    """Test fetching books from NYT canon site."""
    mock_html = """
    <a class="accordionlink">1. Elena Ferrante: Meine geniale Freundin</a>
    <div class="accordionarea">
        <div class="paragraph">Eine wunderbare Geschichte aus Neapel.</div>
    </div>
    <a class="accordionlink">2. Colson Whitehead: Die Underground Railroad</a>
    <div class="accordionarea">
        <div class="paragraph">Ein wichtiges Buch über die Sklaverei.</div>
    </div>
    """
    requests_mock.get(
        "https://www.die-besten-aller-zeiten.de/buecher/kanon/new-york-times-21-jahrhundert.html", text=mock_html
    )

    books = fetch_books_from_site()
    assert len(books) == 2
    assert books[0]["title"] == "Meine geniale Freundin"
    assert books[0]["author"] == "Elena Ferrante"
    assert "Neapel" in books[0]["description"]
    assert books[1]["title"] == "Die Underground Railroad"
    assert books[1]["author"] == "Colson Whitehead"
