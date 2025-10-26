import gradio as gr
import os
import json
import re
from typing import List, Dict, Any, Tuple, Optional
from library.search import KoelnLibrarySearch
from recommender.recommender import Recommender
from recommender.state import AppState
from data_sources.films import fetch_wikipedia_titles
from data_sources.fbw_films import fetch_fbw_films, fetch_oscar_best_picture_winners
from data_sources.oscar_music import add_oscar_music_to_albums

from utils.sources import (
    format_source_for_display,
    SOURCE_RADIO_EINS_TOP_100,
    get_source_emoji,
    SOURCE_NYT_CANON,
    SOURCE_BEST_GUIDES,
)
from data_sources.mp3_analysis import add_top_artist_albums_to_collection

from data_sources.albums import fetch_radioeins_albums
from data_sources.books import fetch_books_from_site
from data_sources.guides import fetch_guides_from_site
from preprocessing.filters import filter_existing_albums
from utils.search_utils import get_media_summary, extract_title_and_author
from utils.logging_config import get_logger

from utils.io import DATA_DIR, save_recommendations_to_markdown

logger = get_logger(__name__)

FILMS_FILE = os.path.join(DATA_DIR, "films.json")
ALBUMS_FILE = os.path.join(DATA_DIR, "albums.json")
BOOKS_FILE = os.path.join(DATA_DIR, "books.json")


def load_or_fetch_books() -> List[Dict[str, Any]]:
    """
    Lädt Bücher aus dem lokalen Cache oder ruft sie von der Quelle ab.

    Falls bereits eine `books.json` im `DATA_DIR` existiert, wird diese Datei geladen.
    Andernfalls werden die Daten mit `fetch_books_from_site()` (Bücher) und
    `fetch_guides_from_site()` (Ratgeber) von den angegebenen Webseiten abgerufen,
    aufbereitet und anschließend als JSON gespeichert.

    Returns:
        Liste von Büchern und Ratgebern mit Schlüsseln:
            - "title" (str): Titel
            - "author" (str): Autor/Autorin
            - "type" (str): "Buch" oder "Ratgeber"
            - "description" (str): Beschreibung
    """
    if os.path.exists(BOOKS_FILE):
        with open(BOOKS_FILE, "r", encoding="utf-8") as f:
            books = json.load(f)
        logger.info(f"{len(books)} Bücher aus Cache geladen.")
    else:
        # Bücher (New York Times Kanon)
        books_data = fetch_books_from_site()

        # Ratgeber (21. Jahrhundert)
        guides_data = fetch_guides_from_site()

        books = []

        # Normale Bücher
        for t in books_data:
            books.append(
                {
                    "title": t["title"],
                    "author": t["author"],
                    "type": "Buch",
                    "description": t["description"],
                    "source": t.get("source", SOURCE_NYT_CANON),
                }
            )

        # Ratgeber hinzufügen
        for g in guides_data:
            books.append(
                {
                    "title": g["title"],
                    "author": g["author"],
                    "type": "Buch",
                    "description": g["description"],
                    "source": t.get("source", SOURCE_BEST_GUIDES),
                }
            )

        with open(BOOKS_FILE, "w", encoding="utf-8") as f:
            json.dump(books, f, ensure_ascii=False, indent=2)

        logger.info(f"{len(books)} Bücher & Ratgeber geladen und gespeichert.")

    return books


