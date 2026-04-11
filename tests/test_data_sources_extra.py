#!/usr/bin/env python3
"""Unit tests for guides, imdb_films, and oscar_music data sources."""
import pytest
import json
from data_sources.guides import fetch_guides_from_site
from data_sources.imdb_films import fetch_imdb_top250
from data_sources.oscar_music import fetch_oscar_music_winners

def test_fetch_guides_from_site(requests_mock):
    """Test fetching guides from site."""
    mock_html = """
    <h2>Die besten Ratgeber des 21. Jahrhunderts</h2>
    <a class="accordionlink">Daniel Kahneman: Schnelles Denken, langsames Denken (2011)</a>
    <div class="accordionarea">
        <p>Ein Buch über kognitive Verzerrungen.</p>
    </div>
    <h2 class="sqrallwaysboxed">Die besten Jugendbücher des 21. Jahrhunderts</h2>
    <a class="accordionlink">Should be ignored</a>
    """
    requests_mock.get("https://www.die-besten-aller-zeiten.de/buecher/kanon/buecher-des-21-jahrhunderts.html", text=mock_html)

    guides = fetch_guides_from_site()
    assert len(guides) == 1
    assert guides[0]["title"] == "Schnelles Denken, langsames Denken"
    assert guides[0]["author"] == "Daniel Kahneman"
    assert "kognitive Verzerrungen" in guides[0]["description"]

def test_fetch_imdb_top250(requests_mock):
    """Test fetching IMDb Top 250 from JSON-LD."""
    mock_json = {
        "itemListElement": [
            {
                "item": {
                    "name": "The Shawshank Redemption",
                    "description": "Two imprisoned men bond over a number of years...",
                    "aggregateRating": {"ratingValue": 9.3, "ratingCount": 2800000},
                    "genre": "Drama",
                    "duration": "PT2H22M",
                    "url": "https://www.imdb.com/title/tt0111161/",
                    "image": "poster.jpg"
                }
            }
        ]
    }
    mock_html = f'<html><script type="application/ld+json">{json.dumps(mock_json)}</script></html>'
    requests_mock.get("https://www.imdb.com/chart/top", text=mock_html)

    films = fetch_imdb_top250()
    assert len(films) == 1
    assert films[0]["title"] == "The Shawshank Redemption"
    assert films[0]["rating"] == 9.3

def test_fetch_oscar_music_winners(requests_mock):
    """Test fetching Oscar Music winners from Wikipedia."""
    mock_html = """
    <table class="wikitable">
        <tr><th>Jahr</th><th>Preisträger</th><th>Film</th></tr>
        <tr>
            <td><a href="/wiki/Oscarverleihung_1998">1998</a></td>
            <td>James Horner</td>
            <td><a href="/wiki/Titanic_(1997)" title="Titanic (1997)">Titanic</a></td>
        </tr>
    </table>
    """
    requests_mock.get("https://de.wikipedia.org/wiki/Oscar/Beste_Filmmusik", text=mock_html)

    winners = fetch_oscar_music_winners()
    assert len(winners) == 1
    assert winners[0]["title"] == "Titanic (1997) (Soundtrack)"
    assert winners[0]["author"] == "James Horner"
    assert winners[0]["year"] == "1998"
