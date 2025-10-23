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


# ============================================================================
# tests/test_search_utils.py
# ============================================================================


class TestSearchUtils:
    """Tests für utils/search_utils.py"""

    def test_extract_title_and_author_with_separator(self):
        """Test extract_title_and_author mit Separator"""
        from utils.search_utils import extract_title_and_author

        title, author = extract_title_and_author("Test Film - Test Director")

        assert title == "Test Film"
        assert author == "Test Director"

    def test_extract_title_and_author_without_separator(self):
        """Test extract_title_and_author ohne Separator"""
        from utils.search_utils import extract_title_and_author

        title, author = extract_title_and_author("Test Film")

        assert title == "Test Film"
        assert author is None

    def test_extract_title_and_author_with_whitespace(self):
        """Test extract_title_and_author mit Whitespace"""
        from utils.search_utils import extract_title_and_author

        title, author = extract_title_and_author("  Test Film  -  Test Director  ")

        assert title == "Test Film"
        assert author == "Test Director"


# ============================================================================
# Pytest Configuration
# ============================================================================

if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
