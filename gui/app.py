import gradio as gr
import os
import json
import re
from typing import List, Dict, Any, Tuple, Optional
from library.search import KoelnLibrarySearch
from library.search import filter_results_by_author
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

from utils.borrowed_blacklist import get_borrowed_blacklist
from utils.blacklist import get_blacklist
from utils.io import DATA_DIR, save_recommendations_to_markdown
from utils.favorites import get_favorites_manager

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
                    "source": g.get("source", SOURCE_BEST_GUIDES),
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

    Die Anzahl wird dynamisch berechnet (4 pro Quelle).

    Args:
        category: Kategorie ('films', 'albums', 'books')

    Returns:
        Tuple mit (checkbox_update, info_text, button_state, detail_text)
    """
    logger.info(f"Erstelle Vorschläge für Kategorie: {category}")

    # Hole Vorschläge (Anzahl wird dynamisch berechnet)
    suggestions = get_n_suggestions(category, items_per_source=4)

    # Aktualisiere globale Vorschläge
    current_suggestions[category] = suggestions

    if not suggestions:
        logger.warning(f"Keine Vorschläge für {category} gefunden")
        return (gr.update(choices=[], value=[]), "Keine Vorschläge gefunden.", gr.update(interactive=False), "")

    # Erstelle Auswahloptionen für die CheckboxGroup
    choices = []
    for s in suggestions:
        display_text = f"{s['title']}"
        if s.get("author"):
            display_text += f" - {s['author']}"
        # Emoji hinzufügen
        if s.get("source"):
            from utils.sources import get_source_emoji

            emoji = get_source_emoji(s["source"])
            if emoji:
                display_text = f"{emoji} {display_text}"
        choices.append(display_text)

    info_text = (
        f"{len(suggestions)} Vorschläge gefunden (balanciert aus allen Quellen). " "Wählen Sie Titel aus, um sie zu entfernen."
    )

    logger.info(f"{len(suggestions)} Vorschläge für {category} erstellt")

    return (gr.update(choices=choices, value=[]), info_text, gr.update(interactive=False), "")


def get_n_suggestions(category: str, items_per_source: int = 4) -> List[Dict[str, Any]]:
    """
    Holt neue Vorschläge für eine Kategorie, balanciert nach Quelle.

    Die Gesamtanzahl wird dynamisch berechnet:
    n = Anzahl Quellen * items_per_source

    Args:
        category: Kategorie ('films', 'albums', 'books')
        items_per_source: Items pro Quelle (default: 4)

    Returns:
        Liste von Empfehlungen, balanciert nach Quelle

    Example:
        >>> suggestions = get_n_suggestions('films', items_per_source=4)
        >>> # Bei 3 Quellen -> 12 Vorschläge
    """
    logger.info(f"Hole Vorschläge für {category} ({items_per_source} pro Quelle)")

    if category == "films":
        suggestions = recommender.suggest_films(films, items_per_source=items_per_source)
    elif category == "albums":
        suggestions = recommender.suggest_albums(albums, items_per_source=items_per_source)
    elif category == "books":
        suggestions = recommender.suggest_books(books, items_per_source=items_per_source)
    else:
        logger.warning(f"Unbekannte Kategorie: {category}")
        suggestions = []

    logger.info(f"{len(suggestions)} Vorschläge für {category} geholt")

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
        logger.debug("Keine Items zum Ablehnen ausgewählt")
        return (
            gr.update(),
            "Keine Items ausgewählt.",
            gr.update(interactive=False),
            "",
            "",
            gr.update(interactive=False),
            "",
        )

    logger.info(f"Lehne {len(selected_items)} {category} ab")

    suggestions = current_suggestions.get(category, [])
    rejected_titles = []
    indices_to_remove = []

    # Identifiziere alle zu entfernenden Items
    for selected_item in selected_items:
        # Entferne Emoji
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
        selected_item_clean = emoji_pattern.sub("", selected_item).strip()

        for i, s in enumerate(suggestions):
            display_text = f"{s['title']}"
            if s.get("author"):
                display_text += f" - {s['author']}"

            if display_text == selected_item_clean:
                rejected_titles.append(s["title"])
                indices_to_remove.append(i)
                rejected_item = {"title": s["title"]}
                state.reject(category, rejected_item)
                logger.debug(f"Item abgelehnt: {s['title']}")
                break

    # Entferne Items (von hinten nach vorne)
    for i in sorted(indices_to_remove, reverse=True):
        current_suggestions[category].pop(i)

    # Versuche neue Vorschläge zu holen (balanciert, 1 pro Quelle)
    needed_count = len(rejected_titles)
    new_suggestions = get_n_suggestions(category, items_per_source=1)

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
        info_text = f"{len(rejected_titles)} Titel wurden abgelehnt " "und durch neue ersetzt."
        success_msg = f"✅ '{rejected_text}' wurde(n) erfolgreich " "abgelehnt und ersetzt"
    elif new_suggestions:
        info_text = f"{len(rejected_titles)} Titel abgelehnt, " f"{len(new_suggestions)} neue Vorschläge verfügbar."
        success_msg = f"✅ '{rejected_text}' wurde(n) abgelehnt " "(keine Ersetzungen verfügbar)"
    else:
        info_text = f"{len(rejected_titles)} Titel wurden abgelehnt. " "Keine weiteren Vorschläge verfügbar."
        success_msg = f"✅ '{rejected_text}' wurde(n) abgelehnt, " f"{len(new_suggestions)} Ersetzungen verfügbar"

    logger.info(f"{len(rejected_titles)} Items abgelehnt, " f"{len(new_suggestions)} neue hinzugefügt")

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

    Ruft für jede Kategorie Empfehlungen ab (4 pro Quelle, dynamisch berechnet)
    und speichert sie automatisch in einer Markdown-Datei.

    Returns:
        Tuple mit (film_suggestions, album_suggestions, book_suggestions)
    """
    logger.info("Lade initiale balancierte Vorschläge...")

    # Filme laden (4 pro Quelle, dynamisch)
    film_suggestions = get_n_suggestions("films", items_per_source=4)
    current_suggestions["films"] = film_suggestions

    # Alben laden (4 pro Quelle, dynamisch)
    album_suggestions = get_n_suggestions("albums", items_per_source=4)
    current_suggestions["albums"] = album_suggestions

    # Bücher laden (4 pro Quelle, dynamisch)
    book_suggestions = get_n_suggestions("books", items_per_source=4)
    current_suggestions["books"] = book_suggestions

    # Automatisch in Datei speichern
    try:
        from utils.io import save_recommendations_to_markdown

        recommendations = {
            "films": film_suggestions,
            "albums": album_suggestions,
            "books": book_suggestions,
        }
        filename = save_recommendations_to_markdown(recommendations)
        total_count = len(film_suggestions) + len(album_suggestions) + len(book_suggestions)
        logger.info(f"{total_count} initiale balancierte Empfehlungen " f"in '{filename}' gespeichert")
    except Exception as e:
        logger.error(f"Fehler beim Speichern der initialen Empfehlungen: {e}")

    return film_suggestions, album_suggestions, book_suggestions


