#!/usr/bin/env python3
"""
I/O-Utilities mit Type Hints und Logging
"""

import os
import re
from datetime import datetime
from typing import Dict, List, Any, Tuple
from collections import defaultdict
from fpdf.enums import XPos, YPos
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


def save_results_to_markdown(all_results: Dict[str, List[Dict[str, Any]]], filename: str = "results.md") -> None:  # noqa: C901
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


def _add_pdf_item(pdf, i, item, author_label, text_width):
    """Hilfsfunktion zum Hinzufügen eines Items zum PDF."""
    from utils.text_utils import remove_emoji

    y_before = pdf.get_y()
    clean_title = remove_emoji(item["title"])
    pdf.set_font("Helvetica", "B", 12)
    title_text = f"{i}. {clean_title}"
    pdf.multi_cell(
        text_width, 8, title_text.encode("latin-1", "replace").decode("latin-1"), new_x=XPos.LMARGIN, new_y=YPos.NEXT
    )

    pdf.set_font("Helvetica", "", 10)
    # Einrücken für Details
    pdf.set_x(15)
    detail_width = text_width - 5

    if item.get("author"):
        author_text = f"{author_label}: {item['author']}"
        pdf.multi_cell(
            detail_width,
            6,
            author_text.encode("latin-1", "replace").decode("latin-1"),
            new_x=XPos.LMARGIN,
            new_y=YPos.NEXT,
        )
        pdf.set_x(15)

    # Zusätzliche Infos (Jahr, Genre) wie im Markdown
    if item.get("year"):
        pdf.cell(
            detail_width,
            6,
            f"Jahr: {item['year']}".encode("latin-1", "replace").decode("latin-1"),
            new_x=XPos.LMARGIN,
            new_y=YPos.NEXT,
        )
        pdf.set_x(15)

    if item.get("genre"):
        pdf.cell(
            detail_width,
            6,
            f"Genre: {item['genre']}".encode("latin-1", "replace").decode("latin-1"),
            new_x=XPos.LMARGIN,
            new_y=YPos.NEXT,
        )
        pdf.set_x(15)

    if item.get("bib_number"):
        availability = truncate_text(item["bib_number"], 300)
        availability_text = f"Verfügbarkeit: {availability}"
        pdf.multi_cell(
            detail_width,
            6,
            availability_text.encode("latin-1", "replace").decode("latin-1"),
            new_x=XPos.LMARGIN,
            new_y=YPos.NEXT,
        )

    return y_before


def _add_album_cover(pdf, item, y_before):
    """Versucht ein Album-Cover in das PDF einzufügen oder zeigt einen Platzhalter."""
    import requests
    from io import BytesIO

    # Position für das Cover (rechts vom Text)
    x_pos = 160
    w_size = 35

    if item.get("cover_url"):
        try:
            response = requests.get(item["cover_url"], timeout=5)
            if response.status_code == 200:
                img_data = BytesIO(response.content)
                # Kleines Cover (35x35 mm) rechts vom Text
                pdf.image(img_data, x=x_pos, y=y_before, w=w_size)
                return
        except Exception as e:
            logger.warning(f"Konnte Cover für {item['title']} nicht laden: {e}")

    # Platzhalter zeichnen, falls kein Cover vorhanden oder Laden fehlgeschlagen
    pdf.set_draw_color(200, 200, 200)
    pdf.rect(x_pos, y_before, w_size, w_size)
    pdf.set_font("Helvetica", "I", 8)
    pdf.set_xy(x_pos, y_before + 15)
    pdf.cell(w_size, 5, "Kein Cover", align="C")
    # Cursor zurücksetzen für nachfolgende Items
    pdf.set_font("Helvetica", "", 10)


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


def save_recommendations_to_pdf(recommendations: Dict[str, List[Dict[str, Any]]], filename: str = "recommended.pdf") -> str:
    """
    Speichert die aktuellen Empfehlungen in einer PDF-Datei mit Album-Covern.

    Args:
        recommendations: Dictionary mit Kategorien als Keys und Listen von Empfehlungen
        filename: Name der Ausgabedatei

    Returns:
        Dateiname der gespeicherten Datei
    """
    from fpdf import FPDF

    timestamp: str = datetime.now().strftime("%d.%m.%Y %H:%M:%S")
    logger.info(f"Speichere Empfehlungen in '{filename}'")

    pdf = FPDF()
    pdf.set_auto_page_break(auto=True, margin=15)
    pdf.add_page()

    # Titel
    pdf.set_font("Helvetica", "B", 16)
    pdf.cell(
        0,
        10,
        "Empfehlungen der Stadtbibliothek Köln",
        new_x=XPos.LMARGIN,
        new_y=YPos.NEXT,
        align="C",
    )
    pdf.set_font("Helvetica", "I", 10)
    pdf.cell(
        0,
        10,
        f"Erstellt am: {timestamp}",
        new_x=XPos.LMARGIN,
        new_y=YPos.NEXT,
        align="C",
    )
    pdf.ln(10)

    categories: Dict[str, Tuple[str, str, str]] = {
        "films": ("Filme", "Film", "Regie"),
        "albums": ("Musik/Alben", "Album", "Künstler"),
        "books": ("Bücher", "Buch", "Autor"),
    }

    for category, items in recommendations.items():
        if not items:
            continue

        category_name, _, author_label = categories.get(category, (category.title(), "Item", "Autor"))

        pdf.set_font("Helvetica", "B", 14)
        pdf.cell(
            0,
            10,
            category_name.encode("latin-1", "replace").decode("latin-1"),
            new_x=XPos.LMARGIN,
            new_y=YPos.NEXT,
        )
        pdf.ln(2)

        items_to_write = _sort_films_by_genre(items) if category == "films" else items

        for i, item in enumerate(items_to_write, 1):
            # Vorab-Check für Seitenumbruch
            needed_height = 45 if category == "albums" else 25
            if pdf.get_y() + needed_height > 270:
                pdf.add_page()

            text_width = 140 if category == "albums" else pdf.epw
            y_before = _add_pdf_item(pdf, i, item, author_label, text_width)

            if category == "albums":
                _add_album_cover(pdf, item, y_before)
                # Stelle sicher, dass wir unter dem Bild weitermachen
                pdf.set_y(max(pdf.get_y(), y_before + 40))
            else:
                pdf.ln(2)

        pdf.ln(5)
        pdf.line(10, pdf.get_y(), 200, pdf.get_y())
        pdf.ln(5)

    # Hinweise
    pdf.add_page()
    pdf.set_font("Helvetica", "B", 12)
    pdf.cell(0, 10, "Hinweise", new_x=XPos.LMARGIN, new_y=YPos.NEXT)
    pdf.set_font("Helvetica", "", 10)
    pdf.multi_cell(
        0,
        6,
        "Die Verfügbarkeit kann sich schnell ändern. Bitte prüfen Sie die aktuelle Verfügbarkeit direkt im Katalog.\n"
        "Diese Empfehlungen basieren auf kuratierten Listen hochwertiger Medien.\n"
        "Katalog: https://katalog.stbib-koeln.de",
        new_x=XPos.LMARGIN,
        new_y=YPos.NEXT,
    )

    pdf.output(filename)
    return filename
