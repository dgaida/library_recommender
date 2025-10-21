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
    
    def test_save_recommendations_to_markdown(self):
        """Test save_recommendations_to_markdown"""
        from utils.io import save_recommendations_to_markdown
        
        recommendations = {
            'films': [
                {'title': 'Test Film', 'author': 'Director', 'bib_number': 'verfügbar'}
            ],
            'albums': [
                {'title': 'Test Album', 'author': 'Artist', 'bib_number': 'ausgeliehen'}
            ],
            'books': []
        }
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.md', delete=False) as f:
            filename = f.name
        
        try:
            result_filename = save_recommendations_to_markdown(recommendations, filename)
            
            assert os.path.exists(result_filename)
            
            with open(result_filename, 'r', encoding='utf-8') as f:
                content = f.read()
                
            assert 'Test Film' in content
            assert 'Test Album' in content
            assert '🎬 Filme' in content
            assert '🎵 Musik/Alben' in content
            
        finally:
            if os.path.exists(filename):
                os.remove(filename)


# ============================================================================
# Pytest Configuration
# ============================================================================

if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