def load_favorites_to_suggestions() -> Tuple[int, int, int]:
    """
    Lädt gespeicherte Favoriten und fügt sie zu den initialen Vorschlägen hinzu.

    Returns:
        Tuple mit (anzahl_filme, anzahl_alben, anzahl_bücher)
    """
    logger.info("=" * 60)
    logger.info("⭐ LADE GESPEICHERTE FAVORITEN")
    logger.info("=" * 60)

    favorites_manager = get_favorites_manager()
    all_favorites = favorites_manager.get_favorites()

    counts = {"films": 0, "albums": 0, "books": 0}

    for category, favorites in all_favorites.items():
        if not favorites:
            continue

        logger.info(f"\n📂 {category.upper()}: {len(favorites)} Favoriten")

        for fav in favorites:
            title = fav["title"]
            author = fav.get("author", "")
            media_type = fav.get("media_type", "")
            search_type = fav.get("search_type", "specific")

            logger.info(f"  🔍 Suche: '{title}' von '{author}'")

            # Suche nach dem Favoriten in der Bibliothek
            try:
                search_engine = KoelnLibrarySearch()

                if search_type == "specific" and title:
                    query = f"{title} {author} {media_type}".strip()
                else:
                    query = f"{author} {media_type}".strip()

                results = search_engine.search(query)

                # Filtere nach Autor falls vorhanden
                if author and results:
                    results = filter_results_by_author(results, author, threshold=0.7)

                # Prüfe auf verfügbare Exemplare
                available = [r for r in results if "verfügbar" in r.get("zentralbibliothek_info", "").lower()]

                if available:
                    # Füge zur Vorschlagsliste hinzu
                    item = {
                        "title": available[0].get("title", title),
                        "author": author,
                        "type": media_type,
                        "bib_number": available[0].get(
                            "zentralbibliothek_bestand", available[0].get("zentralbibliothek_info", "")
                        )[:300],
                        "source": "⭐ Favoriten (Gespeichert)",
                    }

                    current_suggestions[category].insert(0, item)
                    counts[category] += 1

                    logger.info(f"  ✅ Verfügbar! Hinzugefügt zu {category}")
                else:
                    logger.info("  ℹ️ Aktuell nicht verfügbar")

            except Exception as e:
                logger.error(f"  ❌ Fehler bei Suche: {e}")

        # Kurze Pause zwischen Kategorien
        if favorites:
            import time

            time.sleep(1)

    total = sum(counts.values())
    logger.info("\n" + "=" * 60)
    logger.info(f"✅ {total} Favoriten geladen und verfügbar")
    logger.info(f"   Filme: {counts['films']}, Alben: {counts['albums']}, Bücher: {counts['books']}")
    logger.info("=" * 60 + "\n")

    return counts["films"], counts["albums"], counts["books"]


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


def search_favorite_medium(author: str, title: str, media_type: str) -> Tuple[str, str, gr.update, gr.update, gr.update]:
    """
    Sucht nach einem individuellen Medium im Bibliothekskatalog.

    Logik:
    - Wenn Titel angegeben: Suche nach spezifischem Medium
    - Wenn nur Autor: Suche alle Medien des Autors (max. 2 verfügbare)
    - Gefunden & verfügbar: Füge zu entsprechendem Tab hinzu
    - Gefunden & entliehen: Auf Entleih-Blacklist
    - Nicht gefunden: Auf normale Blacklist

    Args:
        author: Autor/Künstler/Regisseur
        title: Titel des Mediums (optional)
        media_type: Medienart (DVD, CD, Buch)

    Returns:
        Tuple mit (result_text, success_msg, film_update, album_update, book_update)
    """
    logger.info(f"Favoriten-Suche: Autor='{author}', Titel='{title}', Typ={media_type}")

    try:
        # Validierung
        if not author and not title:
            error_msg = "❌ Bitte geben Sie mindestens einen Autor/Künstler oder Titel an."
            return error_msg, "", gr.update(), gr.update(), gr.update()

        # Bestimme Kategorie
        category = _get_category_from_media_type(media_type)

        # Prüfe Entleih-Blacklist
        borrowed_blacklist = get_borrowed_blacklist()
        if title and borrowed_blacklist.is_blacklisted(title, author):
            info_msg = f"ℹ️ '{title}' ist aktuell entliehen. Wird automatisch geprüft wenn verfügbar."
            return info_msg, "", gr.update(), gr.update(), gr.update()

        # Suche durchführen
        search_engine = KoelnLibrarySearch()

        # Baue Suchquery
        if title:
            query = f"{title} {author} {media_type}".strip()
        else:
            query = f"{author} {media_type}".strip()

        logger.debug(f"Suchquery: '{query}'")

        # NEU: Nutze erweiterte Suche mit Author-Matching
        # from library.search import search_with_author

        results = search_engine.search_with_author(query, expected_author=author)

        if not results:
            # Keine Treffer - auf Blacklist
            _handle_no_results(title, author, category, media_type)
            error_msg = f"❌ Keine Treffer für '{title or author}' gefunden."
            return error_msg, "", gr.update(), gr.update(), gr.update()

        # Filtere und verarbeite Ergebnisse
        if title:
            # Spezifisches Medium gesucht - verwende Titel UND Autor
            if author:
                logger.info(f"Filtere nach Autor '{author}' und Titel '{title}'")

                # NEU: Übergebe auch den Titel
                filtered = filter_results_by_author(results, author, expected_title=title, threshold=0.7)  # NEU!

                if filtered:
                    results = filtered
                    logger.info(f"Nach Filter: {len(results)} relevante Treffer")

            return _handle_specific_medium(results, title, author, media_type, category)
        else:
            # Alle Medien des Autors (max. 2)
            return _handle_artist_search(results, author, media_type, category)

    except Exception as e:
        logger.error(f"Unerwarteter Fehler in search_favorite_medium: {e}", exc_info=True)
        error_msg = f"❌ Ein Fehler ist aufgetreten: {str(e)}"
        return error_msg, "", gr.update(), gr.update(), gr.update()


def show_saved_favorites() -> str:
    """
    Zeigt alle gespeicherten Favoriten an.

    Returns:
        Formatierte Liste aller Favoriten
    """
    favorites_manager = get_favorites_manager()
    all_favorites = favorites_manager.get_favorites()

    output = "## ⭐ Gespeicherte Favoriten\n\n"

    total = sum(len(items) for items in all_favorites.values())

    if total == 0:
        return output + "_Noch keine Favoriten gespeichert._"

    output += f"**Gesamt:** {total} Favoriten\n\n"

    for category, favorites in all_favorites.items():
        if not favorites:
            continue

        cat_name = {"films": "🎬 Filme", "albums": "🎵 Alben", "books": "📚 Bücher"}.get(category, category)

        output += f"### {cat_name} ({len(favorites)})\n\n"

        for fav in favorites:
            output += f"- **{fav['title']}**"
            if fav.get("author"):
                output += f" - _{fav['author']}_"
            output += f"\n  Hinzugefügt: {fav['added_at']}\n"

        output += "\n"

    return output


