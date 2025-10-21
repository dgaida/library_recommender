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
import json
import tempfile
from unittest.mock import patch


# ============================================================================
# tests/test_state.py
# ============================================================================

class TestAppState:
    """Tests für recommender/state.py"""
    
    @pytest.fixture
    def temp_state_file(self):
        """Erstellt temporäre state.json für Tests"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump({"films": [], "albums": [], "books": []}, f)
            temp_path = f.name
        
        yield temp_path
        
        # Cleanup
        if os.path.exists(temp_path):
            os.remove(temp_path)
    
    def test_app_state_init(self):
        """Test Initialisierung von AppState"""
        from recommender.state import AppState
        
        with patch('recommender.state.STATE_FILE', '/tmp/test_state.json'):
            state = AppState()
            
            assert 'films' in state.rejected
            assert 'albums' in state.rejected
            assert 'books' in state.rejected
            assert isinstance(state.suggested, dict)
    
    def test_mark_suggested(self):
        """Test mark_suggested Methode"""
        from recommender.state import AppState
        
        with patch('recommender.state.STATE_FILE', '/tmp/test_state.json'):
            state = AppState()
            item = {'title': 'Test Film', 'author': 'Test Director'}
            
            state.mark_suggested('films', item)
            
            assert len(state.suggested['films']) == 1
            assert state.suggested['films'][0]['title'] == 'Test Film'
    
    def test_is_already_suggested(self):
        """Test is_already_suggested Methode"""
        from recommender.state import AppState
        
        with patch('recommender.state.STATE_FILE', '/tmp/test_state.json'):
            state = AppState()
            item = {'title': 'Test Film', 'author': 'Test Director'}
            
            # Initial nicht vorgeschlagen
            assert not state.is_already_suggested('films', item)
            
            # Nach mark_suggested sollte es erkannt werden
            state.mark_suggested('films', item)
            assert state.is_already_suggested('films', item)
    
    def test_reject_item(self):
        """Test reject Methode"""
        from recommender.state import AppState
        
        with patch('recommender.state.STATE_FILE', '/tmp/test_state.json'):
            with patch.object(AppState, 'save_rejected_state'):
                state = AppState()
                item = {'title': 'Test Film', 'author': 'Test Director'}
                
                state.reject('films', item)
                
                assert len(state.rejected['films']) == 1
                assert state.rejected['films'][0]['title'] == 'Test Film'
    
    def test_reject_duplicate_prevention(self):
        """Test dass Duplikate nicht mehrfach abgelehnt werden"""
        from recommender.state import AppState
        
        with patch('recommender.state.STATE_FILE', '/tmp/test_state.json'):
            with patch.object(AppState, 'save_rejected_state'):
                state = AppState()
                item = {'title': 'Test Film', 'author': 'Test Director'}
                
                state.reject('films', item)
                state.reject('films', item)  # Zweiter Versuch
                
                # Sollte nur einmal vorhanden sein
                assert len(state.rejected['films']) == 1
    
    def test_get_stats(self):
        """Test get_stats Methode"""
        from recommender.state import AppState
        
        with patch('recommender.state.STATE_FILE', '/tmp/test_state.json'):
            with patch.object(AppState, 'save_rejected_state'):
                state = AppState()
                
                # Füge Testdaten hinzu
                state.mark_suggested('films', {'title': 'Film 1', 'author': 'Director 1'})
                state.reject('albums', {'title': 'Album 1', 'author': 'Artist 1'})
                
                stats = state.get_stats()
                
                assert stats['suggested_total'] == 1
                assert stats['rejected_total'] == 1
                assert stats['suggested_by_category']['films'] == 1
                assert stats['rejected_by_category']['albums'] == 1


# ============================================================================
# Pytest Configuration
# ============================================================================

if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