def load_or_fetch_films() -> List[Dict[str, Any]]:
    """
    Lädt Filme aus dem lokalen Cache oder von externen Quellen.

    Falls bereits eine `films.json` existiert, wird diese Datei geladen.
    Andernfalls werden die Daten kombiniert aus:
      - `fetch_wikipedia_titles()` (Wikipedia-Liste)
      - `fetch_fbw_films()` (FBW-Filmbewertungsstelle)
      - `fetch_oscar_best_picture_winners()` (Oscar-Gewinner)
    Duplikate werden anhand des Titels entfernt, alphabetisch sortiert
    und anschließend in `films.json` gespeichert.

    Returns:
        Liste von Filmen mit Schlüsseln:
            - "title" (str): Titel des Films
            - "author" (str): Regisseur/in
            - "type" (str): Immer "DVD"
            - "description" (str, optional): Kurzbeschreibung
            - "source" (str): Herkunftsquelle
    """
    if os.path.exists(FILMS_FILE):
        with open(FILMS_FILE, "r", encoding="utf-8") as f:
            films = json.load(f)
        logger.info(f"{len(films)} Filme aus Cache geladen.")
    else:
        # Wikipedia-Filme laden
        wiki_films = [
            {"title": t["title"], "author": t.get("regie", ""), "type": "DVD", "source": t.get("source", "")}
            for t in fetch_wikipedia_titles()
        ]
        logger.info(f"{len(wiki_films)} Filme von Wikipedia geladen.")

        # FBW-Filme laden
        fbw_films = fetch_fbw_films(max_pages=750)
        logger.info(f"{len(fbw_films)} Filme von FBW geladen.")

        # Oscar-Filme laden
        oscar_films = fetch_oscar_best_picture_winners()
        logger.info(f"{len(oscar_films)} Oscar-Filme geladen.")

        combined = wiki_films + fbw_films + oscar_films

        # Kombinieren und Duplikate anhand des Titels entfernen
        unique_films = {}
        for f in combined:
            title = f["title"].strip()
            unique_films[title.lower()] = f

        # Alphabetisch nach Titel sortieren
        sorted_films = sorted(unique_films.values(), key=lambda x: x["title"].lower())

        with open(FILMS_FILE, "w", encoding="utf-8") as f:
            json.dump(sorted_films, f, ensure_ascii=False, indent=2)

        logger.info(f"{len(sorted_films)} Filme kombiniert, bereinigt und gespeichert.")
        films = sorted_films

    return films


def load_or_fetch_albums() -> List[Dict[str, Any]]:
    """
    Lädt Musikalben aus dem lokalen Cache oder von verschiedenen Quellen.

    Falls bereits eine `albums.json` existiert, wird diese Datei geladen.
    Ansonsten werden die Daten kombiniert aus:
      - `fetch_radioeins_albums()` (Radio Eins Top 100)
      - `add_oscar_music_to_albums()` (Oscar-Gewinner Filmmusik)
      - `add_top_artist_albums_to_collection()` (Personalisierte Top-Interpreten)
    Danach werden Alben mit `filter_existing_albums` herausgefiltert, die bereits im
    lokalen Musikarchiv vorhanden sind.

    Returns:
        Liste von Alben mit Schlüsseln:
            - "title" (str): Titel des Albums
            - "author" (str): Künstler/in oder Band/Komponist
            - "type" (str): Immer "CD"
            - "source" (str): Herkunftsquelle
    """
    if os.path.exists(ALBUMS_FILE):
        with open(ALBUMS_FILE, "r", encoding="utf-8") as f:
            albums = json.load(f)
        logger.info(f"{len(albums)} Alben aus Cache geladen.")
    else:
        # Radio Eins Alben laden
        albums = [
            {"title": a[1], "author": a[0], "type": "CD", "source": SOURCE_RADIO_EINS_TOP_100}
            for a in fetch_radioeins_albums()
        ]
        with open(ALBUMS_FILE, "w", encoding="utf-8") as f:
            json.dump(albums, f, ensure_ascii=False, indent=2)
        logger.info(f"{len(albums)} Alben von Radioeins geladen und gespeichert.")

        # Oscar-Filmmusik hinzufügen
        logger.info("Füge Oscar-Filmmusik hinzu...")
        add_oscar_music_to_albums()

        # Top-Interpreten-Alben hinzufügen
        logger.info("Analysiere MP3-Archiv für personalisierte Empfehlungen...")
        add_top_artist_albums_to_collection("H:\\MP3 Archiv", top_n=10)

        # Neu laden nach Updates
        with open(ALBUMS_FILE, "r", encoding="utf-8") as f:
            albums = json.load(f)
        logger.info(f"{len(albums)} Alben nach allen Updates geladen.")

    albums = filter_existing_albums(albums, "H:\\MP3 Archiv")

    return albums


