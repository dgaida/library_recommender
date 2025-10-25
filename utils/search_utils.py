#!/usr/bin/env python3
"""
Such- und Zusammenfassungs-Utilities für Medien-Empfehlungen
"""

# import requests
# import json
import os
from ddgs import DDGS
from groq import Groq


def search_media_info(title, author=None, media_type="film"):
    """
    Sucht Informationen über ein Medium mit DuckDuckGo.

    Erstellt einen optimierten Suchbegriff basierend auf Medientyp
    und führt eine DuckDuckGo-Suche durch.

    Args:
        title (str): Titel des Mediums
        author (str, optional): Autor/Regisseur/Künstler
        media_type (str): Art des Mediums ('film', 'album', 'book')

    Returns:
        list[dict]: Liste von Suchergebnissen mit Schlüsseln:
            - "title" (str): Titel des Suchergebnisses
            - "body" (str): Beschreibungstext
            - "href" (str): URL des Ergebnisses

    Raises:
        Exception: Bei Suchproblemen (wird gefangen und gibt [] zurück)

    Example:
        >>> results = search_media_info("Der Pate", "Francis Ford Coppola", "film")
        >>> print(results[0]['title'])
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

        print(f"DEBUG: Suche nach: '{search_term}'")

        # DuckDuckGo Suche
        with DDGS() as ddgs:
            results = list(ddgs.text(search_term, max_results=5))

        return results

    except Exception as e:
        print(f"DEBUG: Fehler bei der Suche: {e}")
        return []


def summarize_with_groq(search_results, title, author=None, media_type="film"):
    """
    Erstellt eine kurze Zusammenfassung mit der Groq API.

    Nutzt ein Llama-Guard-Modell über die Groq API, um aus
    Suchergebnissen eine prägnante 1-2 Sätze Zusammenfassung zu erstellen.

    Args:
        search_results (list[dict]): Suchergebnisse von DuckDuckGo
        title (str): Titel des Mediums
        author (str, optional): Autor/Regisseur/Künstler
        media_type (str): Art des Mediums ('film', 'album', 'book')

    Returns:
        str: 1-2 Sätze Zusammenfassung auf Deutsch

    Raises:
        Exception: Bei API-Problemen (wird gefangen, Fehlermeldung zurückgegeben)

    Note:
        Benötigt GROQ_API_KEY Umgebungsvariable

    Example:
        >>> summary = summarize_with_groq(results, "Der Pate", "Coppola", "film")
        >>> print(summary)
        'Der Pate ist ein Mafia-Drama von 1972...'
    """
    try:
        # Groq API Key aus Umgebungsvariable
        api_key = os.getenv("GROQ_API_KEY")
        if not api_key:
            return "Groq API Key nicht gefunden. Bitte GROQ_API_KEY Umgebungsvariable setzen."

        client = Groq(api_key=api_key)

        # Suchergebnisse zu Text zusammenfassen
        search_text = ""
        for i, result in enumerate(search_results[:3]):  # Nur erste 3 Ergebnisse
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

        prompt = f"""Basierend auf den folgenden Suchergebnissen, schreibe GENAU 1-2 kurze Sätze auf Deutsch über den {media_german} "{title}"{f' von {author}' if author else ''}.

Konzentriere dich auf: {details}. Sei präzise und informativ.

Suchergebnisse:
{search_text}

Antwort (maximal 2 Sätze auf Deutsch):"""

        response = client.chat.completions.create(
            messages=[{"role": "user", "content": prompt}],
            model="moonshotai/kimi-k2-instruct-0905",  # Schnelles Modell
            temperature=0.3,
            max_tokens=150,
        )

        summary = response.choices[0].message.content.strip()
        return summary

    except Exception as e:
        print(f"DEBUG: Fehler bei Groq API: {e}")
        return f"Fehler beim Erstellen der Zusammenfassung: {str(e)}"


def get_media_summary(title, author=None, media_type="film"):
    """
    Kombiniert Suche und Zusammenfassung für ein Medium.

    High-Level-Funktion, die `search_media_info()` und
    `summarize_with_groq()` kombiniert.

    Args:
        title (str): Titel des Mediums
        author (str, optional): Autor/Regisseur/Künstler
        media_type (str): Art des Mediums ('film', 'album', 'book')

    Returns:
        str: Zusammenfassung oder Fehlermeldung

    Example:
        >>> summary = get_media_summary("Mulholland Drive", "David Lynch", "film")
        >>> print(summary)
        'Mulholland Drive ist ein Neo-Noir-Film von 2001...'
    """
    # Erst suchen
    search_results = search_media_info(title, author, media_type)

    if not search_results:
        return f"Keine Informationen zu '{title}' gefunden."

    # Dann zusammenfassen
    summary = summarize_with_groq(search_results, title, author, media_type)

    return summary


def extract_title_and_author(display_text):
    """
    Extrahiert Titel und Autor aus dem Anzeige-Text.

    Parst formatierte Display-Strings aus der GUI und trennt
    Titel und Autor.

    Args:
        display_text (str): Text im Format "Titel - Autor" oder nur "Titel"

    Returns:
        tuple: (title, author)
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
