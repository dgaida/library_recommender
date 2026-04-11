#!/usr/bin/env python3
"""Unit tests for search logic and KoelnLibrarySearch."""

import pytest
from datetime import datetime, timedelta
from library.search import (
    KoelnLibrarySearch,
    calculate_name_similarity,
    extract_person_field,
    normalize_name,
    filter_results_by_author,
)
from utils.borrowed_blacklist import BorrowedBlacklist


def test_normalize_name():
    """Test name normalization."""
    assert normalize_name("Coppola, Francis Ford") == "francis ford coppola"
    assert normalize_name("  Michael   Radford  ") == "michael radford"
    assert normalize_name("Müller, Hans-Peter") == "hans peter müller"
    assert normalize_name("") == ""


def test_calculate_name_similarity():
    """Test name similarity scoring."""
    assert calculate_name_similarity("stephen king", "stephen king") == 1.0
    assert calculate_name_similarity("stephen king", "king") == 0.7
    assert calculate_name_similarity("stephen king", "s. king") == 0.6
    assert calculate_name_similarity("stephen king", "john smith") < 0.3
    assert calculate_name_similarity("", "name") == 0.0


def test_extract_person_field():
    """Test extracting persons from library availability text."""
    text = "Person(en): Radford, Michael Regisseur ; Burton, Richard Schauspieler ; Erschienen: 1984"
    persons = extract_person_field(text)
    assert "Radford, Michael" in persons
    assert "Burton, Richard" in persons

    text = "Person(en): King, Stephen Autor [Verfasser] Umfang: 300 S."
    persons = extract_person_field(text)
    assert persons == ["King, Stephen"]


def test_filter_results_by_author():
    """Test filtering results by author and title."""
    results = [
        {"title": "The Godfather", "zentralbibliothek_info": "Person(en): Coppola, Francis Ford Regisseur"},
        {"title": "Not The Godfather", "zentralbibliothek_info": "Person(en): Other Author"},
    ]
    filtered = filter_results_by_author(results, "Francis Ford Coppola")
    assert len(filtered) == 1
    assert filtered[0]["title"] == "The Godfather"

    # With title match
    filtered = filter_results_by_author(results, "Francis Ford Coppola", expected_title="The Godfather")
    assert len(filtered) == 1
    assert filtered[0]["title"] == "The Godfather"
    assert "combined_score" in filtered[0]


def test_search_advanced_search(requests_mock, mocker):
    """Test advanced search in KoelnLibrarySearch."""
    search_engine = KoelnLibrarySearch()

    # Mock safe_get for the form page
    form_html = '<form name="AdvancedSearch" action="search_action"></form>'
    requests_mock.get(
        "https://katalog.stbib-koeln.de/alswww2.dll/APS_ZONES?fn=AdvancedSearch&Style=Portal3&SubStyle=&Lang=GER&ResponseEncoding=utf-8",
        text=form_html,
    )

    # Mock post for the search results
    results_html = '<html><td class="SummaryDataCell"><a class="SummaryFieldLink" href="detail">Title</a></td></html>'
    requests_mock.post("https://katalog.stbib-koeln.de/alswww2.dll/search_action", text=results_html)

    # Mock get_availability_details to avoid further requests
    mocker.patch.object(KoelnLibrarySearch, "get_availability_details", return_value={})

    results = search_engine.advanced_search(title="Test")
    assert len(results) == 1
    assert results[0]["title"] == "Title"