def suggest(category: str) -> Tuple[gr.update, str, gr.update, str]:
    """
    Erstellt neue balancierte Vorschläge für eine Kategorie.

    Generiert 12 Vorschläge mit 4 Items pro Datenquelle für ausgewogene
    Empfehlungen aus allen verfügbaren Quellen.

    Args:
        category: Kategorie ('films', 'albums', 'books')

    Returns:
        Tuple mit (checkbox_update, info_text, button_state, detail_text)
    """
    # 12 Vorschläge mit je 4 pro Quelle
    suggestions = get_n_suggestions(category, n=12, items_per_source=4)

    # Aktualisiere globale Vorschläge
    current_suggestions[category] = suggestions

    if not suggestions:
        return gr.update(choices=[], value=[]), "Keine Vorschläge gefunden.", gr.update(interactive=False), ""

    # Erstelle Auswahloptionen für die CheckboxGroup
    choices = []
    for s in suggestions:
        display_text = f"{s['title']}"
        if s.get("author"):
            display_text += f" - {s['author']}"
        # Emoji hinzufügen
        if s.get("source"):
            emoji = get_source_emoji(s["source"])
            if emoji:
                display_text = f"{emoji} {display_text}"
        choices.append(display_text)

    info_text = (
        f"{len(suggestions)} Vorschläge gefunden (balanciert aus allen Quellen). Wählen Sie Titel aus, um sie zu entfernen."
    )

    return gr.update(choices=choices, value=[]), info_text, gr.update(interactive=False), ""


def get_n_suggestions(category: str, n: int = 12, items_per_source: int = 4) -> List[Dict[str, Any]]:
    """
    Holt n neue Vorschläge für eine Kategorie, balanciert nach Quelle.

    Args:
        category: Kategorie ('films', 'albums', 'books')
        n: Gesamtanzahl gewünschter Vorschläge (default: 12)
        items_per_source: Items pro Quelle (default: 4)

    Returns:
        Liste von Empfehlungen, balanciert nach Quelle
    """
    if category == "films":
        suggestions = recommender.suggest_films(films, n=n, items_per_source=items_per_source)
    elif category == "albums":
        suggestions = recommender.suggest_albums(albums, n=n, items_per_source=items_per_source)
    elif category == "books":
        suggestions = recommender.suggest_books(books, n=n, items_per_source=items_per_source)
    else:
        suggestions = []

    return suggestions if suggestions else []


def remove_emoji(text: str) -> str:
    """
    Entfernt Emojis am Anfang eines Strings.

    Verwendet einen Unicode-Regex-Pattern, um gängige Emoji-Bereiche
    zu identifizieren und zu entfernen.

    Args:
        text: String möglicherweise mit Emoji

    Returns:
        String ohne Emoji

    Example:
        >>> remove_emoji("🎬 Der Pate")
        'Der Pate'
    """
    emoji_pattern = re.compile(
        "["
        "\U0001f300-\U0001f9ff"
        "\U0001f600-\U0001f64f"
        "\U0001f680-\U0001f6ff"
        "\U0001f1e0-\U0001f1ff"
        "\U00002702-\U000027b0"
        "\U000024c2-\U0001f251"
        "]+",
        flags=re.UNICODE,
    )
    return emoji_pattern.sub("", text).strip()


def on_selection_change(selected_items: List[str], category: str) -> Tuple[gr.update, str, gr.update]:
    """
    Wird aufgerufen, wenn Items in der Liste ausgewählt werden.

    Aktualisiert die Detailansicht und aktiviert/deaktiviert Buttons
    basierend auf der Auswahl.

    Args:
        selected_items: Liste ausgewählter Display-Strings
        category: Kategorie ('films', 'albums', 'books')

    Returns:
        Tuple mit (remove_button_state, detail_text, google_button_state)
    """
    if not selected_items:
        return gr.update(interactive=False), "", gr.update(interactive=False)

    count = len(selected_items)
    detail_text = f"{count} Element(e) ausgewählt:\n\n"

    # Finde die entsprechenden Vorschläge
    suggestions = current_suggestions.get(category, [])

    for selected_item in selected_items:
        selected_item_clean = remove_emoji(selected_item)

        for s in suggestions:
            display_text = f"{s['title']}"
            if s.get("author"):
                display_text += f" - {s['author']}"

            if display_text == selected_item_clean:
                detail_text += f"• {s['title']}"
                if s.get("author"):
                    detail_text += f"\n  Autor/Künstler: {s['author']}"
                if s.get("bib_number"):
                    detail_text += f"\n  Verfügbarkeit: {s['bib_number']}"
                if s.get("source"):
                    source_formatted = format_source_for_display(s["source"])
                    detail_text += f"\n  Quelle: {source_formatted}"
                detail_text += "\n\n"
                break

    google_btn_interactive = len(selected_items) == 1

    return gr.update(interactive=True), detail_text.strip(), gr.update(interactive=google_btn_interactive)


