#!/usr/bin/env python3
"""
I/O-Utilities mit Type Hints und Logging
"""

import os
import re
from datetime import datetime
from typing import Dict, List, Any, Tuple
from collections import defaultdict
from utils.logging_config import get_logger

logger = get_logger(__name__)

DATA_DIR: str = "data"
os.makedirs(DATA_DIR, exist_ok=True)


def extract_genres_from_availability(availability: str) -> List[str]:
    """
    Extrahiert Genres aus der Verfügbarkeitsangabe.

    Args:
        availability: Verfügbarkeitstext aus Bibliothek

    Returns:
        Liste der gefundenen Genres
    """
    if not availability:
        return []

    # Pattern für *Genre*
    pattern = r"\*([^*]+)\*"
    matches = re.findall(pattern, availability)

    genres = [match.strip() for match in matches if match.strip()]
    return genres


def truncate_text(text: str, max_length: int = 300) -> str:
    """
    Kürzt Text auf maximale Länge.

    Args:
        text: Zu kürzender Text
        max_length: Maximale Länge (default: 300)

    Returns:
        Gekürzter Text mit "..." falls nötig
    """
    if not text or len(text) <= max_length:
        return text

    return text[: max_length - 3].strip() + "..."


def save_results_to_markdown(all_results: Dict[str, List[Dict[str, Any]]], filename: str = "results.md") -> None:
    """
    Speichert alle Suchergebnisse in einer Markdown-Datei.

    Args:
        all_results: Dictionary mit Titel als Key und Ergebnisliste als Value
        filename: Name der Ausgabedatei
    """
    logger.info(f"Speichere Ergebnisse in '{filename}'")

    try:
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
                    if result.get("zentralbibliothek_info"):
                        f.write(f"- **Zentralbibliothek:** {result['zentralbibliothek_info']}\n")

                    f.write("\n")

                f.write("---\n\n")

        logger.info(f"Ergebnisse erfolgreich in '{filename}' gespeichert")
    except IOError as e:
        logger.error(f"Fehler beim Speichern in '{filename}': {e}")


def save_recommendations_to_markdown(
    recommendations: Dict[str, List[Dict[str, Any]]], filename: str = "recommended.md"
) -> str:
    """
    Speichert die aktuellen Empfehlungen aus der GUI in eine Markdown-Datei.

    Features:
    - Verfügbarkeit wird auf 300 Zeichen begrenzt
    - Filme werden nach Genre sortiert

    Args:
        recommendations: Dictionary mit Kategorien als Keys und Listen von Empfehlungen
        filename: Name der Ausgabedatei

    Returns:
        Dateiname der gespeicherten Datei

    Raises:
        IOError: Bei Schreibproblemen
    """
    timestamp: str = datetime.now().strftime("%d.%m.%Y %H:%M:%S")

    logger.info(f"Speichere Empfehlungen in '{filename}'")

    # Kategorien mit Emojis und deutschen Namen
    categories: Dict[str, Tuple[str, str, str]] = {
        "films": ("🎬 Filme", "Film", "Regie"),
        "albums": ("🎵 Musik/Alben", "Album", "Künstler"),
        "books": ("📚 Bücher", "Buch", "Autor"),
    }

    total_items: int = sum(len(items) for items in recommendations.values())

    try:
        with open(filename, "w", encoding="utf-8") as f:
            f.write("# 🎬📀📚 Empfehlungen der Stadtbibliothek Köln\n\n")
            f.write(f"**Erstellt am:** {timestamp}\n\n")
            f.write("---\n\n")

            if total_items == 0:
                f.write("_Keine Empfehlungen vorhanden._\n\n")
                f.write("Klicken Sie in der App auf die entsprechenden Buttons, " "um neue Empfehlungen zu erhalten.\n")
                logger.warning("Keine Empfehlungen zum Speichern vorhanden")
                return filename

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

                # Spezielle Behandlung für Filme: Nach Genre sortieren
                if category == "films":
                    items_to_write = _sort_films_by_genre(items)
                else:
                    items_to_write = items

                for i, item in enumerate(items_to_write, 1):
                    f.write(f"### {i}. {item['title']}\n")

                    if item.get("author"):
                        f.write(f"- **{author_label}:** {item['author']}\n")

                    if item.get("bib_number"):
                        # Kürze Verfügbarkeit auf 300 Zeichen
                        availability = truncate_text(item["bib_number"], 300)
                        f.write(f"- **Verfügbarkeit:** {availability}\n")

                    # Zusätzliche Informationen falls vorhanden
                    if item.get("year"):
                        f.write(f"- **Jahr:** {item['year']}\n")

                    if item.get("genre"):
                        f.write(f"- **Genre:** {item['genre']}\n")

                    f.write("\n")

                f.write("---\n\n")

            # Fußzeile
            f.write("## ℹ️ Hinweise\n\n")
            f.write(
                "- Die Verfügbarkeit kann sich schnell ändern. "
                "Bitte prüfen Sie die aktuelle Verfügbarkeit direkt im Katalog.\n"
            )
            f.write("- Diese Empfehlungen basieren auf kuratierten Listen " "hochwertiger Medien.\n")
            f.write("- Weitere Informationen finden Sie auf der Website der " "Stadtbibliothek Köln.\n\n")
            f.write("**🌐 Katalog:** https://katalog.stbib-koeln.de\n\n")
            f.write(f"_Generiert durch die Bibliothek-Empfehlungs-App am {timestamp}_\n")

        logger.info(f"Empfehlungen erfolgreich gespeichert: " f"{total_items} Items in '{filename}'")
    except IOError as e:
        logger.error(f"Fehler beim Speichern der Empfehlungen: {e}")
        raise

    return filename


def _sort_films_by_genre(films: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Sortiert Filme nach Genre.

    Gruppiert Filme nach Genre und sortiert innerhalb der Genres
    alphabetisch nach Titel.

    Args:
        films: Liste von Filmen

    Returns:
        Nach Genre sortierte Liste von Filmen
    """
    logger.info(f"Sortiere {len(films)} Filme nach Genre")

    # Gruppiere nach Genre
    films_by_genre: Dict[str, List[Dict[str, Any]]] = defaultdict(list)

    for film in films:
        # Extrahiere Genres aus Verfügbarkeit
        availability = film.get("bib_number", "")
        genres = extract_genres_from_availability(availability)

        if genres:
            # Verwende erstes Genre für Sortierung
            primary_genre = genres[0]
            films_by_genre[primary_genre].append(film)
            logger.debug(f"Film '{film['title']}' -> Genre: {primary_genre}")
        else:
            # Filme ohne Genre in "Sonstige"
            films_by_genre["Sonstige"].append(film)
            logger.debug(f"Film '{film['title']}' -> Genre: Sonstige")

    # Sortiere Genres alphabetisch und innerhalb nach Titel
    sorted_films: List[Dict[str, Any]] = []

    for genre in sorted(films_by_genre.keys()):
        # Sortiere Filme innerhalb Genre alphabetisch
        genre_films = sorted(films_by_genre[genre], key=lambda x: x["title"].lower())
        sorted_films.extend(genre_films)
        logger.debug(f"Genre '{genre}': {len(genre_films)} Filme")

    logger.info(f"Filme sortiert in {len(films_by_genre)} Genres")

    return sorted_films