def test_extract_item_data(mocker):
    """Test extraction of item data from BeautifulSoup element."""
    from bs4 import BeautifulSoup

    search_engine = KoelnLibrarySearch()
    mocker.patch.object(
        search_engine,
        "get_availability_details",
        return_value={"Zentralbibliothek": "Verfügbar", "Zentralbibliothek_full": "Metadaten + Verfügbar"},
    )

    html = """
    <td class="SummaryDataCell">
        <a class="SummaryFieldLink" href="link1">Title 1</a>
        <td class="SummaryFieldData">Author Name,</td>
        <td class="SummaryFieldData">2023</td>
        <td class="SummaryMaterialTypeField">DVD</td>
        <div class="SummaryActionBox">Verfügbar</div>
    </td>
    """
    soup = BeautifulSoup(html, "html.parser")
    item = soup.find("td")

    data = search_engine._extract_item_data(item)
    assert data["title"] == "Title 1"
    assert data["author"] == "Author Name,"
    assert data["year"] == "2023"
    assert data["material_type"] == "DVD"


def test_get_availability_details_fallbacks(requests_mock):
    """Test various fallbacks in get_availability_details."""
    search_engine = KoelnLibrarySearch()

    # Test stock_header fallback
    html = """
    <div id="stock_header_1">Zentralbibliothek</div>
    <div>Verfügbar, Regal 1</div>
    <div id="stock_header_2">Stadtteilbibliothek Mülheim</div>
    <div>verfügbar</div>
    """
    requests_mock.get("http://detail", text=html)
    details = search_engine.get_availability_details("http://detail")
    assert details["_zentralbib_available"] is True
    assert "stadtteilbibliothek mülheim" in details["_stadtbib_available"]

    # Test table fallback
    html = """
    <table>
        <tr><td>Zentralbibliothek</td><td>Im Regal (Verfügbar)</td></tr>
    </table>
    """
    requests_mock.get("http://detail-table", text=html)
    details = search_engine.get_availability_details("http://detail-table")
    assert "Zentralbibliothek" in details
    assert "verfügbar" in details["Zentralbibliothek"].lower()


class TestBorrowedBlacklist:
    """Tests for BorrowedBlacklist."""

    @pytest.fixture
    def blacklist(self, mocker, tmp_path):
        """Fixture for BorrowedBlacklist with mocked file path."""
        data_dir = tmp_path / "data"
        data_dir.mkdir()
        mocker.patch("utils.borrowed_blacklist.DATA_DIR", str(data_dir))
        mocker.patch("utils.borrowed_blacklist.BORROWED_BLACKLIST_FILE", str(data_dir / "entliehen_blacklist.json"))
        return BorrowedBlacklist()

    def test_extract_return_date(self, blacklist):
        """Test extracting return date from text."""
        assert blacklist.extract_return_date("voraussichtlich bis 08/11/2025") == "2025-11-08"
        assert blacklist.extract_return_date("Entliehen, bis 31/12/2024") == "2024-12-31"
        assert blacklist.extract_return_date("Sofort verfügbar") is None

    def test_is_blacklisted(self, blacklist):
        """Test blacklisting logic based on return date."""
        # Add item that is borrowed until tomorrow
        future_date = (datetime.now() + timedelta(days=1)).strftime("%d/%m/%Y")
        availability = f"Entliehen, bis {future_date}"

        blacklist.add_to_blacklist("Inception", "Nolan", "DVD", availability)
        assert blacklist.is_blacklisted("Inception", "Nolan") is True

        # Add item that was borrowed until yesterday
        past_date = (datetime.now() - timedelta(days=1)).strftime("%d/%m/%Y")
        availability = f"Entliehen, bis {past_date}"
        blacklist.add_to_blacklist("Old Movie", "Old Director", "DVD", availability)
        assert blacklist.is_blacklisted("Old Movie", "Old Director") is False

    def test_cleanup_expired_entries(self, blacklist):
        """Test cleaning up expired entries."""
        past_date = (datetime.now() - timedelta(days=1)).strftime("%d/%m/%Y")
        blacklist.add_to_blacklist("Expired", "Author", "DVD", f"bis {past_date}")

        future_date = (datetime.now() + timedelta(days=1)).strftime("%d/%m/%Y")
        blacklist.add_to_blacklist("Active", "Author", "DVD", f"bis {future_date}")

        removed = blacklist.cleanup_expired_entries()
        assert removed == 1
        assert len(blacklist.blacklist) == 1