def create_media_html(youtube_id: Optional[str], cover_url: Optional[str], media_type: str, title: str) -> str:
    """
    Erstellt HTML für die visuelle Darstellung von Medien.

    Args:
        youtube_id: YouTube Video-ID (für Filme)
        cover_url: URL des Cover-Images
        media_type: Art des Mediums ('film', 'album', 'book')
        title: Titel für Alt-Text

    Returns:
        HTML-String mit eingebettetem Video und/oder Cover-Image
    """
    if not youtube_id and not cover_url:
        return ""

    html_parts = [
        '<div style="margin-top: 20px; text-align: center; background: #f9f9f9; padding: 20px; border-radius: 10px;">'
    ]

    # YouTube-Video einbetten (nur für Filme)
    if youtube_id and media_type == "film":
        html_parts.append(
            f"""
            <div style="margin-bottom: 20px;">
                <h4 style="margin-bottom: 10px; color: #333;">🎬 Trailer</h4>
                <iframe
                    width="800"
                    height="460"
                    src="https://www.youtube.com/embed/{youtube_id}"
                    title="YouTube video player"
                    frameborder="0"
                    allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture; web-share"
                    allowfullscreen
                    style="max-width: 100%; border-radius: 8px; box-shadow: 0 4px 6px rgba(0,0,0,0.1);">
                </iframe>
            </div>
        """
        )

    # Cover-Image anzeigen
    if cover_url:
        if media_type == "film":
            label = "📀 DVD-Cover"
        elif media_type == "album":
            label = "🎵 Album-Cover"
        elif media_type == "book":
            label = "📚 Buch-Cover"
        else:
            label = "🖼️ Cover"

        html_parts.append(
            f"""
            <div style="margin-bottom: 20px;">
                <h4 style="margin-bottom: 10px; color: #333;">{label}</h4>
                <img
                    src="{cover_url}"
                    alt="{title} Cover"
                    style="max-width: 300px; max-height: 450px; border-radius: 8px; box-shadow: 0 4px 6px rgba(0,0,0,0.1);"
                    onerror="this.style.display='none'; this.nextElementSibling.style.display='block';"
                />
                <p style="display: none; color: #666; font-style: italic; margin-top: 10px;">
                    Cover konnte nicht geladen werden
                </p>
            </div>
        """
        )

    html_parts.append("</div>")

    return "".join(html_parts)


def google_search_selected(selected_items: List[str], category: str) -> Tuple[str, str]:
    """
    Googelt das ausgewählte Medium und gibt Zusammenfassung mit visuellen Medien zurück.

    Args:
        selected_items: Liste mit genau einem ausgewählten Item
        category: Kategorie des Mediums ('films', 'albums', 'books')

    Returns:
        Tuple mit (text_output, html_output)
    """
    if not selected_items or len(selected_items) != 1:
        return "Bitte wählen Sie genau ein Medium aus.", ""

    selected_item = selected_items[0]
    selected_item_clean = remove_emoji(selected_item)

    # Extrahiere Titel und Autor
    title, author = extract_title_and_author(selected_item_clean)

    # Bestimme Medientyp
    if category == "films":
        media_type = "film"
    elif category == "albums":
        media_type = "album"
    elif category == "books":
        media_type = "book"
    else:
        media_type = "medium"

    logger.info(f"Google-Suche für {media_type}: '{title}' von '{author}'")

    try:
        media_data = get_media_summary(title, author, media_type)

        text_result = f"🔍 Informationen zu: {title}"
        if author:
            text_result += f" - {author}"
        text_result += f"\n\n{media_data['summary']}"

        html_result = create_media_html(media_data.get("youtube_id"), media_data.get("cover_url"), media_type, title)

        return text_result, html_result

    except Exception as e:
        logger.error(f"Fehler bei Google-Suche: {e}")
        return f"❌ Fehler bei der Suche: {str(e)}", ""