def _get_category_from_media_type(media_type: str) -> str:
    """Wandelt Medientyp in Kategorie um."""
    if media_type == "DVD":
        return "films"
    elif media_type == "CD":
        return "albums"
    elif media_type == "Buch":
        return "books"
    return "films"  # Default


def _handle_no_results(title: str, author: str, category: str, media_type: str) -> None:
    """Behandelt Fall ohne Suchergebnisse."""
    blacklist = get_blacklist()

    item = {"title": title or author, "author": author, "type": media_type}

    reason = "Keine Treffer bei individueller Suche"
    blacklist.add_to_blacklist(category, item, reason=reason)

    logger.info(f"Auf Blacklist: '{title or author}' - {reason}")


def _handle_specific_medium(
    results: List[Dict[str, Any]], title: str, author: str, media_type: str, category: str
) -> Tuple[str, str, gr.update, gr.update, gr.update]:
    """
    Behandelt Suche nach spezifischem Medium.

    Returns:
        Tuple mit Updates
    """
    borrowed_blacklist = get_borrowed_blacklist()
    available_items: List[Dict[str, Any]] = []
    borrowed_items: List[Dict[str, Any]] = []

    try:
        for result in results:
            zentralbib_info = result.get("zentralbibliothek_info", "")

            if "verfügbar" in zentralbib_info.lower():
                # NEU: Füge Match-Info hinzu falls vorhanden
                match_info = ""
                if result.get("author_match_score"):
                    score = result["author_match_score"]
                    field = result.get("author_match_field", "unknown")
                    match_info = f" (Author-Match: {score:.0%} via {field})"

                available_items.append(
                    {
                        "title": result.get("title", title),
                        "author": author,
                        "type": media_type,
                        "bib_number": result.get("zentralbibliothek_bestand", zentralbib_info)[:300]
                        + match_info,  # Match-Info anhängen
                        "source": "Favoriten (Individuelle Suche)",
                    }
                )
            elif "entliehen" in zentralbib_info.lower():
                borrowed_blacklist.add_to_blacklist(
                    title=result.get("title", title), author=author, media_type=media_type, availability_text=zentralbib_info
                )
                borrowed_items.append(result)

        if available_items:
            item = available_items[0]
            _add_to_suggestions(category, item)

            favorites_manager = get_favorites_manager()
            favorites_manager.add_favorite(
                category=category, title=title, author=author, media_type=media_type, search_type="specific"
            )
            logger.info(f"💾 Favorit gespeichert: '{title}'")

            success_msg = f"✅ '{item['title']}' gefunden und zu {_get_tab_name(category)} hinzugefügt!"
            result_text = f"📦 Gefunden: {item['title']}\n📍 Verfügbarkeit: {item['bib_number'][:200]}..."

            updates = _create_tab_updates(category)
            return result_text, success_msg, updates[0], updates[1], updates[2]

        elif borrowed_items:
            info_msg = f"📅 '{title}' ist aktuell entliehen. Wird automatisch geprüft wenn verfügbar."
            return info_msg, "", gr.update(), gr.update(), gr.update()

        else:
            _handle_no_results(title, author, category, media_type)
            error_msg = f"❌ '{title}' gefunden aber nicht verfügbar."
            return error_msg, "", gr.update(), gr.update(), gr.update()

    except Exception as e:
        logger.error(f"Fehler in _handle_specific_medium: {e}", exc_info=True)
        error_msg = f"❌ Fehler bei der Verarbeitung: {str(e)}"
        return error_msg, "", gr.update(), gr.update(), gr.update()


def _handle_artist_search(
    results: List[Dict[str, Any]], artist: str, media_type: str, category: str
) -> Tuple[str, str, gr.update, gr.update, gr.update]:
    """
    Behandelt Suche nach allen Medien eines Künstlers (max. 2).

    Für CDs: Filtert bereits vorhandene Alben aus MP3-Archiv heraus.
    Nutzt Artist-Blacklist statt normaler Blacklist für Künstler ohne Medien.

    Returns:
        Tuple mit Updates
    """
    from preprocessing.filters import filter_existing_albums
    from utils.artist_blacklist import get_artist_blacklist

    borrowed_blacklist = get_borrowed_blacklist()
    available_items: List[Dict[str, Any]] = []

    try:
        for result in results[:15]:  # Max. 15 Treffer prüfen
            zentralbib_info = result.get("zentralbibliothek_info", "")
            result_title = result.get("title", "")

            if "verfügbar" in zentralbib_info.lower():
                available_items.append(
                    {
                        "title": result_title,
                        "author": artist,
                        "type": media_type,
                        "bib_number": result.get("zentralbibliothek_bestand", zentralbib_info)[:300],  # GEÄNDERT
                        "source": "Favoriten (Künstler-Suche)",
                    }
                )
            elif "entliehen" in zentralbib_info.lower():
                borrowed_blacklist.add_to_blacklist(
                    title=result_title, author=artist, media_type=media_type, availability_text=zentralbib_info
                )

            # Stoppe wenn 2 verfügbare gefunden
            if len(available_items) >= 2:
                break

        # NEU: Für CDs - Filtere bereits vorhandene Alben
        if media_type == "CD" and available_items:
            logger.info(f"Filtere bereits vorhandene Alben von '{artist}'...")

            # FIXIERT: available_items ist bereits eine Liste von Dicts
            # filter_existing_albums erwartet genau dieses Format
            filtered_albums = filter_existing_albums(available_items, "H:\\MP3 Archiv")
            available_items = filtered_albums

            logger.info(f"{len(available_items)} neue Alben nach MP3-Filterung")

        if available_items:
            # Füge max. 2 hinzu
            added_count = 0
            added_titles: List[str] = []

            favorites_manager = get_favorites_manager()

            for item in available_items[:2]:
                _add_to_suggestions(category, item)
                added_titles.append(item["title"])
                added_count += 1

                # NEU: Speichere jeden als Favorit
                favorites_manager.add_favorite(
                    category=category, title=item["title"], author=artist, media_type=media_type, search_type="artist"
                )
                logger.info(f"💾 Favorit gespeichert: '{item['title']}'")

            success_msg = f"✅ {added_count} Medium/Medien von '{artist}' zu {_get_tab_name(category)} hinzugefügt!"
            result_text = f"📦 Gefunden von '{artist}':\n" + "\n".join(f"  • {t}" for t in added_titles)

            updates = _create_tab_updates(category)
            return result_text, success_msg, updates[0], updates[1], updates[2]

        else:
            # Keine verfügbaren gefunden (oder alle bereits vorhanden)

            # FIXIERT: Für CDs (Künstler-Suche) -> Artist-Blacklist verwenden
            if media_type == "CD":
                artist_blacklist = get_artist_blacklist()
                # Schätze Song-Count (0 da wir nicht wissen)
                artist_blacklist.add_to_blacklist(
                    artist, song_count=0, reason="Favoriten-Suche: Keine neuen verfügbaren Alben"
                )
                logger.info(f"'{artist}' zur Artist-Blacklist hinzugefügt")
            else:
                # Für Filme/Bücher -> Normale Blacklist (mit leerem Titel!)
                blacklist = get_blacklist()
                item = {"title": "", "author": artist, "type": media_type}  # LEER da nur Künstler-Suche
                blacklist.add_to_blacklist(category, item, reason="Künstler-Suche: Keine verfügbaren/neuen Medien")

            error_msg = f"❌ Keine neuen verfügbaren Medien von '{artist}' gefunden."
            return error_msg, "", gr.update(), gr.update(), gr.update()

    except Exception as e:
        logger.error(f"Fehler in _handle_artist_search: {e}", exc_info=True)
        error_msg = f"❌ Fehler bei der Verarbeitung: {str(e)}"
        return error_msg, "", gr.update(), gr.update(), gr.update()


