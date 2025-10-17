"""
Recommender-Package für das Bibliothek-Recommender-System.

Dieses Package enthält:
- Die zentrale Empfehlungslogik (`Recommender`)
- Die Zustandsverwaltung für vorgeschlagene und abgelehnte Medien (`AppState`)
"""

from .recommender import Recommender
from .state import AppState

__all__ = ["Recommender", "AppState"]
