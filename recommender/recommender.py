import random
from .state import AppState


class Recommender:
    """
    Stellt Empfehlungslogik für Filme, Musik und Bücher bereit.

    Diese Klasse nutzt `KoelnLibrarySearch`, um Titel in der Stadtbibliothek Köln
    zu suchen und prüft deren aktuelle Verfügbarkeit. Bereits vorgeschlagene
    Items werden in `AppState` gespeichert, um Mehrfachvorschläge zu verhindern.
    """

    def __init__(self, library_search, state: AppState):
        self.library_search = library_search
        self.state = state

    def _pick_available_items(self, items, category, n=4, verbose=False):
        """
        Wählt n zufällige, heute verfügbare Items aus einer Liste.

        Args:
            items (list[dict]): Liste von Werken, z.B. [{'title': ..., 'author': ...}]
            category (str): Kategorie, z.B. 'films', 'albums'
            n (int): Anzahl gewünschter Vorschläge

        Returns:
            list[dict]: Liste der ausgewählten Werke
        """
        results = []
        for item in items:
            # Überspringe, wenn schon vorgeschlagen
            if self.state.is_already_suggested(category, item):
                if verbose:
                    print(f"DEBUG: ignore {item} because it was already suggested")
                continue

            media_type = item.get('type', '')

            if media_type == "Buch":
                query = f"{item.get('author', '')} {item.get('title')} {media_type}".strip()
            else:
                query = f"{item.get('title')} {item.get('author', '')} {media_type}".strip()

            # Suche in Bibliothek
            hits = self.library_search.search(query)

            # Prüfen, ob verfügbar (nur auf zentralbibliothek_info)
            available = [
                h for h in hits
                if "zentralbibliothek_info" in h and "verfügbar" in h["zentralbibliothek_info"].lower()
            ]

            if available:
                # alle Verfügbarkeits-Infos zusammenfassen
                infos = [h["zentralbibliothek_info"] for h in hits if "zentralbibliothek_info" in h]

                item['bib_number'] = f"{', '.join(infos)}"
                # als String speichern
                results.append(item)

                self.state.mark_suggested(category, item)

            if len(results) >= n:
                break

        return results

    def suggest_films(self, films, n=4):
        """
        Wählt verfügbare Filme aus der bereitgestellten Liste.

        Args:
            films (list[dict]): Liste von Filmen mit Titeln, Autoren und Typ.
            n (int, optional): Anzahl gewünschter Vorschläge. Standard: 4.

        Returns:
            list[dict]: Liste der vorgeschlagenen Filme, die aktuell in der
            Zentralbibliothek verfügbar sind.
        """
        return self._pick_available_items(films, "films", n)

    def suggest_albums(self, albums, n=4):
        """
        Wählt verfügbare Musikalben aus der bereitgestellten Liste.

        Args:
            albums (list[dict]): Liste von Alben mit Titel, Künstler und Typ.
            n (int, optional): Anzahl gewünschter Vorschläge. Standard: 4.

        Returns:
            list[dict]: Liste der vorgeschlagenen Alben, die aktuell in der
            Zentralbibliothek verfügbar sind.
        """
        return self._pick_available_items(albums, "albums", n)

    def suggest_books(self, books, n=4):
        """
        Wählt verfügbare Bücher aus der bereitgestellten Liste.

        Args:
            books (list[dict]): Liste von Büchern mit Titel, Autor und Typ.
            n (int, optional): Anzahl gewünschter Vorschläge. Standard: 4.

        Returns:
            list[dict]: Liste der vorgeschlagenen Bücher, die aktuell in der
            Zentralbibliothek verfügbar sind.
        """
        # Platzhalter – analog zu Filmen/Alben
        return self._pick_available_items(books, "books", n)
