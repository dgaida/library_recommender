#!/usr/bin/env python3
"""
Buch-Datenquelle: New York Times Kanon des 21. Jahrhunderts

Lädt und verarbeitet Buchempfehlungen vom NYT-Kanon.
"""

import os
import requests
from bs4 import BeautifulSoup
from typing import List, Dict, Any

from utils.logging_config import get_logger
from utils.sources import SOURCE_NYT_CANON

logger = get_logger(__name__)

DATA_DIR = os.path.join(os.path.dirname(__file__), "..", "data")
os.makedirs(DATA_DIR, exist_ok=True)
BOOKS_FILE = os.path.join(DATA_DIR, "books.json")

URL = "https://www.die-besten-aller-zeiten.de/buecher/kanon/new-york-times-21-jahrhundert.html"


def fetch_books_from_site() -> List[Dict[str, Any]]:
    """
    Holt die Liste der 100 Bücher vom NYT-Kanon von der Webseite.

    Parst die HTML-Seite und extrahiert Buch-Titel, Autoren und
    Beschreibungen aus Accordion-Links.

    Returns:
        Liste von Büchern mit Schlüsseln:
            - title: Buchtitel
            - author: Autor/Autorin
            - description: Beschreibungstext
            - source: Quellen-Bezeichnung

    Raises:
        requests.RequestException: Bei Netzwerkproblemen

    Example:
        >>> books = fetch_books_from_site()
        >>> print(books[0]['title'])
        'Meine geniale Freundin'
        >>> print(books[0]['author'])
        'Elena Ferrante'
    """
    logger.info(f"Lade Webseite {URL}...")

    try:
        response = requests.get(URL, headers={"User-Agent": "Mozilla/5.0"}, timeout=15)
        response.raise_for_status()
    except requests.RequestException as e:
        logger.error(f"Fehler beim Laden der Webseite: {e}")
        raise

    soup = BeautifulSoup(response.text, "html.parser")
    books: List[Dict[str, Any]] = []

    # Jeder Titel steckt in einem <a class="accordionlink"> Tag
    links = soup.select("a.accordionlink")
    logger.info(f"Gefunden {len(links)} Buch-Einträge")

    for link in links:
        raw_text: str = link.get_text(strip=True)

        # Nummer entfernen (z.B. "1. Elena Ferrante: Meine geniale Freundin")
        if "." in raw_text.split()[0]:
            raw_text = " ".join(raw_text.split()[1:])

        # Split nach erstem ":" → Autor und Titel
        if ":" in raw_text:
            author, title = raw_text.split(":", 1)
            author = author.strip()
            title = title.strip()
        else:
            author, title = "", raw_text

        # Beschreibung finden: steht im nächsten <div class="accordionarea">
        accordion_div = link.find_next("div", class_="accordionarea")
        description: str = ""
        if accordion_div:
            para = accordion_div.find("div", class_="paragraph")
            if para:
                description = para.get_text(" ", strip=True)

        books.append({"title": title, "author": author, "description": description, "source": SOURCE_NYT_CANON})

    logger.info(f"Extrahiert {len(books)} Bücher")
    return books
