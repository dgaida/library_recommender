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


# ============================================================================
# Pytest Configuration
# ============================================================================

if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
