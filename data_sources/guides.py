import os
import json
import requests
from bs4 import BeautifulSoup

DATA_DIR = os.path.join(os.path.dirname(__file__), "..", "data")
os.makedirs(DATA_DIR, exist_ok=True)
GUIDES_FILE = os.path.join(DATA_DIR, "guides.json")

URL = (
    "https://www.die-besten-aller-zeiten.de/buecher/kanon/buecher-des-21-jahrhunderts.html#ngaw7e610e112e3a6b42a06438725348403"
)


def fetch_guides_from_site():
    """
    Holt die Liste der 'besten Ratgeber des 21. Jahrhunderts' von der Webseite.

    Parst die HTML-Seite und extrahiert Ratgeber-Titel, Autoren und
    Beschreibungen aus dem Abschnitt "Die besten Ratgeber des 21. Jahrhunderts".

    Returns:
        list[dict]: Liste von Ratgebern mit Schlüsseln:
            - "title" (str): Titel des Ratgebers
            - "author" (str): Autor/in
            - "description" (str): Beschreibungstext

    Raises:
        requests.RequestException: Bei Netzwerkproblemen

    Example:
        >>> guides = fetch_guides_from_site()
        >>> print(guides[0]['title'])
        'Schnelles Denken, langsames Denken'
    """
    print(f"DEBUG: Lade Webseite {URL}...")
    response = requests.get(URL, headers={"User-Agent": "Mozilla/5.0"})
    response.raise_for_status()

    soup = BeautifulSoup(response.text, "html.parser")

    guides = []

    # Abschnitt 'Die besten Ratgeber des 21. Jahrhunderts' finden
    header = soup.find("h2", string="Die besten Ratgeber des 21. Jahrhunderts")
    if not header:
        print("WARNUNG: Abschnitt 'Die besten Ratgeber des 21. Jahrhunderts' nicht gefunden.")
        return guides

    # Danach folgen die Einträge als <a class="accordionlink">,
    # bis 'Die besten Jugendbücher des 21. Jahrhunderts' erreicht wird.
    accordion_links = []
    for el in header.find_all_next(["h2", "a"], class_=["sqrallwaysboxed", "accordionlink"]):
        # Stoppe, sobald der nächste Abschnitt (Jugendbücher) beginnt
        if el.name == "h2" and "Die besten Jugendbücher des 21. Jahrhunderts" in el.get_text():
            break
        if el.name == "a" and "accordionlink" in el.get("class", []):
            accordion_links.append(el)

    print(f"DEBUG: Gefunden {len(accordion_links)} Ratgeber-Einträge...")

    for link in accordion_links:
        raw_text = link.get_text(strip=True)

        # Format: "Autor: Titel (Jahr)"
        if ":" in raw_text:
            author, rest = raw_text.split(":", 1)
            author = author.strip()
            title = rest.strip()
        else:
            author, title = "", raw_text

        # Jahr in Klammern entfernen, falls vorhanden
        if title.endswith(")"):
            title = title.rsplit("(", 1)[0].strip()

        # Beschreibung im nächsten <div class="accordionarea">
        accordion_div = link.find_next("div", class_="accordionarea")
        description = ""
        if accordion_div:
            paragraphs = accordion_div.find_all("p")
            description = " ".join(p.get_text(strip=True) for p in paragraphs)

        guides.append({"title": title, "author": author, "description": description})

    print(f"DEBUG: Extrahiert {len(guides)} Ratgeber-Einträge.")
    return guides


def save_guides_to_json():
    """
    Speichert die Ratgeber-Liste in guides.json.

    Ruft `fetch_guides_from_site()` auf und schreibt die Ergebnisse
    in eine JSON-Datei im DATA_DIR.

    Returns:
        None: Datei wird direkt geschrieben

    Raises:
        IOError: Bei Schreibproblemen

    Example:
        >>> save_guides_to_json()
        ✅ 25 Ratgeber in data/guides.json gespeichert.
    """
    guides = fetch_guides_from_site()
    if not guides:
        print("WARNUNG: Keine Ratgeber gefunden – nichts gespeichert.")
        return

    with open(GUIDES_FILE, "w", encoding="utf-8") as f:
        json.dump(guides, f, ensure_ascii=False, indent=2)

    print(f"✅ {len(guides)} Ratgeber in {GUIDES_FILE} gespeichert.")


if __name__ == "__main__":
    save_guides_to_json()
