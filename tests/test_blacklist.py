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
import tempfile
from unittest.mock import patch


# ============================================================================
# tests/test_blacklist.py
# ============================================================================

class TestBlacklist:
    """Tests für utils/blacklist.py"""
    
    @pytest.fixture
    def temp_blacklist_dir(self):
        """Erstellt temporäres Verzeichnis für Blacklist-Dateien"""
        with tempfile.TemporaryDirectory() as tmpdir:
            yield tmpdir
    
    def test_blacklist_init(self, temp_blacklist_dir):
        """Test Initialisierung von Blacklist"""
        from utils.blacklist import Blacklist
        
        with patch('utils.blacklist.DATA_DIR', temp_blacklist_dir):
            blacklist = Blacklist()
            
            assert 'films' in blacklist.blacklists
            assert 'albums' in blacklist.blacklists
            assert 'books' in blacklist.blacklists
    
    def test_add_to_blacklist(self, temp_blacklist_dir):
        """Test Hinzufügen zur Blacklist"""
        from utils.blacklist import Blacklist
        
        with patch('utils.blacklist.DATA_DIR', temp_blacklist_dir):
            blacklist = Blacklist()
            item = {'title': 'Test Film', 'author': 'Test Director', 'type': 'DVD'}
            
            blacklist.add_to_blacklist('films', item, reason="Test")
            
            assert len(blacklist.blacklists['films']) == 1
            assert blacklist.blacklists['films'][0]['title'] == 'Test Film'
            assert blacklist.blacklists['films'][0]['reason'] == 'Test'
    
    def test_is_blacklisted(self, temp_blacklist_dir):
        """Test is_blacklisted Methode"""
        from utils.blacklist import Blacklist
        
        with patch('utils.blacklist.DATA_DIR', temp_blacklist_dir):
            blacklist = Blacklist()
            item = {'title': 'Test Film', 'author': 'Test Director', 'type': 'DVD'}
            
            # Initial nicht geblacklistet
            assert not blacklist.is_blacklisted('films', item)
            
            # Nach Hinzufügen sollte es erkannt werden
            blacklist.add_to_blacklist('films', item)
            assert blacklist.is_blacklisted('films', item)
    
    def test_is_blacklisted_case_insensitive(self, temp_blacklist_dir):
        """Test dass Blacklist case-insensitive ist"""
        from utils.blacklist import Blacklist
        
        with patch('utils.blacklist.DATA_DIR', temp_blacklist_dir):
            blacklist = Blacklist()
            item1 = {'title': 'Test Film', 'author': 'Test Director'}
            item2 = {'title': 'TEST FILM', 'author': 'TEST DIRECTOR'}
            
            blacklist.add_to_blacklist('films', item1)
            
            # Sollte auch mit anderem Case erkannt werden
            assert blacklist.is_blacklisted('films', item2)
    
    def test_remove_from_blacklist(self, temp_blacklist_dir):
        """Test Entfernen von Blacklist"""
        from utils.blacklist import Blacklist
        
        with patch('utils.blacklist.DATA_DIR', temp_blacklist_dir):
            blacklist = Blacklist()
            item = {'title': 'Test Film', 'author': 'Test Director', 'type': 'DVD'}
            
            blacklist.add_to_blacklist('films', item)
            assert blacklist.is_blacklisted('films', item)
            
            removed = blacklist.remove_from_blacklist('films', item)
            
            assert removed is True
            assert not blacklist.is_blacklisted('films', item)
    
    def test_clear_blacklist(self, temp_blacklist_dir):
        """Test clear_blacklist Methode"""
        from utils.blacklist import Blacklist
        
        with patch('utils.blacklist.DATA_DIR', temp_blacklist_dir):
            blacklist = Blacklist()
            
            # Füge Items hinzu
            blacklist.add_to_blacklist('films', {'title': 'Film 1', 'author': 'Director 1'})
            blacklist.add_to_blacklist('albums', {'title': 'Album 1', 'author': 'Artist 1'})
            
            # Lösche nur Filme
            blacklist.clear_blacklist('films')
            
            assert len(blacklist.blacklists['films']) == 0
            assert len(blacklist.blacklists['albums']) == 1
    
    def test_get_blacklist_stats(self, temp_blacklist_dir):
        """Test get_blacklist_stats Methode"""
        from utils.blacklist import Blacklist
        
        with patch('utils.blacklist.DATA_DIR', temp_blacklist_dir):
            blacklist = Blacklist()
            
            blacklist.add_to_blacklist('films', {'title': 'Film 1', 'author': 'Director 1'})
            blacklist.add_to_blacklist('films', {'title': 'Film 2', 'author': 'Director 2'})
            blacklist.add_to_blacklist('albums', {'title': 'Album 1', 'author': 'Artist 1'})
            
            stats = blacklist.get_blacklist_stats()
            
            assert stats['films']['count'] == 2
            assert stats['albums']['count'] == 1
            assert stats['books']['count'] == 0


# ============================================================================
# Pytest Configuration
# ============================================================================

if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
