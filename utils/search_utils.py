#!/usr/bin/env python3
"""
Such- und Zusammenfassungs-Utilities für Medien-Empfehlungen
MIT YouTube-Trailer, Cover-Images und visueller Integration
"""

import os
import re
from typing import Optional, Dict, Any, List, Tuple
import requests
from duckduckgo_search import DDGS
from groq import Groq
from utils.logging_config import get_logger

logger = get_logger(__name__)


def search_youtube_trailer(title: str, author: Optional[str] = None) -> Optional[str]:
    """
    Sucht nach einem YouTube-Trailer für einen Film.

    Args:
        title: Filmtitel
        author: Regisseur (optional)

    Returns:
        YouTube Video-ID oder None

    Example:
        >>> video_id = search_youtube_trailer("Der Pate", "Francis Ford Coppola")
        >>> print(f"https://www.youtube.com/watch?v={video_id}")
    """
    try:
        # Suchbegriff erstellen
        search_term = f"{title} official trailer"
        if author:
            search_term += f" {author}"

        logger.debug(f"Suche YouTube-Trailer: '{search_term}'")

        with DDGS() as ddgs:
            # Suche nach YouTube-Videos
            video_results = list(ddgs.text(f"{search_term} site:youtube.com", max_results=5))

            # Extrahiere YouTube Video-ID
            for result in video_results:
                url = result.get("href", "")

                # Pattern für YouTube URLs
                patterns = [
                    r"youtube\.com/watch\?v=([a-zA-Z0-9_-]{11})",
                    r"youtu\.be/([a-zA-Z0-9_-]{11})",
                    r"youtube\.com/embed/([a-zA-Z0-9_-]{11})",
                ]

                for pattern in patterns:
                    match = re.search(pattern, url)
                    if match:
                        video_id = match.group(1)
                        logger.debug(f"YouTube Video-ID gefunden: {video_id}")
                        return video_id

        logger.debug("Kein YouTube-Trailer gefunden")
        return None

    except Exception as e:
        logger.error(f"Fehler bei YouTube-Suche: {e}")
        return None


def search_itunes_cover(title: str, author: Optional[str] = None) -> Optional[str]:
    """
    Sucht nach einem Album-Cover mit der iTunes Search API.

    Args:
        title: Albumtitel
        author: Künstler (optional)

    Returns:
        URL des Covers (600x600 px) oder None
    """
    try:
        search_term = title
        if author:
            search_term += f" {author}"

        url = "https://itunes.apple.com/search"
        params = {"term": search_term, "media": "music", "entity": "album", "limit": 1}

        logger.debug(f"Suche iTunes-Cover für: '{search_term}'")
        response = requests.get(url, params=params, timeout=5)

        if response.status_code == 200:
            data = response.json()
            if data.get("resultCount", 0) > 0:
                # Nimm das erste Ergebnis
                result = data["results"][0]
                # Hole das größte verfügbare Cover (meist artworkUrl100)
                # Ersetze 100x100 mit 600x600 für bessere Qualität
                cover_url = result.get("artworkUrl100", "")
                if cover_url:
                    cover_600 = cover_url.replace("100x100bb.jpg", "600x600bb.jpg")
                    logger.debug(f"iTunes-Cover gefunden: {cover_600[:50]}...")
                    return cover_600

        return None
    except Exception as e:
        logger.error(f"Fehler bei iTunes-Suche: {e}")
        return None


