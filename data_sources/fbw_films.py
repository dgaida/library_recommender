#!/usr/bin/env python3
"""
FBW-Filmempfehlungen – Extraktion der Filme mit Prädikat „besonders wertvoll“.

Diese Datei lädt die Filme von der Webseite der Deutschen Film- und Medienbewertung (FBW)
und speichert diejenigen Filme, die das Prädikat „besonders wertvoll“ erhalten haben, in einer JSON-Datei.

Ziel-Format (data/films.json):

[
  {
    "title": "Chihiros Reise ins Zauberland",
    "author": "Hayao Miyazaki",
    "type": "DVD"
  },
  ...
]
"""

import requests
from bs4 import BeautifulSoup
import json
import os
import time

from utils.io import DATA_DIR


BASE_URL = "https://www.fbw-filmbewertung.com"
FILM_LIST_URL = f"{BASE_URL}/filme"


def fetch_fbw_films(max_pages=5, delay=1.0):
    """
    Ruft Filme von der FBW-Filmbewertungsseite ab, die das
    Prädikat "besonders wertvoll" tragen.

    Args:
        max_pages (int): Anzahl der Seiten, die durchsucht werden sollen.
        delay (float): Wartezeit (Sekunden) zwischen Seitenabrufen.

    Returns:
        list[dict]: Liste von Filmen mit Schlüsseln:
            - "title" (str): Titel des Films
            - "author" (str): Regisseur/in
            - "description" (str): Kurzbeschreibung
            - "url" (str): Link zur Filmseite
            - "type" (str): Immer "DVD"
    """
    all_films = []

    session = requests.Session()
    headers = {"User-Agent": "Mozilla/5.0 (compatible; FBW-Scraper/1.0)"}

    for page in range(1, max_pages + 1):
        url = f"{FILM_LIST_URL}?page={page}"
        print(f"DEBUG: Rufe Seite {page} ab: {url}")

        try:
            response = session.get(url, headers=headers, timeout=15)
            response.raise_for_status()
        except requests.RequestException as e:
            print(f"FEHLER beim Laden von Seite {page}: {e}")
            continue

        soup = BeautifulSoup(response.text, "html.parser")

        film_items = soup.select("div.row--filmitem.clearfix")
        if not film_items:
            print(f"DEBUG: Keine Filmitems auf Seite {page} gefunden.")
            break

        for item in film_items:
            # Prüfe auf das "besonders wertvoll"-Siegel
            seal_img = item.select_one("div.film_rating img[alt*='besonders wertvoll']")
            if not seal_img:
                continue  # überspringe Filme ohne Siegel

            # Titel
            title_tag = item.select_one("h2 a")
            title = title_tag.text.strip() if title_tag else "Unbekannt"
            link = BASE_URL + title_tag["href"] if title_tag and title_tag.has_attr("href") else None

            # Regie
            director = ""
            regie_tag = item.select_one(".row--filmitem-additionalinfos-cast")
            if regie_tag and "Regie:" in regie_tag.text:
                text = regie_tag.get_text(" ", strip=True)
                if "Regie:" in text:
                    director = text.split("Regie:")[1].split("|")[0].strip()

            # Beschreibung
            desc_tag = item.select_one("p.film_presstext")
            description = desc_tag.text.strip() if desc_tag else ""

            film_info = {
                "title": title,
                "author": director,
                "description": description,
                "url": link,
                "type": "DVD",
            }
            all_films.append(film_info)

        print(f"DEBUG: {len(film_items)} Filme auf Seite {page} gefunden, davon {len(all_films)} mit Siegel.")
        time.sleep(delay)

    print(f"DEBUG: Insgesamt {len(all_films)} Filme mit 'besonders wertvoll' gefunden.")
    return all_films


def fetch_oscar_best_picture_winners(url="https://de.wikipedia.org/wiki/Oscar/Bester_Film"):
    """
    Ruft alle Gewinnerfilme des Oscars für 'Bester Film' von der deutschen Wikipedia ab.

    Die Funktion parst die HTML-Tabelle(n) auf der Wikipedia-Seite und extrahiert:
      - Jahr der Verleihung
      - Produzent bzw. Studio
      - Titel des Gewinnerfilms
      - (Optional) URL zur Wikipedia-Seite des Films

    Args:
        url (str, optional): URL der Wikipedia-Seite. Standardmäßig die deutsche Seite zu
            'Oscar/Bester Film'.

    Returns:
        list[dict]: Liste von Gewinnerfilmen mit folgenden Schlüsseln:
            - "year" (str): Jahr der Oscarverleihung
            - "producer" (str): Produzent oder Studio
            - "title" (str): Titel des ausgezeichneten Films
            - "url" (str): Vollständige Wikipedia-URL des Films
            - "type" (str): Immer "Oscar Bester Film"
    """
    headers = {
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/130.0 Safari/537.36"
        )
    }

    for attempt in range(3):
        try:
            resp = requests.get(url, headers=headers, timeout=10)
            resp.raise_for_status()
            break
        except requests.exceptions.RequestException as e:
            print(f"Versuch {attempt+1}/3 fehlgeschlagen: {e}")
            time.sleep(2)
    else:
        raise RuntimeError(f"Fehler: Zugriff auf {url} nicht möglich.")

    base_url = "https://de.wikipedia.org"
    soup = BeautifulSoup(resp.text, "html.parser")

    results = []
    tables = soup.find_all("table", class_="wikitable")

    for table in tables:
        rows = table.find_all("tr")[1:]  # Header-Zeile überspringen
        for row in rows:
            cols = row.find_all("td")
            if len(cols) < 4:
                continue

            year_link = cols[1].find("a")
            year = year_link.text.strip() if year_link else cols[1].get_text(strip=True)
            producer = cols[2].get_text(strip=True)

            film_link = cols[3].find("a")
            if not film_link:
                continue

            title = film_link.get("title", film_link.text.strip())
            href = film_link.get("href")
            film_url = base_url + href if href else None

            results.append({
                "year": year,
                "producer": producer,
                "title": title,
                "url": film_url,
                "type": "Oscar Bester Film"
            })

    print(f"DEBUG: {len(results)} Oscar-Gewinnerfilme gefunden.")
    return results


def save_fbw_films_to_json(filename="films.json"):
    """
    Lädt Filme von FBW und speichert sie als JSON-Datei im data-Verzeichnis.

    Args:
        filename (str): Name der Ausgabedatei.
    """
    films = fetch_fbw_films(max_pages=10)
    output_path = os.path.join(DATA_DIR, filename)

    os.makedirs(DATA_DIR, exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(films, f, ensure_ascii=False, indent=2)

    print(f"✅ {len(films)} Filme in '{output_path}' gespeichert.")


if __name__ == "__main__":
    save_fbw_films_to_json()
