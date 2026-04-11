#!/usr/bin/env python3
"""
Unit Tests für die Bibliothek-Empfehlungs-App

Installation:
    pip install pytest pytest-cov pytest-mock

Ausführen:
    pytest tests/
    pytest tests/ -v                    # Verbose
    pytest tests/ --cov=.              # Mit Coverage
    pytest tests/test_filters.py       # Einzelne Datei
"""

import pytest
import os
import tempfile

# ============================================================================
# tests/test_filters.py
# ============================================================================


class TestFilters:
    """Tests für preprocessing/filters.py"""

    def test_filter_existing_albums_empty_list(self):
        """Test mit leerer Album-Liste"""
        from preprocessing.filters import filter_existing_albums

        result = filter_existing_albums([], "/nonexistent/path")
        assert result == []

    def test_filter_existing_albums_nonexistent_path(self):
        """Test mit nicht-existierendem Pfad"""
        from preprocessing.filters import filter_existing_albums

        albums = [{"author": "Radiohead", "title": "OK Computer", "source": "Test"}]
        result = filter_existing_albums(albums, "/nonexistent/path")
        # Sollte alle Alben zurückgeben, da Pfad nicht existiert
        assert len(result) == 1
        assert result[0]["title"] == "OK Computer"

    def test_filter_existing_albums_with_mock_filesystem(self):
        """Test mit gemocktem Dateisystem"""
        from preprocessing.filters import filter_existing_albums

        albums = [
            {"author": "Radiohead", "title": "OK Computer", "source": "Test"},
            {"author": "Pink Floyd", "title": "Dark Side of the Moon", "source": "Test"},
        ]

        with tempfile.TemporaryDirectory() as tmpdir:
            # Erstelle einen Ordner für ein vorhandenes Album
            os.makedirs(os.path.join(tmpdir, "Radiohead - OK Computer"))

            result = filter_existing_albums(albums, tmpdir)

            # Nur "Dark Side of the Moon" sollte zurückgegeben werden
            assert len(result) == 1
            assert result[0]["title"] == "Dark Side of the Moon"

    def test_filter_preserves_all_properties(self):
        """Test dass alle Properties erhalten bleiben"""
        from preprocessing.filters import filter_existing_albums

        albums = [
            {
                "author": "Test Artist",
                "title": "Test Album",
                "source": "Test Source",
                "year": "2020",
                "custom_field": "custom_value",
            }
        ]

        with tempfile.TemporaryDirectory() as tmpdir:
            result = filter_existing_albums(albums, tmpdir)

            assert len(result) == 1
            assert result[0]["custom_field"] == "custom_value"
            assert result[0]["source"] == "Test Source"

    def test_normalize_album_title(self):
        """Test album title normalization."""
        from preprocessing.filters import normalize_album_title

        assert normalize_album_title("OK Computer [CD]", "Radiohead") == "radiohead ok computer"
        assert normalize_album_title("Abbey Road (2019 Mix)", "The Beatles") == "the beatles abbey road"

    def test_albums_are_similar(self):
        """Test similarity check between albums."""
        from preprocessing.filters import albums_are_similar

        album1 = {"title": "OK Computer", "author": "Radiohead"}
        album2 = {"title": "OK Computer [Tonträger]", "author": "Radiohead"}
        assert albums_are_similar(album1, album2) is True

        album3 = {"title": "Kid A", "author": "Radiohead"}
        assert albums_are_similar(album1, album3) is False

    def test_get_album_statistics(self, mocker):
        """Test album statistics generation."""
        from preprocessing.filters import get_album_statistics

        mocker.patch("os.path.exists", return_value=True)
        mocker.patch("preprocessing.filters._get_existing_folders", return_value={"radiohead - ok computer"})

        albums = [{"title": "OK Computer", "author": "Radiohead"}, {"title": "Kid A", "author": "Radiohead"}]

        stats = get_album_statistics(albums, "/archive")
        assert stats["original_count"] == 2
        assert stats["found_count"] == 1
        assert stats["missing_count"] == 1


# ============================================================================
# Pytest Configuration
# ============================================================================

if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
