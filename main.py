#!/usr/bin/env python3
"""
Stadtbibliothek Köln Katalog Suche
Programm zur Suche im Online-Katalog der Stadtbibliothek Köln
"""

from dotenv import load_dotenv
import time
import sys
from library.search import KoelnLibrarySearch
from gui.app import demo

load_dotenv(dotenv_path="secrets.env")


# wird nicht mehr genutzt
def main():
    """Hauptfunktion für die interaktive Nutzung"""
    search_engine = KoelnLibrarySearch()

    print("Stadtbibliothek Köln - Katalogsuche")
    print("=" * 40)

    while True:
        try:
            search_term = input("\nGeben Sie einen Suchbegriff ein (oder 'quit' zum Beenden): ").strip()

            if search_term.lower() in ['quit', 'exit', 'q']:
                print("Auf Wiedersehen!")
                break

            if not search_term:
                print("Bitte geben Sie einen Suchbegriff ein.")
                continue

            # Suchtyp auswählen
            print("\nSuchtyp auswählen:")
            print("1. Alle Felder (Standard)")
            print("2. Titel")
            print("3. Autor")
            print("4. Schlagwort")

            choice = input("Ihre Wahl (1-4, Enter für Standard): ").strip()

            search_types = {
                '1': 'all',
                '2': 'title',
                '3': 'author',
                '4': 'subject',
                '': 'all'
            }

            search_type = search_types.get(choice, 'all')

            # Suche durchführen
            results = search_engine.search(search_term, search_type)

            # Ergebnisse anzeigen
            search_engine.display_results(results)

            # Kurze Pause um Server nicht zu überlasten
            time.sleep(1)

        except KeyboardInterrupt:
            print("\n\nProgramm beendet.")
            break
        except Exception as e:
            print(f"Ein Fehler ist aufgetreten: {e}")


if __name__ == "__main__":
    # Abhängigkeiten prüfen
    try:
        import requests
        import bs4
    except ImportError as e:
        print("Fehlende Abhängigkeiten. Bitte installieren Sie diese mit:")
        print("pip install requests beautifulsoup4")
        sys.exit(1)

    # Gradio-App starten
    demo.launch()
