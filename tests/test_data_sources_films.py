#!/usr/bin/env python3
"""Unit tests for film data sources."""
import pytest
from data_sources.fbw_films import fetch_fbw_films, fetch_oscar_best_picture_winners
from data_sources.films import fetch_wikipedia_titles

def test_fetch_fbw_films(requests_mock):
    """Test fetching FBW films."""
    mock_html = """
    <div class="row--filmitem clearfix">
        <div class="film_rating"><img alt="besonders wertvoll" src="seal.png"></div>
        <h2><a href="/filme/das_leben_der_anderen">Das Leben der Anderen</a></h2>
        <div class="row--filmitem-additionalinfos-cast">Regie: Florian Henckel von Donnersmarck | Producer: ...</div>
        <p class="film_presstext">Ein DDR-Drama.</p>
    </div>
    """
    requests_mock.get("https://www.fbw-filmbewertung.com/filme?page=1", text=mock_html)

    # Mock subsequent pages as empty to stop pagination
    for p in range(2, 6):
        requests_mock.get(f"https://www.fbw-filmbewertung.com/filme?page={p}", text="")

    films = fetch_fbw_films(max_pages=2)
    assert len(films) == 1
    assert films[0]["title"] == "Das Leben der Anderen"
    assert films[0]["author"] == "Florian Henckel von Donnersmarck"
    assert films[0]["description"] == "Ein DDR-Drama."

def test_fetch_oscar_best_picture_winners(requests_mock):
    """Test fetching Oscar Best Picture winners from Wikipedia."""
    mock_html = """
    <table class="wikitable">
        <tr><th>№</th><th>Jahr</th><th>Produzent</th><th>Film</th></tr>
        <tr>
            <td>96</td>
            <td><a href="/wiki/Oscarverleihung_2024">2024</a></td>
            <td>Emma Thomas</td>
            <td><a href="/wiki/Oppenheimer_(Film)" title="Oppenheimer (Film)">Oppenheimer</a></td>
        </tr>
    </table>
    """
    requests_mock.get("https://de.wikipedia.org/wiki/Oscar/Bester_Film", text=mock_html)

    winners = fetch_oscar_best_picture_winners()
    assert len(winners) == 1
    assert winners[0]["title"] == "Oppenheimer (Film)"
    assert winners[0]["year"] == "2024"

def test_fetch_wikipedia_titles(requests_mock):
    """Test fetching BBC 100 Greatest Films from Wikipedia."""
    mock_html = """
    <h3>Liste der häufigsten Nennungen</h3>
    <table class="wikitable">
        <tr><th>№</th><th>Originaltitel</th><th>Deutscher Titel</th><th>Regie</th></tr>
        <tr><td>1</td><td>Mulholland Dr.</td><td>Mulholland Drive</td><td>David Lynch</td></tr>
    </table>
    """
    requests_mock.get("https://de.wikipedia.org/wiki/BBC_Culture%E2%80%99s_100_Greatest_Films_of_the_21st_Century", text=mock_html)

    titles = fetch_wikipedia_titles()
    assert len(titles) == 1
    assert titles[0]["title"] == "Mulholland Dr."
    assert titles[0]["regie"] == "Mulholland Drive"
