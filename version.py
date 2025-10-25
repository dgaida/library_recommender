#!/usr/bin/env python3
"""
Versionsinformationen für die Bibliothek-Empfehlungs-App
"""

__version__ = "2.0.0"
__author__ = "dgaida"
__license__ = "MIT"
__description__ = "Intelligente Empfehlungs-App für die Stadtbibliothek Köln"

# Release-Informationen
RELEASE_DATE = "2025-01-20"
RELEASE_NAME = "Personalized Recommendations"

# Feature-Flags
FEATURES = {
    "films": True,
    "albums": True,
    "books": True,
    "guides": True,
    "personalized_recommendations": True,
    "oscar_music": True,
    "google_search": True,
    "blacklist_system": True,
    "source_tracking": True,
}


def get_version_info():
    """Gibt vollständige Versionsinformationen zurück"""
    return {
        "version": __version__,
        "release_date": RELEASE_DATE,
        "release_name": RELEASE_NAME,
        "author": __author__,
        "license": __license__,
        "description": __description__,
        "features": FEATURES,
    }


def print_version_info():
    """Druckt Versionsinformationen auf der Konsole"""
    print(f"\n{'=' * 60}")
    print("  🎬📀📚 Bibliothek-Empfehlungs-App")
    print(f"{'=' * 60}")
    print(f"  Version:      {__version__}")
    print(f"  Release:      {RELEASE_NAME}")
    print(f"  Datum:        {RELEASE_DATE}")
    print(f"  Autor:        {__author__}")
    print(f"  Lizenz:       {__license__}")
    print(f"{'=' * 60}\n")


if __name__ == "__main__":
    print_version_info()
