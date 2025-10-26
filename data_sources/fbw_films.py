#!/usr/bin/env python3
"""
FBW-Filmempfehlungen – Extraktion der Filme mit Prädikat „besonders wertvoll".

Diese Datei lädt die Filme von der Webseite der Deutschen Film- und Medienbewertung (FBW)
und speichert diejenigen Filme, die das Prädikat „besonders wertvoll" erhalten haben.
"""

import requests
from bs4 import BeautifulSoup
import json
import os
import time
from typing import List, Dict, Any

from utils.io import DATA_DIR
from utils.sources import SOURCE_FBW_EXCEPTIONAL, SOURCE_OSCAR_BEST_PICTURE
from utils.logging_config import get_logger

logger = get_logger(__name__)

BASE_URL = "https://www.fbw-filmbewertung.com"
FILM_LIST_URL = f"{BASE_URL}/filme"


def fetch_fbw_films(max_pages: int = 5, delay: float = 1.0) -> List[Dict[str, Any]]:
    """
    Ruft Filme von der FBW-Filmbewertungsseite ab, die das
    Prädikat "besonders wertvoll" tragen.

    Args:
        max_pages: Anzahl der Seiten, die durchsucht werden sollen (default: 5)
        delay: Wartezeit (Sekunden) zwischen Seitenabrufen (default: 1.0)

    Returns:
        Liste von Filmen mit Schlüsseln:
            - title: Titel des Films
            - author: Regisseur/in
            - description: Kurzbeschreibung
            - url: Link zur Filmseite
            - type: Immer "DVD"
            - source: Quellen-Bezeichnung

    Raises:
        requests.RequestException: Bei Netzwerkproblemen

    Example:
        >>> films = fetch_fbw_films(max_pages=2)
        >>> print(len(films))
        25
        >>> print(films[0]['title'])
        'Das Leben der Anderen'
    """
    all_films: List[Dict[str, Any]] = []

    session = requests.Session()
    headers = {"User-Agent": "Mozilla/5.0 (compatible; FBW-Scraper/1.0)"}

    for page in range(1, max_pages + 1):
        url = f"{FILM_LIST_URL}?page={page}"
        logger.info(f"Rufe Seite {page} ab: {url}")

        try:
            response = session.get(url, headers=headers, timeout=15)
            response.raise_for_status()
        except requests.RequestException as e:
            logger.error(f"Fehler beim Laden von Seite {page}: {e}")
            continue

        soup = BeautifulSoup(response.text, "html.parser")

        film_items = soup.select("div.row--filmitem.clearfix")
        if not film_items:
            logger.debug(f"Keine Filmitems auf Seite {page} gefunden.")
            break

        for item in film_items:
            # Prüfe auf das "besonders wertvoll"-Siegel
            seal_img = item.select_one("div.film_rating img[alt*='besonders wertvoll']")
            if not seal_img:
                continue

            # Titel
            title_tag = item.select_one("h2 a")
            title: str = title_tag.text.strip() if title_tag else "Unbekannt"
            link: str = BASE_URL + title_tag["href"] if title_tag and title_tag.has_attr("href") else ""

            # Regie
            director: str = ""
            regie_tag = item.select_one(".row--filmitem-additionalinfos-cast")
            if regie_tag and "Regie:" in regie_tag.text:
                text = regie_tag.get_text(" ", strip=True)
                if "Regie:" in text:
                    director = text.split("Regie:")[1].split("|")[0].strip()

            # Beschreibung
            desc_tag = item.select_one("p.film_presstext")
            description: str = desc_tag.text.strip() if desc_tag else ""

            film_info: Dict[str, Any] = {
                "title": title,
                "author": director,
                "description": description,
                "url": link,
                "type": "DVD",
                "source": SOURCE_FBW_EXCEPTIONAL,
            }
            all_films.append(film_info)

        logger.debug(
            f"{len(film_items)} Filme auf Seite {page} gefunden, "
            f"davon {len([f for f in all_films if f['source'] == SOURCE_FBW_EXCEPTIONAL])} mit Siegel."
        )
        time.sleep(delay)

    logger.info(f"Insgesamt {len(all_films)} Filme mit 'besonders wertvoll' gefunden")
    return all_films