def reject_selected(selected_items: List[str], category: str) -> Tuple[gr.update, str, gr.update, str, str, gr.update, str]:
    """
    Entfernt die ausgewählten Items und ersetzt sie durch neue (balanciert).

    Args:
        selected_items: Liste ausgewählter Display-Strings
        category: Kategorie ('films', 'albums', 'books')

    Returns:
        Tuple mit Updates für alle GUI-Komponenten
    """
    if not selected_items:
        return (
            gr.update(),
            "Keine Items ausgewählt.",
            gr.update(interactive=False),
            "",
            "",
            gr.update(interactive=False),
            "",
        )

    suggestions = current_suggestions.get(category, [])
    rejected_titles = []
    indices_to_remove = []

    # Identifiziere alle zu entfernenden Items
    for selected_item in selected_items:
        selected_item_clean = remove_emoji(selected_item)

        for i, s in enumerate(suggestions):
            display_text = f"{s['title']}"
            if s.get("author"):
                display_text += f" - {s['author']}"

            if display_text == selected_item_clean:
                rejected_titles.append(s["title"])
                indices_to_remove.append(i)
                rejected_item = {"title": s["title"]}
                state.reject(category, rejected_item)
                break

    # Entferne Items (von hinten nach vorne)
    for i in sorted(indices_to_remove, reverse=True):
        current_suggestions[category].pop(i)

    # Versuche neue Vorschläge zu holen (balanciert, 1 pro Quelle)
    needed_count = len(rejected_titles)
    new_suggestions = get_n_suggestions(category, n=needed_count, items_per_source=1)

    # Füge neue Vorschläge hinzu
    current_suggestions[category].extend(new_suggestions)

    # Aktualisiere die Auswahloptionen
    choices = []
    for s in current_suggestions[category]:
        display_text = f"{s['title']}"
        if s.get("author"):
            display_text += f" - {s['author']}"
        if s.get("source"):
            emoji = get_source_emoji(s["source"])
            if emoji:
                display_text = f"{emoji} {display_text}"
        choices.append(display_text)

    rejected_text = "', '".join(rejected_titles)
    if len(new_suggestions) == needed_count:
        info_text = f"{len(rejected_titles)} Titel wurden abgelehnt und durch neue ersetzt."
        success_msg = f"✅ '{rejected_text}' wurde(n) erfolgreich abgelehnt und ersetzt"
    elif new_suggestions:
        info_text = f"{len(rejected_titles)} Titel abgelehnt, {len(new_suggestions)} neue Vorschläge verfügbar."
        success_msg = f"✅ '{rejected_text}' wurde(n) abgelehnt, {len(new_suggestions)} Ersetzungen verfügbar"
    else:
        info_text = f"{len(rejected_titles)} Titel wurden abgelehnt. Keine weiteren Vorschläge verfügbar."
        success_msg = f"✅ '{rejected_text}' wurde(n) abgelehnt (keine Ersetzungen verfügbar)"

    return (
        gr.update(choices=choices, value=[]),
        info_text,
        gr.update(interactive=False),
        "",
        success_msg,
        gr.update(interactive=False),
        "",
    )


def save_current_recommendations() -> str:
    """
    Speichert die aktuell angezeigten Empfehlungen in eine Markdown-Datei.

    Sammelt alle aktuellen Vorschläge aus den drei Kategorien und
    schreibt sie formatiert in 'recommended.md'.

    Returns:
        Erfolgsmeldung oder Fehlermeldung
    """
    try:
        recommendations = {}

        for category in ["films", "albums", "books"]:
            suggestions = current_suggestions.get(category, [])
            recommendations[category] = suggestions

        filename = save_recommendations_to_markdown(recommendations)

        total_count = sum(len(items) for items in recommendations.values())

        if total_count == 0:
            return "⚠️ Keine Empfehlungen zum Speichern vorhanden. Erstellen Sie zuerst Vorschläge."

        return f"✅ {total_count} Empfehlungen erfolgreich in '{filename}' gespeichert!"

    except Exception as e:
        logger.error(f"Fehler beim Speichern: {e}")
        return f"❌ Fehler beim Speichern: {str(e)}"


