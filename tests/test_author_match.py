#!/usr/bin/env python3
"""
Unit Tests für Author-Matching Funktionalität
"""

import pytest
from library.search import (
    normalize_name,
    calculate_name_similarity,
    extract_person_field,
    check_author_match,
    filter_results_by_author,
)


class TestNameNormalization:
    """Tests für Name-Normalisierung"""

    def test_normalize_name_lastname_first(self):
        """Test Normalisierung bei Nachname, Vorname Format"""
        assert normalize_name("Mühlhoff, Rainer") == "rainer mühlhoff"
        assert normalize_name("Coppola, Francis Ford") == "francis ford coppola"

    def test_normalize_name_firstname_first(self):
        """Test Normalisierung bei Vorname Nachname Format"""
        assert normalize_name("Rainer Mühlhoff") == "rainer mühlhoff"
        assert normalize_name("Francis Ford Coppola") == "francis ford coppola"

    def test_normalize_name_special_chars(self):
        """Test Entfernung von Sonderzeichen"""
        assert normalize_name("O'Connor, John") == "john o connor"
        assert normalize_name("Jean-Luc Godard") == "jean luc godard"


class TestNameSimilarity:
    """Tests für Namens-Ähnlichkeit"""

    def test_exact_match(self):
        """Test exakte Übereinstimmung"""
        similarity = calculate_name_similarity("francis ford coppola", "francis ford coppola")
        assert similarity == 1.0

    def test_lastname_match(self):
        """Test Nachnamen-Match"""
        similarity = calculate_name_similarity("francis ford coppola", "coppola")
        assert similarity >= 0.90  # Sehr hohe Ähnlichkeit

    def test_partial_match(self):
        """Test Teil-Übereinstimmung"""
        similarity = calculate_name_similarity("rainer mühlhoff", "mühlhoff")
        assert similarity >= 0.90

    def test_no_match(self):
        """Test keine Übereinstimmung"""
        similarity = calculate_name_similarity("francis ford coppola", "steven spielberg")
        assert similarity < 0.5


class TestPersonFieldExtraction:
    """Tests für Person(en)-Feld Extraktion"""

    def test_extract_person_field_author(self):
        """Test Extraktion von Autor"""
        text = "Person(en): Mühlhoff, Rainer Verfasser"
        result = extract_person_field(text)
        assert result == "Mühlhoff, Rainer"

    def test_extract_person_field_director(self):
        """Test Extraktion von Regisseur"""
        text = "Person(en): Coppola, Francis Ford Regisseur"
        result = extract_person_field(text)
        assert result == "Coppola, Francis Ford"

    def test_extract_person_field_actor(self):
        """Test Extraktion von Schauspieler"""
        text = "Person(en): Pacino, Al Schauspieler"
        result = extract_person_field(text)
        assert result == "Pacino, Al"

    def test_extract_person_field_not_found(self):
        """Test wenn kein Person(en)-Feld vorhanden"""
        text = "Nur normale Verfügbarkeit ohne Person"
        result = extract_person_field(text)
        assert result is None


class TestAuthorMatch:
    """Tests für Author-Match Funktion"""

    def test_match_in_person_field(self):
        """Test Match im Person(en)-Feld"""
        result = {"title": "Künstliche Intelligenz", "zentralbibliothek_info": "Person(en): Mühlhoff, Rainer Verfasser"}

        match_found, score, field = check_author_match(result, "Rainer Mühlhoff")

        assert match_found is True
        assert score >= 0.95
        assert field == "person_field"

    def test_match_in_full_text(self):
        """Test Match im Volltext (Fallback)"""
        result = {
            "title": "Der Pate",
            "zentralbibliothek_info": ("Titel: Der Pate / Francis Ford Coppola\n" "Person(en): Pacino, Al Schauspieler"),
        }

        match_found, score, field = check_author_match(result, "Francis Ford Coppola")

        assert match_found is True
        assert score >= 0.7
        assert field == "full_text"

    def test_no_match(self):
        """Test kein Match"""
        result = {"title": "Anderes Buch", "zentralbibliothek_info": "Person(en): Schmidt, Hans Verfasser"}

        match_found, score, field = check_author_match(result, "Rainer Mühlhoff")

        assert match_found is False
        assert score < 0.7
        assert field == "no_match"

    def test_no_expected_author(self):
        """Test wenn kein Autor erwartet wird"""
        result = {"title": "Irgendein Buch", "zentralbibliothek_info": "Person(en): Jemand Verfasser"}

        match_found, score, field = check_author_match(result, "")

        assert match_found is True  # Akzeptiert alles
        assert field == "no_author_specified"


class TestFilterByAuthor:
    """Tests für Autor-basierte Filterung"""

    def test_filter_sorted_by_score(self):
        """Test dass Ergebnisse nach Score sortiert werden"""
        results = [
            {"title": "Buch 1", "zentralbibliothek_info": "Person(en): Müller, Hans Verfasser"},
            {"title": "Buch 2", "zentralbibliothek_info": "Person(en): Mühlhoff, Rainer Verfasser"},
            {"title": "Buch 3", "zentralbibliothek_info": "Autor: Rainer Mühlhoff, Soziologe"},
        ]

        filtered = filter_results_by_author(results, "Rainer Mühlhoff", threshold=0.5)

        # Sollte nach Score sortiert sein (beste zuerst)
        assert len(filtered) >= 2
        assert filtered[0]["author_match_score"] >= filtered[1]["author_match_score"]