def _add_to_suggestions(category: str, item: Dict[str, Any]) -> None:
    """
    Fügt ein Medium an den Anfang der Vorschlagsliste ein.

    Args:
        category: Kategorie ('films', 'albums', 'books')
        item: Medium-Dictionary
    """
    # Füge an Position 0 ein
    current_suggestions[category].insert(0, item)

    logger.info(f"Medium an Anfang von {category} eingefügt: {item['title']}")


def _get_tab_name(category: str) -> str:
    """Gibt deutschen Tab-Namen zurück."""
    names = {"films": "Filme", "albums": "Musik", "books": "Bücher"}
    return names.get(category, category)


def _create_tab_updates(category: str) -> Tuple[gr.update, gr.update, gr.update]:
    """
    Erstellt Updates für alle drei Tabs.

    Args:
        category: Aktive Kategorie die geupdatet werden soll

    Returns:
        Tuple mit (film_update, album_update, book_update)
    """
    from utils.sources import get_source_emoji

    updates = []

    for cat in ["films", "albums", "books"]:
        if cat == category:
            # Update diesen Tab
            choices = []
            for s in current_suggestions[cat]:
                display_text = f"{s['title']}"
                if s.get("author"):
                    display_text += f" - {s['author']}"
                if s.get("source"):
                    emoji = get_source_emoji(s["source"])
                    if emoji:
                        display_text = f"{emoji} {display_text}"
                    else:
                        display_text = f"⭐ {display_text}"  # Favoriten-Emoji
                choices.append(display_text)

            updates.append(gr.update(choices=choices, value=[]))
        else:
            # Keine Änderung
            updates.append(gr.update())

    return tuple(updates)


