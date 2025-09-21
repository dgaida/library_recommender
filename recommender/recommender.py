import random
from .state import AppState


class Recommender:
    """
    Stellt Empfehlungen für Filme, Musik und später Bücher bereit.
    """

    def __init__(self, library_search, state: AppState):
        self.library_search = library_search
        self.state = state

    def _pick_available_items(self, items, category, n=4):
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
                print(f"DEBUG: ignore {item} because it was already suggested")
                continue

            # Suche in Bibliothek
            query = f"{item.get('title')} {item.get('author', '')}".strip()
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
        return self._pick_available_items(films, "films", n)

    def suggest_albums(self, albums, n=4):
        return self._pick_available_items(albums, "albums", n)

    def suggest_books(self, books, n=4):
        # Platzhalter – analog zu Filmen/Alben
        return self._pick_available_items(books, "books", n)
