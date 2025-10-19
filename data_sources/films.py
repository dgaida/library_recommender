#!/usr/bin/env python3
"""
Stadtbibliothek Köln Katalog Suche
Programm zur Suche im Online-Katalog der Stadtbibliothek Köln
"""

import requests
from bs4 import BeautifulSoup
import time

from utils.sources import SOURCE_BBC_100_FILMS
from library.search import KoelnLibrarySearch
from utils.io import save_results_to_markdown


def fetch_wikipedia_titles():
    """
    Lädt die deutschen Filmtitel von der Wikipedia-Seite
    'BBC Culture’s 100 Greatest Films of the 21st Century'
    und gibt sie als Liste zurück.
    Nutzt die Tabelle *nach* der Überschrift "Liste der häufigsten Nennungen".
    """
    url = "https://de.wikipedia.org/wiki/BBC_Culture%E2%80%99s_100_Greatest_Films_of_the_21st_Century"
    print(f"DEBUG: Hole Wikipedia-Seite: {url}")

    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                      "AppleWebKit/537.36 (KHTML, like Gecko) "
                      "Chrome/122.0.0.0 Safari/537.36"
    }
    response = requests.get(url, headers=headers, timeout=15)
    response.raise_for_status()

    soup = BeautifulSoup(response.text, "html.parser")

    titles = []

    # Finde die Überschrift „Liste der häufigsten Nennungen“
    heading = soup.find(lambda tag: tag.name in ["h2", "h3", "h4"] and "Liste der häufigsten Nennungen" in tag.text)
    if not heading:
        print("WARNUNG: Überschrift 'Liste der häufigsten Nennungen' nicht gefunden, nehme erste passende Tabelle.")
        # fallback
        table = soup.find("table", class_="wikitable")
    else:
        # Tabelle nach dieser Überschrift suchen
        table = heading.find_next("table", class_="wikitable")

    if not table:
        print("ERROR: Keine passende Tabelle gefunden.")
        return []

    rows = table.find_all("tr")

    # Kopfzeile identifizieren: die Spalten sind:
    # Platz | Originaltitel | Deutscher Titel | Regie | Jahr | Anmerkungen.
    # Wir wollen die Spalte „Deutscher Titel“
    # Kopfzeile ist rows[0]
    header_cells = [th.get_text(strip=True) for th in rows[0].find_all(["th", "td"])]
    # Finde Index der Spalte „Deutscher Titel“
    try:
        idx_deutscher_titel = header_cells.index("Deutscher Titel")
    except ValueError:
        print(f"WARNUNG: Spalte 'Deutscher Titel' nicht gefunden in Kopfzeile {header_cells}")
        # wir nehmen dann z. B. Spalte 2 (als Fallback)
        idx_deutscher_titel = 2

    # print(idx_deutscher_titel)

    # Durch alle Zeilen gehen
    for row in rows[1:]:
        cells = row.find_all("td")  # kann man das vllt. verallgemeinern, dass es auch für th gilt?
        if len(cells) > idx_deutscher_titel:
            german_title = cells[idx_deutscher_titel - 1].get_text(strip=True)
            regisseur = cells[idx_deutscher_titel].get_text(strip=True)
            if german_title:
                titles.append({
                    "title": german_title,
                    "regie": regisseur,
                    "source": SOURCE_BBC_100_FILMS
                })

    print(f"DEBUG: Insgesamt {len(titles)} deutsche Titel extrahiert.")
    return titles


def search_wikipedia_titles_in_library():
    """
    Holt alle Wikipedia-Titel und sucht sie im Bibliothekskatalog.
    Ergebnisse werden zusätzlich in einer Markdown-Datei gespeichert.
    """
    search_engine = KoelnLibrarySearch()
    titles = fetch_wikipedia_titles()

    # print(titles)

    all_results = {}

    for i, title in enumerate(titles, 1):
        # if i > 5:  # aktuell auf 5 Titel begrenzt
        #     break
        print(f"\n### Suche {i}/{len(titles)}: {title} ###")
        results = search_engine.advanced_search(title['title'], author=title['regie'])
        search_engine.display_results(results)
        all_results[title['title']] = results
        print("Warte 5 Sekunden, um Server nicht zu überlasten...")
        time.sleep(5)  # Pause, um den Server nicht zu überlasten

    # Ergebnisse in Markdown speichern
    save_results_to_markdown(all_results, "results.md")
