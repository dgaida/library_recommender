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
# tests/test_io.py
# ============================================================================


class TestIO:
    """Tests für utils/io.py"""

    def test_save_recommendations_to_pdf(self):
        """Test save_recommendations_to_pdf"""
        from utils.io import save_recommendations_to_pdf

        recommendations = {
            "films": [{"title": "Test Film", "author": "Director", "bib_number": "verfügbar"}],
            "albums": [{"title": "Test Album", "author": "Artist", "bib_number": "ausgeliehen"}],
            "books": [],
        }

        with tempfile.NamedTemporaryFile(mode="w", suffix=".pdf", delete=False) as f:
            filename = f.name

        try:
            result_filename = save_recommendations_to_pdf(recommendations, filename)

            assert os.path.exists(result_filename)
            assert os.path.getsize(result_filename) > 0

        finally:
            if os.path.exists(filename):
                os.remove(filename)


# ============================================================================
# Pytest Configuration
# ============================================================================

if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
