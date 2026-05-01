# ⚙️ Konfiguration

Dieser Abschnitt beschreibt, wie Sie die App an Ihre Bedürfnisse anpassen.

## 1. MP3-Archiv Pfad

Die personalisierten Musikempfehlungen analysieren Ihr lokales MP3-Archiv. Um dies zu konfigurieren, bearbeiten Sie folgende Dateien:

- `data_sources/mp3_analysis.py`: Ändern Sie den Pfad in `add_top_artist_albums_to_collection("PFAD/ZU/DEINEM/MP3/ARCHIV", top_n=30)`.  
- `data_sources/albums.py`: Passen Sie den Filterpfad in `filter_existing_albums(albums, "PFAD/ZU/DEINEM/MP3/ARCHIV")` an.  

## 2. Groq API Key

Erstellen Sie eine Datei namens `secrets.env` im Hauptverzeichnis mit folgendem Inhalt:

```env
GROQ_API_KEY=gsk_...
```

Dieser Key wird für die KI-generierten Zusammenfassungen (über das Groq-Modell) verwendet.

## 3. Anzahl der Empfehlungen

Die App schlägt standardmäßig 25 Titel pro Kategorie vor (5 pro Datenquelle). Dies kann in `recommender/recommender.py` angepasst werden.