def initialize_recommendations() -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]], List[Dict[str, Any]]]:
    """
    Lädt initiale balancierte Vorschläge für alle Kategorien beim Start.

    Ruft für jede Kategorie Empfehlungen ab (12 Items mit 4 pro Quelle)
    und speichert sie automatisch in einer Markdown-Datei.

    Returns:
        Tuple mit (film_suggestions, album_suggestions, book_suggestions)
    """
    logger.info("Lade initiale balancierte Vorschläge...")

    # Filme laden (12 mit je 4 pro Quelle)
    film_suggestions = get_n_suggestions("films", n=12, items_per_source=4)
    current_suggestions["films"] = film_suggestions

    # Alben laden (12 mit je 4 pro Quelle)
    album_suggestions = get_n_suggestions("albums", n=12, items_per_source=4)
    current_suggestions["albums"] = album_suggestions

    # Bücher laden (12 mit je 4 pro Quelle)
    book_suggestions = get_n_suggestions("books", n=12, items_per_source=4)
    current_suggestions["books"] = book_suggestions

    # Automatisch in Datei speichern
    try:
        recommendations = {
            "films": film_suggestions,
            "albums": album_suggestions,
            "books": book_suggestions,
        }
        filename = save_recommendations_to_markdown(recommendations)
        total_count = len(film_suggestions) + len(album_suggestions) + len(book_suggestions)
        logger.info(f"{total_count} initiale balancierte Empfehlungen in '{filename}' gespeichert")
    except Exception as e:
        logger.error(f"Fehler beim Speichern der initialen Empfehlungen: {e}")

    return film_suggestions, album_suggestions, book_suggestions


def get_initial_choices(suggestions: List[Dict[str, Any]]) -> List[str]:
    """
    Erstellt die Auswahloptionen für die initiale Anzeige.

    Formatiert Empfehlungen mit Titel, Autor und Quellen-Emoji für
    die CheckboxGroup-Komponente.

    Args:
        suggestions: Liste von Empfehlungen

    Returns:
        Liste formatierter Display-Strings mit Emojis
    """
    if not suggestions:
        return []

    choices = []
    for s in suggestions:
        display_text = f"{s['title']}"
        if s.get("author"):
            display_text += f" - {s['author']}"
        if s.get("source"):
            emoji = get_source_emoji(s["source"])
            if emoji:
                display_text = f"{emoji} {display_text}"
        choices.append(display_text)
    return choices


# CSS für besseres Styling
css = """
.suggestion-container {
    border: 1px solid #ddd;
    border-radius: 8px;
    padding: 15px;
    margin: 10px 0;
    background-color: #f9f9f9;
}

.suggestion-info {
    background-color: #e8f4f8;
    padding: 10px;
    border-radius: 5px;
    margin: 10px 0;
    border-left: 4px solid #17a2b8;
}

.reject-button {
    background-color: #dc3545 !important;
    border-color: #dc3545 !important;
}

.reject-button:hover {
    background-color: #c82333 !important;
    border-color: #bd2130 !important;
}

.save-button {
    background-color: #28a745 !important;
    border-color: #28a745 !important;
    font-weight: bold !important;
}

.save-button:hover {
    background-color: #218838 !important;
    border-color: #1e7e34 !important;
}

.google-button {
    background-color: #4285f4 !important;
    border-color: #4285f4 !important;
    color: white !important;
}

.google-button:hover {
    background-color: #3367d6 !important;
    border-color: #3367d6 !important;
}

.google-button:disabled {
    background-color: #cccccc !important;
    border-color: #cccccc !important;
    color: #666666 !important;
}

.success-message {
    background-color: #d4edda;
    color: #155724;
    border: 1px solid #c3e6cb;
    padding: 8px 12px;
    border-radius: 4px;
    margin: 5px 0;
}

.gradio-checkboxgroup label {
    padding: 8px 12px;
    margin: 4px 0;
    border-radius: 6px;
    border: 1px solid #e0e0e0;
    background-color: #fafafa;
    transition: all 0.2s ease;
    display: block;
}

.gradio-checkboxgroup label:hover {
    background-color: #f0f8ff;
    border-color: #007bff;
}

.gradio-checkboxgroup input[type="checkbox"]:checked + span {
    background-color: #e7f3ff;
    border-color: #007bff;
    font-weight: 500;
}
"""

# Initialisiere Komponenten
state = AppState()
library_search = KoelnLibrarySearch()
recommender = Recommender(library_search, state)

# Lade Datenquellen (nur einmal beim Start)
logger.info("Lade Datenquellen...")
films = load_or_fetch_films()
albums = load_or_fetch_albums()
books = load_or_fetch_books()

# Globale Variablen für aktuelle Vorschläge
current_suggestions: Dict[str, List[Dict[str, Any]]] = {"films": [], "albums": [], "books": []}