def search_cover_image(title: str, author: Optional[str] = None, media_type: str = "film") -> Optional[str]:  # noqa: C901
    """
    Sucht nach einem Cover-Image für ein Medium.

    Versucht bei Alben zuerst iTunes, sonst DuckDuckGo Bildsuche.

    Args:
        title: Titel des Mediums
        author: Autor/Künstler/Regisseur (optional)
        media_type: Art des Mediums ('film', 'album', 'book')

    Returns:
        URL des Cover-Images oder None

    Example:
        >>> cover_url = search_cover_image("OK Computer", "Radiohead", "album")
        >>> print(f"Album-Cover: {cover_url}")
    """
    # 1. Speziell für Alben: iTunes zuerst versuchen
    if media_type == "album":
        itunes_url = search_itunes_cover(title, author)
        if itunes_url:
            return itunes_url

    # 2. Fallback: DuckDuckGo Bildsuche
    try:
        # Suchbegriff erstellen
        if media_type == "film":
            search_term = f"{title} movie poster"
        elif media_type == "album":
            search_term = f"{title} album cover"
        elif media_type == "book":
            search_term = f"{title} book cover"
        else:
            search_term = f"{title} cover"

        if author:
            search_term += f" {author}"

        logger.debug(f"Suche DuckDuckGo-Cover: '{search_term}'")

        with DDGS() as ddgs:
            # Bildsuche
            image_results = list(ddgs.images(search_term, max_results=3))

            if image_results:
                # Nimm das erste Ergebnis
                image_url = image_results[0].get("image")
                if image_url:
                    logger.debug(f"DuckDuckGo-Cover gefunden: {image_url[:50]}...")
                    return image_url

        logger.debug("Kein Cover-Image gefunden")
        return None

    except Exception as e:
        logger.error(f"Fehler bei Cover-Suche: {e}")
        return None


def search_media_info(title: str, author: Optional[str] = None, media_type: str = "film") -> List[Dict[str, Any]]:
    """
    Sucht Informationen über ein Medium mit DuckDuckGo.

    Erstellt einen optimierten Suchbegriff basierend auf Medientyp und führt eine DuckDuckGo-Suche durch.

    Args:
        title: Titel des Mediums
        author: Autor/Regisseur/Künstler (optional)
        media_type: Art des Mediums ('film', 'album', 'book')

    Returns:
        Liste von Suchergebnissen mit Schlüsseln:
            - "title" (str): Titel des Suchergebnisses
            - "body" (str): Beschreibungstext
            - "href" (str): URL des Ergebnisses

    Example:
        >>> results = search_media_info("Der Pate", "Francis Ford Coppola", "film")
        >>> print(results[0].get("title"))
        'Der Pate – Wikipedia'
    """
    try:
        # Suchbegriff erstellen
        if media_type == "film":
            search_term = f"{title}"
            if author:
                search_term += f" {author} film"
            else:
                search_term += " film"
        elif media_type == "album":
            search_term = f"{title}"
            if author:
                search_term += f" {author} album"
            else:
                search_term += " album musik"
        elif media_type == "book":
            search_term = f"{title}"
            if author:
                search_term += f" {author} buch"
            else:
                search_term += " buch"
        else:
            search_term = f"{title} {author}" if author else title

        logger.debug(f"Suche nach: '{search_term}'")

        with DDGS() as ddgs:
            results = list(ddgs.text(search_term, max_results=5))

        return results

    except Exception as e:
        print(f"DEBUG: Fehler bei der Suche: {e}")
        return []