class TestRealWorldScenarios:
    """Tests für reale Szenarien"""

    def test_coppola_movie_scenario(self):
        """Test Pate-Film mit Coppola als Regisseur"""
        result = {
            "title": "Der Pate : Trilogie",
            "zentralbibliothek_info": (
                "Signatur: Uv *Krimi/Thriller* Pate\n"
                "Titel: Der Pate : Trilogie / Francis Ford Coppola; Al Pacino\n"
                "Person(en): Pacino, Al Regisseur ; Schauspieler"
            ),
        }

        # Sollte Coppola trotzdem finden (im Volltext)
        match_found, score, field = check_author_match(result, "Francis Ford Coppola")

        assert match_found is True
        assert score >= 0.7
        assert field in ["full_text", "title_field"]

    def test_muhlhoff_book_scenario(self):
        """Test Mühlhoff-Buch Szenario"""
        result = {
            "title": "Künstliche Intelligenz und der neue Faschismus",
            "zentralbibliothek_info": (
                "Signatur: Aqm 2 Mühlhoff Gesellschaft-7\n"
                "Titel: Künstliche Intelligenz und der neue Faschismus / Rainer Mühlhoff\n"
                "Person(en): Mühlhoff, Rainer Verfasser"
            ),
        }

        match_found, score, field = check_author_match(result, "Rainer Mühlhoff")

        assert match_found is True
        assert score >= 0.95
        assert field == "person_field"

    def test_kygo_artist_scenario(self):
        """Test Kygo Künstler-Suche"""
        results = [
            {"title": "Cloud Nine", "zentralbibliothek_info": "Person(en): Kygo Interpret"},
            {"title": "Golden Hour", "zentralbibliothek_info": "Person(en): Kygo Komponist"},
            {"title": "Some Other Album", "zentralbibliothek_info": "Person(en): Other Artist"},
        ]

        filtered = filter_results_by_author(results, "Kygo")

        assert len(filtered) == 2
        assert all("Kygo" in r["zentralbibliothek_info"] for r in filtered)


class TestEdgeCases:
    """Tests für Edge Cases"""

    def test_empty_person_field(self):
        """Test mit leerem Person(en)-Feld"""
        result = {"title": "Test", "zentralbibliothek_info": "Person(en): "}

        match_found, score, field = check_author_match(result, "Test Author")

        # Sollte im Fulltext suchen
        assert match_found is False or field != "person_field"

    def test_multiple_persons(self):
        """Test mit mehreren Personen im Feld"""
        result = {"title": "Test", "zentralbibliothek_info": ("Person(en): Müller, Hans ; Schmidt, Anna Verfasser")}

        match_found1, _, _ = check_author_match(result, "Hans Müller")
        match_found2, _, _ = check_author_match(result, "Anna Schmidt")

        assert match_found1 is True
        assert match_found2 is True

    def test_special_characters_in_name(self):
        """Test mit Sonderzeichen im Namen"""
        result = {"title": "Test", "zentralbibliothek_info": "Person(en): O'Connor, Séan Verfasser"}

        match_found, score, _ = check_author_match(result, "Sean O'Connor")

        assert match_found is True
        assert score >= 0.7

    def test_abbreviated_names(self):
        """Test mit abgekürzten Namen"""
        result = {"title": "Test", "zentralbibliothek_info": "Person(en): King, S. Verfasser"}

        # Sollte nicht zu Stephen King matchen (zu unsicher)
        match_found, score, _ = check_author_match(result, "Stephen King", threshold=0.8)

        # Je nach Implementierung könnte das matchen oder nicht
        # Der Test prüft, dass der Score angemessen ist
        assert score < 0.9  # Nicht zu sicher bei Abkürzungen


# Integrations-Test
def test_full_workflow():
    """Test kompletter Workflow"""
    # Simuliere Suche nach "Der Pate" von "Coppola"
    search_results = [
        {
            "title": "Der Pate",
            "zentralbibliothek_info": (
                "Titel: Der Pate / Francis Ford Coppola\n" "Person(en): Pacino, Al Schauspieler\n" "Uv *Drama* verfügbar"
            ),
        },
        {
            "title": "Der Pate II",
            "zentralbibliothek_info": (
                "Person(en): De Niro, Robert Schauspieler\n" "Regie: Francis Ford Coppola\n" "Uv verfügbar"
            ),
        },
        {"title": "Anderer Film", "zentralbibliothek_info": ("Person(en): Andere Person Regisseur\n" "verfügbar")},
    ]

    # Filtere nach Coppola
    filtered = filter_results_by_author(search_results, "Francis Ford Coppola", threshold=0.7)

    # Sollte die beiden Pate-Filme finden
    assert len(filtered) >= 2
    assert "Pate" in filtered[0]["title"]

    # Sollte nach Score sortiert sein
    assert filtered[0]["author_match_score"] >= filtered[1]["author_match_score"]


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
