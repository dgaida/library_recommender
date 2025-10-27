#!/usr/bin/env python3
"""
Haupteinstiegspunkt für die Bibliothek-Empfehlungs-App
"""

import sys
from typing import NoReturn
from dotenv import load_dotenv
from utils.logging_config import setup_logging, get_logger
from utils.borrowed_blacklist import initialize_borrowed_blacklist
from gui import launch_app

# Lade Umgebungsvariablen
load_dotenv(dotenv_path="secrets.env")

# Initialisiere Logging
setup_logging()
logger = get_logger(__name__)


def check_dependencies() -> None:
    """
    Prüft ob alle erforderlichen Abhängigkeiten installiert sind.

    Raises:
        SystemExit: Wenn wichtige Abhängigkeiten fehlen
    """
    logger.info("Prüfe Abhängigkeiten...")

    try:
        import requests  # noqa: F401
        import bs4  # noqa: F401
        import gradio  # noqa: F401

        logger.info("✅ Alle Basis-Abhängigkeiten verfügbar")
    except ImportError as e:
        logger.error(f"❌ Fehlende Abhängigkeit: {e}")
        print("\nFehlende Abhängigkeiten. Bitte installieren Sie diese mit:")
        print("pip install -r requirements.txt")
        sys.exit(1)


def main() -> NoReturn:
    """
    Hauptfunktion - Startet die Gradio-App.

    Diese Funktion wird beim direkten Ausführen der Datei aufgerufen.
    """
    logger.info("=" * 60)
    logger.info("🎬📀📚 Bibliothek-Empfehlungs-App startet...")
    logger.info("=" * 60)

    # Abhängigkeiten prüfen
    check_dependencies()

    try:
        # NEU: Initialisiere Entleih-Blacklist beim Start
        logger.info("Initialisiere Entleih-Blacklist...")
        initialize_borrowed_blacklist()

        # Gradio-App starten
        logger.info("Starte Gradio-Webinterface...")
        launch_app(share=False, inbrowser=True)

    except KeyboardInterrupt:
        logger.info("\n\n⚠️  App durch Benutzer beendet (Ctrl+C)")
        sys.exit(0)

    except Exception as e:
        logger.error(f"❌ Kritischer Fehler beim Start der App: {e}", exc_info=True)
        print(f"\n❌ Fehler: {e}")
        print("\nBitte prüfen Sie die Log-Datei für Details.")
        sys.exit(1)


if __name__ == "__main__":
    main()