def summarize_with_groq(
    search_results: List[Dict[str, Any]], title: str, author: Optional[str] = None, media_type: str = "film"
) -> str:
    """
    Erstellt eine kurze Zusammenfassung mit der Groq API.

    Nutzt ein moonshotai/kimi-k2-instruct-0905 über die Groq API, um aus
    Suchergebnissen eine prägnante 2-3 Sätze Zusammenfassung zu erstellen.

    Args:
        search_results: Suchergebnisse von DuckDuckGo
        title: Titel des Mediums
        author: Autor/Regisseur/Künstler (optional)
        media_type: Art des Mediums ('film', 'album', 'book')

    Returns:
        2-3 Sätze Zusammenfassung auf Deutsch

    Note:
        Benötigt GROQ_API_KEY Umgebungsvariable

    Example:
        >>> summary = summarize_with_groq(results, "Der Pate", "Coppola", "film")
        >>> print(summary)
        'Der Pate ist ein Mafia-Drama von 1972...'
    """
    try:
        api_key = os.getenv("GROQ_API_KEY")
        if not api_key:
            return "Groq API Key nicht gefunden. Bitte GROQ_API_KEY Umgebungsvariable setzen."

        client = Groq(api_key=api_key)

        # Suchergebnisse zu Text zusammenfassen
        search_text = ""
        for i, result in enumerate(search_results[:3]):
            search_text += f"Ergebnis {i + 1}: {result.get('title', '')} - {result.get('body', '')}\n\n"

        # Medientyp-spezifischer Prompt
        if media_type == "film":
            media_german = "Film"
            details = "Handlung, Genre, Erscheinungsjahr"
        elif media_type == "album":
            media_german = "Album"
            details = "Musikstil, Erscheinungsjahr, bekannte Songs"
        elif media_type == "book":
            media_german = "Buch"
            details = "Inhalt, Genre, Erscheinungsjahr"
        else:
            media_german = "Medium"
            details = "wichtige Informationen"

        prompt = f"""Basierend auf den folgenden Suchergebnissen, schreibe GENAU 2-3 kurze Sätze auf Deutsch über den {media_german} "{title}"{f' von {author}' if author else ''}.

Konzentriere dich auf: {details}. Sei präzise und informativ.

Suchergebnisse:
{search_text}

Antwort (maximal 3 Sätze auf Deutsch):"""

        response = client.chat.completions.create(
            messages=[{"role": "user", "content": prompt}],
            model="moonshotai/kimi-k2-instruct-0905",
            temperature=0.3,
            max_tokens=150,
        )

        summary = response.choices[0].message.content.strip()
        return summary

    except Exception as e:
        logger.error(f"Fehler bei Groq API: {e}")
        return f"Fehler beim Erstellen der Zusammenfassung: {str(e)}"


def get_media_summary(title: str, author: Optional[str] = None, media_type: str = "film") -> Dict[str, Any]:
    """
    Kombiniert Suche, Zusammenfassung und visuelle Medien.

    Hauptfunktion, die alle Such- und Zusammenfassungsfunktionen kombiniert
    und ein umfassendes Ergebnis mit Text, Trailer und Cover zurückgibt.

    Args:
        title: Titel des Mediums
        author: Autor/Regisseur/Künstler (optional)
        media_type: Art des Mediums ('film', 'album', 'book')

    Returns:
        Dictionary mit:
            - summary (str): Textzusammenfassung (1-2 Sätze)
            - youtube_id (str|None): YouTube Video-ID (nur bei Filmen)
            - cover_url (str|None): URL des Cover-Images

    Example:
        >>> result = get_media_summary("Mulholland Drive", "David Lynch", "film")
        >>> print(result['summary'])
        >>> if result['youtube_id']:
        ...     print(f"Trailer: https://youtube.com/watch?v={result['youtube_id']}")
        >>> if result['cover_url']:
        ...     print(f"Cover: {result['cover_url']}")
    """
    result = {"summary": "", "youtube_id": None, "cover_url": None}

    # Textsuche und Zusammenfassung
    search_results = search_media_info(title, author, media_type)

    if not search_results:
        result["summary"] = f"Keine Informationen zu '{title}' gefunden."
    else:
        result["summary"] = summarize_with_groq(search_results, title, author, media_type)

    # Für Filme: YouTube-Trailer suchen
    if media_type == "film":
        result["youtube_id"] = search_youtube_trailer(title, author)

    # Cover-Image suchen (für alle Medientypen)
    result["cover_url"] = search_cover_image(title, author, media_type)

    return result


def extract_title_and_author(display_text: str) -> Tuple[str, Optional[str]]:
    """
    Extrahiert Titel und Autor aus dem Anzeige-Text.

    Parst formatierte Display-Strings aus der GUI und trennt
    Titel und Autor am " - " Separator.

    Args:
        display_text: Text im Format "Titel - Autor" oder nur "Titel"

    Returns:
        Tuple mit (title, author)
            - title (str): Extrahierter Titel
            - author (str | None): Extrahierter Autor oder None

    Example:
        >>> extract_title_and_author("Der Pate - Francis Ford Coppola")
        ('Der Pate', 'Francis Ford Coppola')
        >>> extract_title_and_author("Standalone Film")
        ('Standalone Film', None)
    """
    if " - " in display_text:
        parts = display_text.split(" - ", 1)
        return parts[0].strip(), parts[1].strip()
    else:
        return display_text.strip(), None