# Lade initiale Vorschläge
logger.info("Initialisiere balancierte Empfehlungen...")
initial_films, initial_albums, initial_books = initialize_recommendations()

# Erstelle initiale Auswahloptionen
initial_film_choices = get_initial_choices(initial_films)
initial_album_choices = get_initial_choices(initial_albums)
initial_book_choices = get_initial_choices(initial_books)

with gr.Blocks(css=css, title="Bibliothek-Empfehlungen") as demo:
    gr.Markdown("# 🎬💿📚 Bibliothek-Empfehlungen")
    gr.Markdown("Entdecken Sie verfügbare Medien in der Stadtbibliothek Köln!")

    # Globaler Speichern-Button oben
    with gr.Row():
        save_btn = gr.Button("💾 Alle Empfehlungen speichern", variant="primary", elem_classes=["save-button"], size="lg")

    save_message = gr.HTML(value="", visible=False, elem_classes=["success-message"])

    with gr.Tab("🎬 Filme"):
        with gr.Column(elem_classes=["suggestion-container"]):
            film_checkbox = gr.CheckboxGroup(
                label="Empfohlene Filme (balanciert: 4 BBC, 4 FBW, 4 Oscar)",
                choices=initial_film_choices,
                value=[],
                interactive=True,
                info="Wählen Sie Filme aus der Liste aus, um sie zu entfernen",
            )

            with gr.Row():
                film_suggest_btn = gr.Button("Neue Filme vorschlagen", variant="primary")
                film_reject_btn = gr.Button(
                    "Ausgewählte Filme entfernen", variant="secondary", interactive=False, elem_classes=["reject-button"]
                )
                film_google_btn = gr.Button(
                    "🔍 Google-Suche", variant="secondary", interactive=False, elem_classes=["google-button"]
                )

            film_info = gr.Textbox(
                label="Information",
                value=(
                    f"{len(initial_films)} Filme beim Start geladen (balanciert aus allen Quellen). "
                    "Wählen Sie Titel aus, um sie zu entfernen."
                    if initial_films
                    else "Keine Filme verfügbar."
                ),
                interactive=False,
                elem_classes=["suggestion-info"],
            )

            film_detail = gr.Textbox(label="Details zu den ausgewählten Filmen", value="", interactive=False, lines=6)

            film_media = gr.HTML(value="", label="Visuelle Medien")

            film_message = gr.HTML(value="", visible=False, elem_classes=["success-message"])

    with gr.Tab("🎵 Musik"):
        with gr.Column(elem_classes=["suggestion-container"]):
            album_checkbox = gr.CheckboxGroup(
                label="Empfohlene Alben (balanciert: 4 Radio Eins, 4 Oscar, 4 Personalisiert)",
                choices=initial_album_choices,
                value=[],
                interactive=True,
                info="Wählen Sie Alben aus der Liste aus, um sie zu entfernen",
            )

            with gr.Row():
                album_suggest_btn = gr.Button("Neue Alben vorschlagen", variant="primary")
                album_reject_btn = gr.Button(
                    "Ausgewählte Alben entfernen", variant="secondary", interactive=False, elem_classes=["reject-button"]
                )
                album_google_btn = gr.Button(
                    "🔍 Google-Suche", variant="secondary", interactive=False, elem_classes=["google-button"]
                )

            album_info = gr.Textbox(
                label="Information",
                value=(
                    f"{len(initial_albums)} Alben beim Start geladen (balanciert aus allen Quellen). "
                    "Wählen Sie Titel aus, um sie zu entfernen."
                    if initial_albums
                    else "Keine Alben verfügbar."
                ),
                interactive=False,
                elem_classes=["suggestion-info"],
            )

            album_detail = gr.Textbox(label="Details zu den ausgewählten Alben", value="", interactive=False, lines=6)

            album_media = gr.HTML(value="", label="Visuelle Medien")

            album_message = gr.HTML(value="", visible=False, elem_classes=["success-message"])

    with gr.Tab("📚 Bücher"):
        with gr.Column(elem_classes=["suggestion-container"]):
            book_checkbox = gr.CheckboxGroup(
                label="Empfohlene Bücher (balanciert: 6 NYT Kanon, 6 Ratgeber)",
                choices=initial_book_choices,
                value=[],
                interactive=True,
                info="Wählen Sie Bücher aus der Liste aus, um sie zu entfernen",
            )

            with gr.Row():
                book_suggest_btn = gr.Button("Neue Bücher vorschlagen", variant="primary")
                book_reject_btn = gr.Button(
                    "Ausgewählte Bücher entfernen", variant="secondary", interactive=False, elem_classes=["reject-button"]
                )
                book_google_btn = gr.Button(
                    "🔍 Google-Suche", variant="secondary", interactive=False, elem_classes=["google-button"]
                )

            book_info = gr.Textbox(
                label="Information",
                value=(
                    f"{len(initial_books)} Bücher beim Start geladen (balanciert aus allen Quellen). "
                    "Wählen Sie Titel aus, um sie zu entfernen."
                    if initial_books
                    else "Keine Bücher verfügbar."
                ),
                interactive=False,
                elem_classes=["suggestion-info"],
            )

            book_detail = gr.Textbox(label="Details zu den ausgewählten Büchern", value="", interactive=False, lines=6)

            book_media = gr.HTML(value="", label="Visuelle Medien")

            book_message = gr.HTML(value="", visible=False, elem_classes=["success-message"])

    # Event Handler für globalen Speichern-Button
    save_btn.click(fn=save_current_recommendations, outputs=[save_message]).then(
        fn=lambda x: gr.update(visible=bool(x), value=x) if x else gr.update(visible=False),
        inputs=[save_message],
        outputs=[save_message],
    )

    # Event Handler für Filme
    film_suggest_btn.click(fn=lambda: suggest("films"), outputs=[film_checkbox, film_info, film_reject_btn, film_detail])

    film_checkbox.change(
        fn=lambda x: on_selection_change(x, "films"),
        inputs=[film_checkbox],
        outputs=[film_reject_btn, film_detail, film_google_btn],
    )

    film_reject_btn.click(
        fn=lambda x: reject_selected(x, "films"),
        inputs=[film_checkbox],
        outputs=[film_checkbox, film_info, film_reject_btn, film_detail, film_message, film_google_btn, film_media],
    ).then(
        fn=lambda x: gr.update(visible=bool(x), value=x) if x else gr.update(visible=False),
        inputs=[film_message],
        outputs=[film_message],
    )

    film_google_btn.click(
        fn=lambda x: google_search_selected(x, "films"), inputs=[film_checkbox], outputs=[film_detail, film_media]
    )

    # Event Handler für Alben
    album_suggest_btn.click(fn=lambda: suggest("albums"), outputs=[album_checkbox, album_info, album_reject_btn, album_detail])

    album_checkbox.change(
        fn=lambda x: on_selection_change(x, "albums"),
        inputs=[album_checkbox],
        outputs=[album_reject_btn, album_detail, album_google_btn],
    )

    album_reject_btn.click(
        fn=lambda x: reject_selected(x, "albums"),
        inputs=[album_checkbox],
        outputs=[album_checkbox, album_info, album_reject_btn, album_detail, album_message, album_google_btn, album_media],
    ).then(
        fn=lambda x: gr.update(visible=bool(x), value=x) if x else gr.update(visible=False),
        inputs=[album_message],
        outputs=[album_message],
    )

    album_google_btn.click(
        fn=lambda x: google_search_selected(x, "albums"), inputs=[album_checkbox], outputs=[album_detail, album_media]
    )

    # Event Handler für Bücher
    book_suggest_btn.click(fn=lambda: suggest("books"), outputs=[book_checkbox, book_info, book_reject_btn, book_detail])

    book_checkbox.change(
        fn=lambda x: on_selection_change(x, "books"),
        inputs=[book_checkbox],
        outputs=[book_reject_btn, book_detail, book_google_btn],
    )

    book_reject_btn.click(
        fn=lambda x: reject_selected(x, "books"),
        inputs=[book_checkbox],
        outputs=[book_checkbox, book_info, book_reject_btn, book_detail, book_message, book_google_btn, book_media],
    ).then(
        fn=lambda x: gr.update(visible=bool(x), value=x) if x else gr.update(visible=False),
        inputs=[book_message],
        outputs=[book_message],
    )

    book_google_btn.click(
        fn=lambda x: google_search_selected(x, "books"), inputs=[book_checkbox], outputs=[book_detail, book_media]
    )

if __name__ == "__main__":
    demo.launch()