# Modernes, dark-mode-freundliches CSS
css = """
/* =================================================================
   GLOBALE VARIABLEN & THEME
   ================================================================= */
:root {
    --primary-color: #667eea;
    --primary-hover: #5568d3;
    --secondary-color: #764ba2;
    --success-color: #48bb78;
    --success-hover: #38a169;
    --danger-color: #f56565;
    --danger-hover: #e53e3e;
    --info-color: #4299e1;
    --warning-color: #ed8936;

    --bg-primary: #ffffff;
    --bg-secondary: #f7fafc;
    --bg-tertiary: #edf2f7;
    --bg-gradient-start: #667eea;
    --bg-gradient-end: #764ba2;

    --text-primary: #2d3748;
    --text-secondary: #4a5568;
    --text-tertiary: #718096;

    --border-color: #e2e8f0;
    --border-radius: 12px;
    --border-radius-sm: 8px;
    --border-radius-lg: 16px;

    --shadow-sm: 0 1px 3px 0 rgba(0, 0, 0, 0.1), 0 1px 2px 0 rgba(0, 0, 0, 0.06);
    --shadow-md: 0 4px 6px -1px rgba(0, 0, 0, 0.1), 0 2px 4px -1px rgba(0, 0, 0, 0.06);
    --shadow-lg: 0 10px 15px -3px rgba(0, 0, 0, 0.1), 0 4px 6px -2px rgba(0, 0, 0, 0.05);
    --shadow-xl: 0 20px 25px -5px rgba(0, 0, 0, 0.1), 0 10px 10px -5px rgba(0, 0, 0, 0.04);

    --transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
}

/* Dark Mode Support */
@media (prefers-color-scheme: dark) {
    :root {
        --bg-primary: #1a202c;
        --bg-secondary: #2d3748;
        --bg-tertiary: #4a5568;

        --text-primary: #f7fafc;
        --text-secondary: #e2e8f0;
        --text-tertiary: #cbd5e0;

        --border-color: #4a5568;
    }
}

/* =================================================================
   GLOBALE STYLES
   ================================================================= */
.gradio-container {
    font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', 'Roboto',
                 'Helvetica Neue', Arial, sans-serif !important;
    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%) !important;
    min-height: 100vh;
    padding: 2rem 1rem !important;
}

/* Haupt-Container */
.contain {
    background: var(--bg-primary) !important;
    border-radius: var(--border-radius-lg) !important;
    box-shadow: var(--shadow-xl) !important;
    padding: 2rem !important;
    max-width: 1400px !important;
    margin: 0 auto !important;
}

/* =================================================================
   HEADER & TITLE
   ================================================================= */
.gradio-container h1 {
    background: linear-gradient(135deg, var(--bg-gradient-start), var(--bg-gradient-end));
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    background-clip: text;
    font-size: 2.5rem !important;
    font-weight: 800 !important;
    text-align: center !important;
    margin-bottom: 0.5rem !important;
    letter-spacing: -0.025em !important;
}

.gradio-container h1 + p {
    color: var(--text-secondary) !important;
    text-align: center !important;
    font-size: 1.125rem !important;
    margin-bottom: 2rem !important;
}

.gradio-container h1 {
    /* WICHTIG: Fallback-Farbe zuerst */
    color: #2d3748 !important;

    /* Dann Gradient-Effekt */
    background: linear-gradient(135deg, #667eea, #764ba2);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    background-clip: text;
}

/* Extra Fallback für Firefox */
@supports not (background-clip: text) {
    .gradio-container h1 {
        color: #667eea !important;
        background: none !important;
    }
}

/* =================================================================
   TABS
   ================================================================= */
.tabs {
    border: none !important;
    background: transparent !important;
    margin-bottom: 2rem !important;
}

.tab-nav {
    background: var(--bg-secondary) !important;
    border-radius: var(--border-radius) !important;
    padding: 0.5rem !important;
    display: flex !important;
    gap: 0.5rem !important;
    border: 1px solid var(--border-color) !important;
}

.tab-nav button {
    background: transparent !important;
    border: none !important;
    border-radius: var(--border-radius-sm) !important;
    padding: 0.75rem 1.5rem !important;
    font-weight: 600 !important;
    font-size: 1rem !important;
    color: var(--text-secondary) !important;
    transition: var(--transition) !important;
    cursor: pointer !important;
}

.tab-nav button:hover {
    background: var(--bg-primary) !important;
    color: var(--text-primary) !important;
    transform: translateY(-2px) !important;
}

.tab-nav button.selected {
    background: linear-gradient(135deg, var(--primary-color), var(--secondary-color)) !important;
    color: white !important;
    box-shadow: var(--shadow-md) !important;
}

/* =================================================================
   BUTTONS
   ================================================================= */
button, .gr-button {
    border-radius: var(--border-radius-sm) !important;
    font-weight: 600 !important;
    padding: 0.75rem 1.5rem !important;
    transition: var(--transition) !important;
    border: none !important;
    cursor: pointer !important;
    font-size: 0.95rem !important;
    box-shadow: var(--shadow-sm) !important;
}

button:hover, .gr-button:hover {
    transform: translateY(-2px) !important;
    box-shadow: var(--shadow-md) !important;
}

button:active, .gr-button:active {
    transform: translateY(0) !important;
}

/* Primary Button */
button[variant="primary"], .gr-button-primary {
    background: linear-gradient(135deg, var(--primary-color), var(--secondary-color)) !important;
    color: white !important;
}

button[variant="primary"]:hover, .gr-button-primary:hover {
    background: linear-gradient(135deg, var(--primary-hover), var(--secondary-color)) !important;
}

/* Save Button */
.save-button {
    background: linear-gradient(135deg, var(--success-color), #38b2ac) !important;
    color: white !important;
    font-size: 1.1rem !important;
    padding: 1rem 2rem !important;
    box-shadow: var(--shadow-lg) !important;
}

.save-button:hover {
    background: linear-gradient(135deg, var(--success-hover), #319795) !important;
    box-shadow: var(--shadow-xl) !important;
}

/* Reject/Remove Button */
.reject-button {
    background: linear-gradient(135deg, var(--danger-color), #fc8181) !important;
    color: white !important;
}

.reject-button:hover {
    background: linear-gradient(135deg, var(--danger-hover), #f56565) !important;
}

.reject-button:disabled {
    background: var(--bg-tertiary) !important;
    color: var(--text-tertiary) !important;
    cursor: not-allowed !important;
    opacity: 0.5 !important;
    transform: none !important;
}

/* Google Search Button */
.google-button {
    background: linear-gradient(135deg, var(--info-color), #63b3ed) !important;
    color: white !important;
}

.google-button:hover {
    background: linear-gradient(135deg, #3182ce, var(--info-color)) !important;
}

.google-button:disabled {
    background: var(--bg-tertiary) !important;
    color: var(--text-tertiary) !important;
    cursor: not-allowed !important;
    opacity: 0.5 !important;
    transform: none !important;
}

/* =================================================================
   CONTAINERS & CARDS
   ================================================================= */
.suggestion-container {
    background: var(--bg-secondary) !important;
    border: 1px solid var(--border-color) !important;
    border-radius: var(--border-radius) !important;
    padding: 1.5rem !important;
    margin: 1rem 0 !important;
    box-shadow: var(--shadow-sm) !important;
    transition: var(--transition) !important;
}

.suggestion-container:hover {
    box-shadow: var(--shadow-md) !important;
    transform: translateY(-2px) !important;
}

/* Info Box */
.suggestion-info {
    background: linear-gradient(135deg, #e6fffa 0%, #e0f2fe 100%) !important;
    border-left: 4px solid var(--info-color) !important;
    border-radius: var(--border-radius-sm) !important;
    padding: 1rem !important;
    margin: 1rem 0 !important;
    color: #0c4a6e !important;
    font-weight: 500 !important;
    box-shadow: var(--shadow-sm) !important;
}

/* Success Message */
.success-message {
    background: linear-gradient(135deg, #d1fae5 0%, #a7f3d0 100%) !important;
    border-left: 4px solid var(--success-color) !important;
    border-radius: var(--border-radius-sm) !important;
    padding: 1rem !important;
    margin: 0.5rem 0 !important;
    color: #064e3b !important;
    font-weight: 600 !important;
    box-shadow: var(--shadow-sm) !important;
    animation: slideInDown 0.3s ease-out !important;
}

@keyframes slideInDown {
    from {
        opacity: 0;
        transform: translateY(-20px);
    }
    to {
        opacity: 1;
        transform: translateY(0);
    }
}

/* =================================================================
   CHECKBOX GROUP & SELECTIONS
   ================================================================= */
.gradio-checkboxgroup {
    background: var(--bg-primary) !important;
    border-radius: var(--border-radius) !important;
}

.gradio-checkboxgroup label {
    background: var(--bg-secondary) !important;
    border: 2px solid var(--border-color) !important;
    border-radius: var(--border-radius-sm) !important;
    padding: 1rem 1.25rem !important;
    margin: 0.5rem 0 !important;
    transition: var(--transition) !important;
    cursor: pointer !important;
    display: flex !important;
    align-items: center !important;
    gap: 0.75rem !important;
}

.gradio-checkboxgroup label:hover {
    background: linear-gradient(135deg, #faf5ff 0%, #f3e8ff 100%) !important;
    border-color: var(--primary-color) !important;
    transform: translateX(4px) !important;
    box-shadow: var(--shadow-sm) !important;
}

.gradio-checkboxgroup input[type="checkbox"]:checked + span {
    background: linear-gradient(135deg, #ede9fe 0%, #ddd6fe 100%) !important;
    border-color: var(--primary-color) !important;
    font-weight: 600 !important;
    box-shadow: var(--shadow-md) !important;
}

.gradio-checkboxgroup input[type="checkbox"] {
    width: 1.25rem !important;
    height: 1.25rem !important;
    border: 2px solid var(--border-color) !important;
    border-radius: 4px !important;
    cursor: pointer !important;
}

.gradio-checkboxgroup input[type="checkbox"]:checked {
    background: linear-gradient(135deg, var(--primary-color), var(--secondary-color)) !important;
    border-color: var(--primary-color) !important;
}

/* =================================================================
   TEXT AREAS & INPUTS
   ================================================================= */
textarea, .gr-text-input, .gr-textbox {
    background: var(--bg-secondary) !important;
    border: 2px solid var(--border-color) !important;
    border-radius: var(--border-radius-sm) !important;
    padding: 1rem !important;
    color: var(--text-primary) !important;
    font-size: 0.95rem !important;
    line-height: 1.6 !important;
    transition: var(--transition) !important;
}

textarea:focus, .gr-text-input:focus, .gr-textbox:focus {
    outline: none !important;
    border-color: var(--primary-color) !important;
    box-shadow: 0 0 0 3px rgba(102, 126, 234, 0.1) !important;
}

/* =================================================================
   MEDIA DISPLAY (Images, Videos)
   ================================================================= */
.gr-html img {
    border-radius: var(--border-radius) !important;
    box-shadow: var(--shadow-lg) !important;
    transition: var(--transition) !important;
}

.gr-html img:hover {
    transform: scale(1.02) !important;
    box-shadow: var(--shadow-xl) !important;
}

.gr-html iframe {
    border-radius: var(--border-radius) !important;
    box-shadow: var(--shadow-lg) !important;
}

/* Media Container */
.gr-html > div {
    background: var(--bg-secondary) !important;
    border-radius: var(--border-radius) !important;
    padding: 1.5rem !important;
    margin: 1rem 0 !important;
    box-shadow: var(--shadow-md) !important;
}

.gr-html h4 {
    color: var(--text-primary) !important;
    font-weight: 600 !important;
    margin-bottom: 1rem !important;
    font-size: 1.1rem !important;
}

/* =================================================================
   RESPONSIVE DESIGN
   ================================================================= */
@media (max-width: 768px) {
    .gradio-container {
        padding: 1rem 0.5rem !important;
    }

    .contain {
        padding: 1rem !important;
        border-radius: var(--border-radius) !important;
    }

    .gradio-container h1 {
        font-size: 1.875rem !important;
    }

    .tab-nav {
        flex-direction: column !important;
    }

    .tab-nav button {
        width: 100% !important;
    }

    button, .gr-button {
        width: 100% !important;
        padding: 0.875rem 1rem !important;
    }

    .gradio-checkboxgroup label {
        padding: 0.875rem 1rem !important;
    }
}

/* =================================================================
   SCROLLBAR STYLING
   ================================================================= */
::-webkit-scrollbar {
    width: 10px;
    height: 10px;
}

::-webkit-scrollbar-track {
    background: var(--bg-secondary);
    border-radius: 10px;
}

::-webkit-scrollbar-thumb {
    background: linear-gradient(135deg, var(--primary-color), var(--secondary-color));
    border-radius: 10px;
}

::-webkit-scrollbar-thumb:hover {
    background: linear-gradient(135deg, var(--primary-hover), var(--secondary-color));
}

/* =================================================================
   LOADING & ANIMATIONS
   ================================================================= */
.loading {
    animation: pulse 2s cubic-bezier(0.4, 0, 0.6, 1) infinite;
}

@keyframes pulse {
    0%, 100% {
        opacity: 1;
    }
    50% {
        opacity: 0.5;
    }
}

.fade-in {
    animation: fadeIn 0.3s ease-in;
}

@keyframes fadeIn {
    from {
        opacity: 0;
    }
    to {
        opacity: 1;
    }
}

/* =================================================================
   TOOLTIPS & HINTS
   ================================================================= */
[title]:hover::after {
    content: attr(title);
    position: absolute;
    bottom: 100%;
    left: 50%;
    transform: translateX(-50%);
    background: var(--text-primary);
    color: var(--bg-primary);
    padding: 0.5rem 1rem;
    border-radius: var(--border-radius-sm);
    font-size: 0.875rem;
    white-space: nowrap;
    box-shadow: var(--shadow-md);
    z-index: 1000;
}

/* =================================================================
   ACCESSIBILITY
   ================================================================= */
*:focus {
    outline: 2px solid var(--primary-color) !important;
    outline-offset: 2px !important;
}

button:focus, .gr-button:focus {
    outline: 3px solid var(--primary-color) !important;
    outline-offset: 2px !important;
}

/* High contrast mode support */
@media (prefers-contrast: high) {
    :root {
        --border-color: #000000;
        --text-primary: #000000;
    }
}

/* Reduced motion support */
@media (prefers-reduced-motion: reduce) {
    * {
        animation-duration: 0.01ms !important;
        animation-iteration-count: 1 !important;
        transition-duration: 0.01ms !important;
    }
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

fav_films, fav_albums, fav_books = load_favorites_to_suggestions()

# Choices aus current_suggestions erstellen (jetzt mit Favoriten!)
initial_film_choices = get_initial_choices(current_suggestions["films"])
initial_album_choices = get_initial_choices(current_suggestions["albums"])
initial_book_choices = get_initial_choices(current_suggestions["books"])


def create_custom_theme() -> gr.Theme:
    """
    Erstellt ein benutzerdefiniertes Gradio Theme mit modernem Design.

    Returns:
        Konfiguriertes Gradio Theme
    """
    # from utils.logging_config import get_logger

    # logger = get_logger(__name__)
    logger.info("Erstelle benutzerdefiniertes Theme")

    theme = gr.themes.Soft(
        primary_hue="purple",
        secondary_hue="blue",
        neutral_hue="slate",
        font=[
            gr.themes.GoogleFont("Inter"),
            "ui-sans-serif",
            "system-ui",
            "sans-serif",
        ],
        font_mono=[
            gr.themes.GoogleFont("IBM Plex Mono"),
            "ui-monospace",
            "Consolas",
            "monospace",
        ],
    ).set(
        # Buttons
        button_primary_background_fill="linear-gradient(135deg, #667eea 0%, #764ba2 100%)",
        button_primary_background_fill_hover="linear-gradient(135deg, #5568d3 0%, #6a3f8f 100%)",
        button_primary_text_color="white",
        button_primary_border_color="transparent",
        # Inputs
        input_background_fill="*neutral_50",
        input_border_color="*neutral_300",
        input_border_width="2px",
        # Containers
        background_fill_primary="white",
        background_fill_secondary="*neutral_50",
        # Borders
        block_border_width="1px",
        block_border_color="*neutral_200",
        block_radius="12px",
        block_shadow="*shadow_md",
    )

    return theme


def create_statistics_display(films_count: int, albums_count: int, books_count: int) -> str:
    """
    Erstellt eine Statistik-Anzeige mit aktuellen Zahlen.

    Args:
        films_count: Anzahl Filmvorschläge
        albums_count: Anzahl Albumvorschläge
        books_count: Anzahl Buchvorschläge

    Returns:
        HTML-String für Statistik-Display
    """
    total = films_count + albums_count + books_count

    return f"""
    <div style="
        display: grid;
        grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
        gap: 1rem;
        margin: 2rem 0;
    ">
        <div style="
            background: linear-gradient(135deg, #e6fffa 0%, #e0f2fe 100%);
            padding: 1.5rem;
            border-radius: 12px;
            text-align: center;
            box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1);
        ">
            <div style="font-size: 2.5rem; font-weight: 800; color: #0c4a6e;">
                {films_count}
            </div>
            <div style="color: #0c4a6e; font-weight: 600; margin-top: 0.5rem;">
                🎬 Filme
            </div>
        </div>

        <div style="
            background: linear-gradient(135deg, #fef3c7 0%, #fde68a 100%);
            padding: 1.5rem;
            border-radius: 12px;
            text-align: center;
            box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1);
        ">
            <div style="font-size: 2.5rem; font-weight: 800; color: #78350f;">
                {albums_count}
            </div>
            <div style="color: #78350f; font-weight: 600; margin-top: 0.5rem;">
                🎵 Alben
            </div>
        </div>

        <div style="
            background: linear-gradient(135deg, #ddd6fe 0%, #c4b5fd 100%);
            padding: 1.5rem;
            border-radius: 12px;
            text-align: center;
            box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1);
        ">
            <div style="font-size: 2.5rem; font-weight: 800; color: #3730a3;">
                {books_count}
            </div>
            <div style="color: #3730a3; font-weight: 600; margin-top: 0.5rem;">
                📚 Bücher
            </div>
        </div>

        <div style="
            background: linear-gradient(135deg, #d1fae5 0%, #a7f3d0 100%);
            padding: 1.5rem;
            border-radius: 12px;
            text-align: center;
            box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1);
        ">
            <div style="font-size: 2.5rem; font-weight: 800; color: #064e3b;">
                {total}
            </div>
            <div style="color: #064e3b; font-weight: 600; margin-top: 0.5rem;">
                ✨ Gesamt
            </div>
        </div>
    </div>
    """


def create_header_section() -> None:
    """
    Erstellt einen ansprechenden Header-Bereich mit Titel und Beschreibung.

    Returns:
        None: Komponenten werden direkt in Gradio-Block erstellt
    """
    gr.HTML(
        """
        <div style="text-align: center; margin-bottom: 2rem;">
            <h1 style="
                font-size: 2.5rem;
                font-weight: 800;
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                -webkit-background-clip: text;
                -webkit-text-fill-color: transparent;
                background-clip: text;
                color: #667eea;  /* Fallback! */
            ">
                🎬📀📚 Bibliothek-Empfehlungen
            </h1>
        </div>
        """
    )

    gr.Markdown(
        """
        ### Entdecken Sie verfügbare Medien in der Stadtbibliothek Köln!

        Intelligente Empfehlungen aus kuratierten Premium-Listen mit Live-Verfügbarkeitscheck,
        KI-gestützter Suche und visuellen Medien.
        """,
        elem_classes=["header-section"],
    )


def create_info_card(icon: str, title: str, description: str) -> str:
    """
    Erstellt eine HTML-Info-Karte.

    Args:
        icon: Emoji-Icon
        title: Titel der Karte
        description: Beschreibungstext

    Returns:
        HTML-String für die Info-Karte

    Example:
        >>> card = create_info_card("🎬", "Filme", "Premium-Auswahl")
        >>> gr.HTML(card)
    """
    return f"""
    <div style="
        background: linear-gradient(135deg, #faf5ff 0%, #f3e8ff 100%);
        border-left: 4px solid #667eea;
        border-radius: 12px;
        padding: 1.5rem;
        margin: 1rem 0;
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1);
    ">
        <div style="display: flex; align-items: center; gap: 1rem;">
            <span style="font-size: 2rem;">{icon}</span>
            <div>
                <h3 style="margin: 0; color: #2d3748; font-weight: 700;">
                    {title}
                </h3>
                <p style="margin: 0.25rem 0 0 0; color: #4a5568;">
                    {description}
                </p>
            </div>
        </div>
    </div>
    """


def create_footer_section() -> None:
    """
    Erstellt einen informativen Footer-Bereich.

    Returns:
        None: Komponenten werden direkt erstellt
    """
    gr.Markdown(
        """
        ---

        ### ℹ️ Hinweise

        - 🔄 **Live-Verfügbarkeit**: Die Verfügbarkeit wird in Echtzeit geprüft
        - 🏷️ **Quellen-Emojis**: Zeigen die Herkunft jeder Empfehlung
        - 💎 **Personalisiert**: Basierend auf Ihrem MP3-Archiv
        - 🔍 **KI-Suche**: Powered by Groq AI & DuckDuckGo

        **🌐 Katalog**: [Stadtbibliothek Köln](https://katalog.stbib-koeln.de)

        *Entwickelt mit ❤️ für Bibliotheksliebhaber und Medienentdecker*
        """,
        elem_classes=["footer-section"],
    )


def create_loading_spinner() -> str:
    """
    Erstellt einen animierten Lade-Spinner.

    Returns:
        HTML-String für Spinner
    """
    return """
    <div style="
        display: flex;
        justify-content: center;
        align-items: center;
        padding: 2rem;
    ">
        <div style="
            border: 4px solid #f3f4f6;
            border-top: 4px solid #667eea;
            border-radius: 50%;
            width: 40px;
            height: 40px;
            animation: spin 1s linear infinite;
        "></div>
    </div>
    <style>
        @keyframes spin {
            0% { transform: rotate(0deg); }
            100% { transform: rotate(360deg); }
        }
    </style>
    """


def create_empty_state(category: str) -> str:
    """
    Erstellt eine ansprechende "Empty State" Anzeige.

    Args:
        category: Kategorie ('films', 'albums', 'books')

    Returns:
        HTML-String für Empty State
    """
    icons = {"films": "🎬", "albums": "🎵", "books": "📚"}

    labels = {"films": "Filme", "albums": "Alben", "books": "Bücher"}

    icon = icons.get(category, "📦")
    label = labels.get(category, "Medien")

    return f"""
    <div style="
        text-align: center;
        padding: 4rem 2rem;
        background: linear-gradient(135deg, #faf5ff 0%, #f3e8ff 100%);
        border-radius: 16px;
        margin: 2rem 0;
    ">
        <div style="font-size: 4rem; margin-bottom: 1rem;">
            {icon}
        </div>
        <h3 style="
            color: #2d3748;
            font-weight: 700;
            margin-bottom: 0.5rem;
        ">
            Keine {label} gefunden
        </h3>
        <p style="color: #718096; margin-bottom: 2rem;">
            Klicken Sie auf "Neue {label} vorschlagen" um Empfehlungen zu erhalten
        </p>
        <div style="
            display: inline-block;
            padding: 0.5rem 1rem;
            background: white;
            border-radius: 8px;
            color: #667eea;
            font-weight: 600;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        ">
            💡 Tipp: Wählen Sie mehrere Titel aus um sie zu entfernen
        </div>
    </div>
    """


def create_badge(text: str, color: str = "blue") -> str:
    """
    Erstellt ein kleines Badge/Label.

    Args:
        text: Badge-Text
        color: Farbe (blue, green, red, purple, yellow)

    Returns:
        HTML-String für Badge
    """
    colors = {
        "blue": "linear-gradient(135deg, #3b82f6 0%, #2563eb 100%)",
        "green": "linear-gradient(135deg, #10b981 0%, #059669 100%)",
        "red": "linear-gradient(135deg, #ef4444 0%, #dc2626 100%)",
        "purple": "linear-gradient(135deg, #8b5cf6 0%, #7c3aed 100%)",
        "yellow": "linear-gradient(135deg, #f59e0b 0%, #d97706 100%)",
    }

    bg = colors.get(color, colors["blue"])

    return f"""
    <span style="
        display: inline-block;
        padding: 0.25rem 0.75rem;
        background: {bg};
        color: white;
        border-radius: 9999px;
        font-size: 0.875rem;
        font-weight: 600;
        margin: 0.25rem;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
    ">
        {text}
    </span>
    """


def create_progress_bar(current: int, total: int) -> str:
    """
    Erstellt einen Fortschrittsbalken.

    Args:
        current: Aktueller Wert
        total: Gesamtwert

    Returns:
        HTML-String für Fortschrittsbalken
    """
    percentage = int((current / total * 100)) if total > 0 else 0

    return f"""
    <div style="margin: 1rem 0;">
        <div style="
            display: flex;
            justify-content: space-between;
            margin-bottom: 0.5rem;
            color: #4a5568;
            font-weight: 600;
        ">
            <span>{current} von {total}</span>
            <span>{percentage}%</span>
        </div>
        <div style="
            background: #e2e8f0;
            border-radius: 9999px;
            height: 8px;
            overflow: hidden;
        ">
            <div style="
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                height: 100%;
                width: {percentage}%;
                transition: width 0.3s ease;
                border-radius: 9999px;
            "></div>
        </div>
    </div>
    """


def create_tooltip_icon(text: str, tooltip: str) -> str:
    """
    Erstellt ein Icon mit Tooltip.

    Args:
        text: Anzuzeigender Text/Icon
        tooltip: Tooltip-Text

    Returns:
        HTML-String mit Tooltip
    """
    return f"""
    <span style="
        position: relative;
        cursor: help;
        border-bottom: 2px dotted #cbd5e0;
    " title="{tooltip}">
        {text}
    </span>
    """


with gr.Blocks(theme=create_custom_theme(), css=css, title="Bibliothek-Empfehlungen") as demo:
    # Header
    create_header_section()

    # Statistiken
    stats_html = gr.HTML(value=create_statistics_display(len(initial_films), len(initial_albums), len(initial_books)))

    # Info-Karten (optional)
    with gr.Row():
        gr.HTML(create_info_card("🎬", "Premium-Filme", "BBC, FBW & Oscar-Gewinner"))
        gr.HTML(create_info_card("🎵", "Kuratierte Musik", "Radio Eins, Oscar & Personalisiert"))
        gr.HTML(create_info_card("📚", "Beste Bücher", "NYT Kanon & Top-Ratgeber"))

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
                # TODO: diese Anzahl und die Inhalte sollten dynamisch sein und sich anpassen an die Zahl an Quellen
                #  und dem eingestellten Parameter. gilt auch für CDs und DVDs
                label="Empfohlene Bücher (balanciert: 4 NYT Kanon, 4 Ratgeber)",
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
    with gr.Tab("⭐ Favoriten"):
        gr.Markdown(
            """
            ### 🔍 Individuelle Mediensuche

            Suchen Sie gezielt nach spezifischen Medien oder entdecken Sie Werke
            Ihrer Lieblingskünstler. Gefundene Medien werden automatisch zu den
            entsprechenden Tabs hinzugefügt und als Favoriten gespeichert.
            """
        )

        with gr.Row():
            with gr.Column(scale=2):
                fav_author = gr.Textbox(
                    label="👤 Autor / Künstler / Regisseur",
                    placeholder="z.B. Stephen King, Radiohead, Christopher Nolan",
                    info="Pflichtfeld wenn kein Titel angegeben",
                )

            with gr.Column(scale=2):
                fav_title = gr.Textbox(
                    label="📝 Titel des Mediums (optional)",
                    placeholder="z.B. Es, OK Computer, Inception",
                    info="Leer lassen für Künstler-Suche",
                )

            with gr.Column(scale=1):
                fav_media_type = gr.Dropdown(
                    label="📦 Medienart", choices=["DVD", "CD", "Buch"], value="DVD", info="Art des Mediums"
                )

        with gr.Row():
            fav_search_btn = gr.Button("🔍 Medium suchen", variant="primary", size="lg")

        fav_result = gr.Textbox(label="📊 Suchergebnis", lines=5, interactive=False)

        fav_success_msg = gr.HTML(value="", visible=False, elem_classes=["success-message"])

        gr.Markdown("---")

        with gr.Row():
            show_favorites_btn = gr.Button("📋 Gespeicherte Favoriten anzeigen", variant="secondary")

        saved_favorites_display = gr.Markdown(value="", visible=False)

        gr.Markdown(
            """
            ---

            ### 💡 Tipps

            - **Spezifische Suche**: Geben Sie Titel + Autor an für ein bestimmtes Medium
            - **Künstler-Suche**: Nur Autor angeben → findet bis zu 2 verfügbare Medien
            - **Automatische Integration**: Gefundene Medien erscheinen oben in den entsprechenden Tabs
            - **Favoriten-Speicherung**: 💾 Erfolgreich gefundene Medien werden automatisch gespeichert
            - **Beim nächsten Start**: ⭐ Gespeicherte Favoriten werden automatisch geladen und geprüft
            - **Intelligentes Tracking**:
              - 📅 Entliehene Medien werden automatisch überwacht
              - ⚫ Nicht gefundene Medien für 1 Jahr gespeichert
              - 🔄 Automatische Neuprüfung nach Rückgabe

            **Beispiele:**
            - Film: `Christopher Nolan` + `Inception` + `DVD`
            - Musik: `Radiohead` + (leer) + `CD` → findet 2 verfügbare Alben
            - Buch: `Stephen King` + `Es` + `Buch`
            """
        )

        # Event Handler
        fav_search_btn.click(
            fn=search_favorite_medium,
            inputs=[fav_author, fav_title, fav_media_type],
            outputs=[fav_result, fav_success_msg, film_checkbox, album_checkbox, book_checkbox],
        ).then(
            fn=lambda x: gr.update(visible=bool(x), value=x) if x else gr.update(visible=False),
            inputs=[fav_success_msg],
            outputs=[fav_success_msg],
        )

        show_favorites_btn.click(fn=show_saved_favorites, outputs=[saved_favorites_display]).then(
            fn=lambda: gr.update(visible=True), outputs=[saved_favorites_display]
        )

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

    # Footer am Ende
    create_footer_section()


if __name__ == "__main__":
    demo.launch()
