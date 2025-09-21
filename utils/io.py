#!/usr/bin/env python3
"""
Stadtbibliothek Köln Katalog Suche
Programm zur Suche im Online-Katalog der Stadtbibliothek Köln
"""

import os
from datetime import datetime

DATA_DIR = "data"  # os.path.join(os.path.dirname(__file__), "data")
os.makedirs(DATA_DIR, exist_ok=True)


def save_results_to_markdown(all_results, filename="results.md"):
    """
    Speichert alle Suchergebnisse in einer Markdown-Datei.

    Args:
        all_results (dict): Dictionary mit Titel als Key und Ergebnisliste als Value
        filename (str): Name der Ausgabedatei
    """
    with open(filename, "a", encoding="utf-8") as f:
        f.write("# Suchergebnisse Stadtbibliothek Köln\n\n")

        for title, results in all_results.items():
            f.write(f"## {title}\n")
            if not results:
                f.write("_Keine Ergebnisse gefunden._\n\n")
                continue

            for i, result in enumerate(results, 1):
                f.write(f"### {i}. {result['title']}\n")
                if result.get("author"):
                    f.write(f"- **Autor:** {result['author']}\n")
                if result.get("year"):
                    f.write(f"- **Jahr:** {result['year']}\n")
                if result.get("material_type"):
                    f.write(f"- **Medientyp:** {result['material_type']}\n")
                if result.get("availability") and result["availability"] != "Unbekannt":
                    f.write(f"- **Status:** {result['availability']}\n")
                # if result.get("link"):
                #     f.write(f"- [Detailseite]({result['link']})\n")
                if result.get("zentralbibliothek_info"):
                    f.write(f"- **Zentralbibliothek:** {result['zentralbibliothek_info']}\n")

                f.write("\n")

            f.write("---\n\n")

    print(f"DEBUG: Ergebnisse in {filename} gespeichert.")


def save_recommendations_to_markdown(recommendations, filename="recommended.md"):
    """
    Speichert die aktuellen Empfehlungen aus der GUI in eine Markdown-Datei.

    Args:
        recommendations (dict): Dictionary mit Kategorien als Keys und Listen von Empfehlungen als Values
                               Format: {"films": [item1, item2, ...], "albums": [...], "books": [...]}
        filename (str): Name der Ausgabedatei
    """
    timestamp = datetime.now().strftime("%d.%m.%Y %H:%M:%S")

    with open(filename, "w", encoding="utf-8") as f:
        f.write("# 🎬📀📚 Empfehlungen der Stadtbibliothek Köln\n\n")
        f.write(f"**Erstellt am:** {timestamp}\n\n")
        f.write("---\n\n")

        # Kategorien mit Emojis und deutschen Namen
        categories = {
            "films": ("🎬 Filme", "Film", "Regie"),
            "albums": ("🎵 Musik/Alben", "Album", "Künstler"),
            "books": ("📚 Bücher", "Buch", "Autor")
        }

        total_items = sum(len(items) for items in recommendations.values())

        if total_items == 0:
            f.write("_Keine Empfehlungen vorhanden._\n\n")
            f.write("Klicken Sie in der App auf die entsprechenden Buttons, um neue Empfehlungen zu erhalten.\n")
            return

        # Übersicht
        f.write("## 📊 Übersicht\n\n")
        for category, items in recommendations.items():
            if items:
                category_name, _, _ = categories.get(category, (category.title(), "Item", "Autor"))
                f.write(f"- **{category_name}:** {len(items)} Empfehlungen\n")
        f.write(f"\n**Gesamt:** {total_items} Empfehlungen\n\n")
        f.write("---\n\n")

        # Detaillierte Empfehlungen pro Kategorie
        for category, items in recommendations.items():
            if not items:
                continue

            category_name, item_type, author_label = categories.get(category, (category.title(), "Item", "Autor"))
            f.write(f"## {category_name}\n\n")

            for i, item in enumerate(items, 1):
                f.write(f"### {i}. {item['title']}\n")

                if item.get('author'):
                    f.write(f"- **{author_label}:** {item['author']}\n")

                if item.get('bib_number'):
                    f.write(f"- **Verfügbarkeit:** {item['bib_number']}\n")

                # Zusätzliche Informationen falls vorhanden
                if item.get('year'):
                    f.write(f"- **Jahr:** {item['year']}\n")

                if item.get('genre'):
                    f.write(f"- **Genre:** {item['genre']}\n")

                f.write("\n")

            f.write("---\n\n")

        # Fußzeile
        f.write("## ℹ️ Hinweise\n\n")
        f.write(
            "- Die Verfügbarkeit kann sich schnell ändern. Bitte prüfen Sie die aktuelle Verfügbarkeit direkt im Katalog.\n")
        f.write("- Diese Empfehlungen basieren auf kuratierten Listen hochwertiger Medien.\n")
        f.write("- Weitere Informationen finden Sie auf der Website der Stadtbibliothek Köln.\n\n")
        f.write("**🌐 Katalog:** https://katalog.stbib-koeln.de\n\n")
        f.write(f"_Generiert durch die Bibliothek-Empfehlungs-App am {timestamp}_\n")

    print(f"DEBUG: Empfehlungen in {filename} gespeichert.")
    return filename
