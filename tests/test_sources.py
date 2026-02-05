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
# tests/test_sources.py
# ============================================================================


class TestSources:
    """Tests für utils/sources.py"""

    def test_get_source_emoji_known_sources(self):
        """Test get_source_emoji mit bekannten Quellen"""
        from utils.sources import get_source_emoji, SOURCE_OSCAR_BEST_PICTURE, SOURCE_BBC_100_FILMS

        assert get_source_emoji(SOURCE_OSCAR_BEST_PICTURE) == "🏆"
        assert get_source_emoji(SOURCE_BBC_100_FILMS) == "🎬"

    def test_get_source_emoji_personalized(self):
        """Test get_source_emoji mit personalisierten Empfehlungen"""
        from utils.sources import get_source_emoji

        source = "Interessant für dich (Top-Interpret: Radiohead)"
        assert get_source_emoji(source) == "💎"

    def test_get_source_emoji_unknown(self):
        """Test get_source_emoji mit unbekannter Quelle"""
        from utils.sources import get_source_emoji

        assert get_source_emoji("Unknown Source") == ""

    def test_format_source_for_display(self):
        """Test format_source_for_display"""
        from utils.sources import format_source_for_display, SOURCE_OSCAR_BEST_PICTURE

        formatted = format_source_for_display(SOURCE_OSCAR_BEST_PICTURE)
        assert "🏆" in formatted
        assert SOURCE_OSCAR_BEST_PICTURE in formatted


# ============================================================================
# Pytest Configuration
# ============================================================================

if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