def fetch_oscar_best_picture_winners(url: str = "https://de.wikipedia.org/wiki/Oscar/Bester_Film") -> List[Dict[str, Any]]:
    """
    Ruft alle Gewinnerfilme des Oscars für 'Bester Film' von der deutschen Wikipedia ab.

    Die Funktion parst die HTML-Tabelle(n) auf der Wikipedia-Seite und extrahiert:
      - Jahr der Verleihung
      - Produzent bzw. Studio
      - Titel des Gewinnerfilms
      - URL zur Wikipedia-Seite des Films

    Args:
        url: URL der Wikipedia-Seite (default: deutsche Seite zu 'Oscar/Bester Film')

    Returns:
        Liste von Gewinnerfilmen mit Schlüsseln:
            - year: Jahr der Oscarverleihung
            - producer: Produzent oder Studio
            - title: Titel des ausgezeichneten Films
            - url: Vollständige Wikipedia-URL des Films
            - type: Immer "DVD"
            - source: Quellen-Bezeichnung

    Raises:
        RuntimeError: Nach 3 erfolglosen Verbindungsversuchen

    Example:
        >>> winners = fetch_oscar_best_picture_winners()
        >>> print(winners[0]['title'])
        'Oppenheimer'
        >>> print(winners[0]['year'])
        '2024'
    """
    headers = {
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) " "AppleWebKit/537.36 (KHTML, like Gecko) " "Chrome/130.0 Safari/537.36"
        )
    }

    logger.info(f"Lade Oscar-Seite: {url}")

    for attempt in range(3):
        try:
            resp = requests.get(url, headers=headers, timeout=10)
            resp.raise_for_status()
            break
        except requests.exceptions.RequestException as e:
            logger.warning(f"Versuch {attempt + 1}/3 fehlgeschlagen: {e}")
            time.sleep(2)
    else:
        raise RuntimeError(f"Fehler: Zugriff auf {url} nicht möglich.")

    base_url = "https://de.wikipedia.org"
    soup = BeautifulSoup(resp.text, "html.parser")

    results: List[Dict[str, Any]] = []
    tables = soup.find_all("table", class_="wikitable")

    for table in tables:
        rows = table.find_all("tr")[1:]  # Header-Zeile überspringen
        for row in rows:
            cols = row.find_all("td")
            if len(cols) < 4:
                continue

            year_link = cols[1].find("a")
            year: str = year_link.text.strip() if year_link else cols[1].get_text(strip=True)
            producer: str = cols[2].get_text(strip=True)

            film_link = cols[3].find("a")
            if not film_link:
                continue

            title: str = film_link.get("title", film_link.text.strip())
            href = film_link.get("href")
            film_url: str = base_url + href if href else ""

            results.append(
                {
                    "year": year,
                    "producer": producer,
                    "title": title,
                    "url": film_url,
                    "type": "DVD",
                    "source": SOURCE_OSCAR_BEST_PICTURE,
                }
            )

    logger.info(f"{len(results)} Oscar-Gewinnerfilme gefunden")
    return results


def save_fbw_films_to_json(filename: str = "films.json") -> None:
    """
    Lädt Filme von FBW und speichert sie als JSON-Datei im data-Verzeichnis.

    Ruft fetch_fbw_films() auf und schreibt die Ergebnisse in eine JSON-Datei
    im konfigurierten DATA_DIR.

    Args:
        filename: Name der Ausgabedatei (default: "films.json")

    Raises:
        IOError: Bei Schreibproblemen

    Example:
        >>> save_fbw_films_to_json("meine_filme.json")
        # INFO: ✅ 150 Filme in 'data/meine_filme.json' gespeichert.
    """
    films = fetch_fbw_films(max_pages=10)
    output_path = os.path.join(DATA_DIR, filename)

    try:
        os.makedirs(DATA_DIR, exist_ok=True)
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(films, f, ensure_ascii=False, indent=2)

        logger.info(f"✅ {len(films)} Filme in '{output_path}' gespeichert")

    except IOError as e:
        logger.error(f"Fehler beim Speichern in {output_path}: {e}")
        raise


if __name__ == "__main__":
    save_fbw_films_to_json()
