#!/usr/bin/env python3
"""
IMDb Top 250 Filme – Extraktion der Filmdaten.

Dieses Skript liest die IMDb-Top-250-Seite aus, parst die JSON-LD-Daten
im HTML-Quelltext und extrahiert Informationen zu Filmen wie Titel, Bewertung,
Anzahl der Bewertungen, Genre, Dauer und URL.

Autor: ChatGPT
Version: 1.0
"""

import requests
from bs4 import BeautifulSoup
import json
import os
import time
from typing import List, Dict, Any

from utils.io import DATA_DIR
from utils.logging_config import get_logger

logger = get_logger(__name__)

IMDB_TOP250_URL = "https://www.imdb.com/chart/top"


def fetch_imdb_top250(delay: float = 1.0) -> List[Dict[str, Any]]:
    """
    Ruft die IMDb Top 250 Filme ab, indem die JSON-LD-Daten aus dem HTML-Quelltext
    extrahiert und in Python-Objekte umgewandelt werden.

    Args:
        delay: Wartezeit (Sekunden) nach dem Abruf (default: 1.0)

    Returns:
        Liste von Dictionaries mit Schlüsseln:
            - title: Titel des Films
            - alternate_name: Alternativtitel (falls vorhanden)
            - description: Kurzbeschreibung
            - rating: Durchschnittliche Bewertung
            - rating_count: Anzahl der Bewertungen
            - genre: Filmgenre
            - duration: Dauer im ISO-8601-Format
            - url: IMDb-Link zum Film
            - image: Poster-URL

    Raises:
        requests.RequestException: Bei Netzwerkfehlern
        json.JSONDecodeError: Falls die JSON-LD-Daten fehlerhaft sind
    """
    logger.info(f"Lade IMDb Top 250 von {IMDB_TOP250_URL}")

    headers = {"User-Agent": "Mozilla/5.0 (compatible; IMDbScraper/1.0)"}

    try:
        response = requests.get(IMDB_TOP250_URL, headers=headers, timeout=15)
        response.raise_for_status()
    except requests.RequestException as e:
        logger.error(f"Fehler beim Laden der IMDb-Seite: {e}")
        raise

    soup = BeautifulSoup(response.text, "html.parser")
    json_ld_tag = soup.find("script", {"type": "application/ld+json"})

    if not json_ld_tag:
        logger.error("Keine JSON-LD-Daten im HTML gefunden.")
        return []

    try:
        data = json.loads(json_ld_tag.string)
    except json.JSONDecodeError as e:
        logger.error(f"Fehler beim Parsen der JSON-LD-Daten: {e}")
        raise

    if "itemListElement" not in data:
        logger.error("Unerwartete JSON-Struktur. 'itemListElement' fehlt.")
        return []

    films: List[Dict[str, Any]] = []

    for entry in data["itemListElement"]:
        item = entry.get("item", {})
        rating_data = item.get("aggregateRating", {})

        film_info = {
            "title": item.get("name"),
            "alternate_name": item.get("alternateName", ""),
            "description": item.get("description", ""),
            "rating": rating_data.get("ratingValue"),
            "rating_count": rating_data.get("ratingCount"),
            "genre": item.get("genre"),
            "duration": item.get("duration"),
            "url": item.get("url"),
            "image": item.get("image"),
        }
        films.append(film_info)

    logger.info(f"✅ {len(films)} Filme erfolgreich extrahiert.")
    time.sleep(delay)

    return films


def save_imdb_top250_to_json(filename: str = "imdb_top250.json") -> None:
    """
    Lädt die IMDb Top 250 Filme und speichert sie als JSON-Datei im data-Verzeichnis.

    Args:
        filename: Name der Ausgabedatei (default: "imdb_top250.json")

    Raises:
        IOError: Wenn beim Schreiben der Datei ein Fehler auftritt
    """
    films = fetch_imdb_top250()
    output_path = os.path.join(DATA_DIR, filename)

    try:
        os.makedirs(DATA_DIR, exist_ok=True)
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(films, f, ensure_ascii=False, indent=2)

        logger.info(f"✅ {len(films)} IMDb-Filme in '{output_path}' gespeichert.")

    except IOError as e:
        logger.error(f"Fehler beim Speichern in {output_path}: {e}")
        raise


if __name__ == "__main__":
    save_imdb_top250_to_json()
