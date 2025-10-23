#!/usr/bin/env python3
"""
Zustandsverwaltung für Medien-Empfehlungen
Speichert nur explizit abgelehnte Medien persistent
"""

import os
import json

from utils.io import DATA_DIR

STATE_FILE = os.path.join(DATA_DIR, "state.json")


class AppState:
    """
    Verwaltet den Zustand der Medien-Empfehlungen.

    Trennt zwischen:
    - suggested: Alle vorgeschlagenen Medien (nur im Arbeitsspeicher)
    - rejected: Explizit abgelehnte Medien (persistent gespeichert)
    """

    def __init__(self):
        # Struktur: { "films": [ {title:..., author:...}, ...], "albums": [...], "books": [...] }
        # Nur abgelehnte Medien, persistent gespeichert
        self.rejected = self.load_rejected_state()

        # Alle vorgeschlagenen Medien, nur im Arbeitsspeicher
        # Wird bei jedem App-Start zurückgesetzt
        self.suggested = {"films": [], "albums": [], "books": []}

    @staticmethod
    def load_rejected_state():
        """Lädt nur die abgelehnten Medien aus der JSON-Datei"""
        if os.path.exists(STATE_FILE):
            try:
                with open(STATE_FILE, "r", encoding="utf-8") as f:
                    rejected = json.load(f)
                print(f"DEBUG: {sum(len(items) for items in rejected.values())} abgelehnte Medien aus state.json geladen.")
                return rejected
            except (json.JSONDecodeError, KeyError) as e:
                print(f"DEBUG: Fehler beim Laden der state.json: {e}")
                print("DEBUG: Erstelle neue state.json")
                return {"films": [], "albums": [], "books": []}
        else:
            rejected = {"films": [], "albums": [], "books": []}
            AppState.save_rejected_state(rejected)
            print(f"DEBUG: Neue state.json erstellt.")
            return rejected

    @staticmethod
    def save_rejected_state(rejected):
        """Speichert nur die abgelehnten Medien in die JSON-Datei"""
        try:
            with open(STATE_FILE, "w", encoding="utf-8") as f:
                json.dump(rejected, f, ensure_ascii=False, indent=2)
            print(f"DEBUG: {sum(len(items) for items in rejected.values())} abgelehnte Medien in state.json gespeichert.")
        except Exception as e:
            print(f"DEBUG: Fehler beim Speichern der state.json: {e}")

    def is_already_suggested(self, category, item):
        """
        Prüft, ob ein Item schon vorgeschlagen wurde (im aktuellen Lauf)
        oder explizit abgelehnt wurde (persistent)
        """
        title_lower = item["title"].lower()

        # Prüfe ob schon in diesem Lauf vorgeschlagen
        already_suggested_this_run = any(x["title"].lower() == title_lower for x in self.suggested.get(category, []))

        # Prüfe ob explizit abgelehnt (persistent)
        already_rejected = any(x["title"].lower() == title_lower for x in self.rejected.get(category, []))

        if already_suggested_this_run:
            print(f"DEBUG: '{item['title']}' bereits in diesem Lauf vorgeschlagen")
        if already_rejected:
            print(f"DEBUG: '{item['title']}' wurde früher abgelehnt")

        return already_suggested_this_run or already_rejected

    def mark_suggested(self, category, item):
        """Markiert ein Item als vorgeschlagen (nur im Arbeitsspeicher)"""
        if category not in self.suggested:
            self.suggested[category] = []

        # Prüfe ob schon vorhanden
        title_lower = item["title"].lower()
        if not any(x["title"].lower() == title_lower for x in self.suggested[category]):
            self.suggested[category].append(item)
            print(f"DEBUG: '{item['title']}' als vorgeschlagen markiert")

    def reject(self, category, item):
        """
        Lehnt ein Item explizit ab - wird persistent gespeichert
        """
        if category not in self.rejected:
            self.rejected[category] = []

        title_lower = item["title"].lower()

        # Prüfe ob schon in abgelehnten Items
        if not any(x["title"].lower() == title_lower for x in self.rejected[category]):
            self.rejected[category].append(item)
            print(f"DEBUG: '{item['title']}' als abgelehnt markiert")

            # Speichere sofort persistent
            self.save_rejected_state(self.rejected)
        else:
            print(f"DEBUG: '{item['title']}' war bereits als abgelehnt markiert")

    def reset_rejected(self):
        """Setzt alle abgelehnten Medien zurück (löscht state.json)"""
        self.rejected = {"films": [], "albums": [], "books": []}
        self.save_rejected_state(self.rejected)
        print("DEBUG: Alle abgelehnten Medien zurückgesetzt")

    def reset_suggested(self):
        """Setzt nur die aktuell vorgeschlagenen zurück"""
        self.suggested = {"films": [], "albums": [], "books": []}
        print("DEBUG: Aktuell vorgeschlagene Medien zurückgesetzt")

    def get_stats(self):
        """Gibt Statistiken über den aktuellen Zustand zurück"""
        stats = {
            "rejected_total": sum(len(items) for items in self.rejected.values()),
            "suggested_total": sum(len(items) for items in self.suggested.values()),
            "rejected_by_category": {category: len(items) for category, items in self.rejected.items()},
            "suggested_by_category": {category: len(items) for category, items in self.suggested.items()},
        }
        return stats

    def print_stats(self):
        """Druckt Statistiken über den aktuellen Zustand"""
        stats = self.get_stats()
        print("\n" + "=" * 50)
        print("MEDIEN-ZUSTAND STATISTIKEN")
        print("=" * 50)
        print(f"Abgelehnte Medien (persistent): {stats['rejected_total']}")
        for category, count in stats["rejected_by_category"].items():
            if count > 0:
                print(f"  - {category.capitalize()}: {count}")

        print(f"Vorgeschlagene Medien (aktueller Lauf): {stats['suggested_total']}")
        for category, count in stats["suggested_by_category"].items():
            if count > 0:
                print(f"  - {category.capitalize()}: {count}")
        print("=" * 50 + "\n")

    def list_rejected_items(self, category=None):
        """
        Listet abgelehnte Items auf

        Args:
            category (str, optional): Spezifische Kategorie oder None für alle

        Returns:
            dict oder list: Abgelehnte Items
        """
        if category:
            return self.rejected.get(category, [])
        else:
            return self.rejected
