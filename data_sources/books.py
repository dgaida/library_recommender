import os
import requests
from bs4 import BeautifulSoup

DATA_DIR = os.path.join(os.path.dirname(__file__), "..", "data")
os.makedirs(DATA_DIR, exist_ok=True)
BOOKS_FILE = os.path.join(DATA_DIR, "books.json")

URL = "https://www.die-besten-aller-zeiten.de/buecher/kanon/new-york-times-21-jahrhundert.html"


def fetch_books_from_site():
    """
    Holt die Liste der 100 Bücher von der Webseite und gibt sie als Liste von Dicts zurück.
    Jedes Dict enthält: title, author, description.
    """
    print(f"DEBUG: Lade Webseite {URL}...")
    response = requests.get(URL, headers={"User-Agent": "Mozilla/5.0"})
    response.raise_for_status()

    soup = BeautifulSoup(response.text, "html.parser")

    books = []

    # Jeder Titel steckt in einem <a class="accordionlink"> Tag
    links = soup.select("a.accordionlink")
    print(f"DEBUG: Gefunden {len(links)} Buch-Einträge...")

    for link in links:
        raw_text = link.get_text(strip=True)  # z. B. "1. Elena Ferrante: Meine geniale Freundin"
        # Nummer entfernen
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
        description = ""
        if accordion_div:
            para = accordion_div.find("div", class_="paragraph")
            if para:
                description = para.get_text(" ", strip=True)

        books.append({"title": title, "author": author, "description": description})

    return books
