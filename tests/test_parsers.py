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
# tests/test_parsers.py
# ============================================================================

class TestParsers:
    """Tests für library/parsers.py"""
    
    def test_normalize_text_removes_stopwords(self):
        """Test dass Füllwörter entfernt werden"""
        from library.parsers import normalize_text
        
        assert normalize_text("The Dark Side of the Moon") == "dark side moon"
        assert normalize_text("A Day in the Life") == "day life"
    
    def test_normalize_text_removes_special_chars(self):
        """Test dass Sonderzeichen entfernt werden"""
        from library.parsers import normalize_text
        
        assert normalize_text("What's Going On?") == "whats going"
        assert normalize_text("Rock & Roll!") == "rock roll"
    
    def test_normalize_text_lowercase(self):
        """Test dass Text in Kleinbuchstaben konvertiert wird"""
        from library.parsers import normalize_text
        
        assert normalize_text("UPPERCASE TEXT") == "uppercase text"
    
    def test_normalize_text_empty_string(self):
        """Test mit leerem String"""
        from library.parsers import normalize_text
        
        assert normalize_text("") == ""
        assert normalize_text(None) == ""
    
    def test_create_search_variants_basic(self):
        """Test Erstellung von Suchvarianten"""
        from library.parsers import create_search_variants
        
        variants = create_search_variants("Radiohead", "OK Computer")
        
        # Sollte mehrere Varianten enthalten
        assert len(variants) > 0
        assert "radiohead ok computer" in variants
    
    def test_create_search_variants_with_brackets(self):
        """Test mit Klammern im Titel"""
        from library.parsers import create_search_variants
        
        variants = create_search_variants("Oasis", "(What's The Story) Morning Glory?")
        
        # Sollte Variante ohne Klammern enthalten
        assert any("morning glory" in v for v in variants)
    
    def test_fuzzy_match_exact(self):
        """Test Fuzzy-Matching mit exakter Übereinstimmung"""
        from library.parsers import fuzzy_match, create_search_variants
        
        search_terms = create_search_variants("Radiohead", "OK Computer")
        existing = "Radiohead - OK Computer"
        
        assert fuzzy_match(search_terms, existing, "Radiohead", "OK Computer")
    
    def test_fuzzy_match_case_insensitive(self):
        """Test Fuzzy-Matching case-insensitive"""
        from library.parsers import fuzzy_match, create_search_variants
        
        search_terms = create_search_variants("radiohead", "ok computer")
        existing = "RADIOHEAD - OK COMPUTER"
        
        assert fuzzy_match(search_terms, existing, "radiohead", "ok computer")


# ============================================================================
# Pytest Configuration
# ============================================================================

if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
