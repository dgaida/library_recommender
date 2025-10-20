# 🎬📀📚 Bibliothek-Empfehlungs-App

Eine intelligente Empfehlungs-App für die **Stadtbibliothek Köln**, die verfügbare Filme, Alben und Bücher basierend auf kuratierten Listen hochwertiger Medien vorschlägt.

![Python](https://img.shields.io/badge/python-3.8+-blue.svg)
![Gradio](https://img.shields.io/badge/gradio-4.0+-green.svg)
![License](https://img.shields.io/badge/license-MIT-blue.svg)

## ✨ Features

### 🎯 **Intelligente Empfehlungen**

#### 🎬 **Filme**
Kombination aus mehreren Premium-Quellen:
- **BBC Culture**: *100 Greatest Films of the 21st Century*
- **FBW**: Deutsche Filme mit Prädikat „besonders wertvoll"
- **Oscar**: Alle Gewinner der Kategorie „Bester Film"
- Automatische Zusammenführung, Duplikats-Bereinigung und alphabetische Sortierung
- Lokaler JSON-Cache für schnelleren Start

#### 🎵 **Musik**
Vielfältige Musikempfehlungen aus:
- **Radio Eins**: Top 100 Alben 2019
- **Oscar**: Beste Filmmusik-Gewinner aller Zeiten
- **Personalisiert**: Basierend auf deinem MP3-Archiv (Top-Interpreten-Analyse)
- Intelligente Filterung bereits vorhandener Alben
- Fuzzy-Matching-Algorithmen für präzise Duplikatserkennung

#### 📚 **Bücher & Ratgeber**
Hochwertige Literatur aus:
- **New York Times**: Kanon des 21. Jahrhunderts
- **Die besten Ratgeber**: Sachbücher des 21. Jahrhunderts
- Mit Autorenangaben und ausführlichen Beschreibungstexten

### 🔍 **Verfügbarkeitsprüfung**
- Automatische Live-Suche im Online-Katalog der Stadtbibliothek Köln
- Nur tatsächlich verfügbare Medien werden vorgeschlagen
- Echtzeit-Verfügbarkeitsstatus für die Zentralbibliothek
- **Intelligente Blacklist**: Medien ohne Treffer werden gespeichert und bei zukünftigen Läufen übersprungen

### 🎮 **Interaktive GUI**
- **Mehrfachauswahl**: Mehrere Titel gleichzeitig auswählen und entfernen
- **Quellen-Kennzeichnung**: Emojis zeigen die Herkunft jeder Empfehlung (🏆 Oscar, ⭐ FBW, 📻 Radio Eins, etc.)
- **Google-Suche mit KI**: 1-2 Sätze Zusammenfassung zu jedem Medium (powered by Groq AI)
- **Automatischer Start**: Vorschläge werden beim App-Start geladen und automatisch gespeichert
- **Persistente Ablehnungen**: Abgelehnte Titel werden permanent gespeichert und nie wieder vorgeschlagen
- **Erfolgs-Feedback**: Visuelle Bestätigung nach jeder Aktion

### 💎 **Personalisierte Empfehlungen**
- **MP3-Archiv-Analyse**: Automatische Erkennung deiner Lieblingskünstler
- **Top-Interpreten-Tracking**: Identifiziert deine meist gehörten Künstler
- **Neue Alben deiner Favoriten**: Sucht gezielt nach weiteren Werken deiner Top-10-Interpreten
- **Smart Filtering**: Schlägt nur Alben vor, die du noch nicht besitzt

### 💾 **Export-Funktionen**
- Empfehlungen als übersichtliche Markdown-Datei speichern
- Automatische Dokumentation mit Verfügbarkeitsstatus
- Zeitstempel und detaillierte Kategorien-Übersicht
- Automatisches Speichern bei App-Start

### 🧠 **Intelligentes Caching & Performance**
- **Daten-Cache**: Alle Film-, Musik- und Buchdaten werden nach dem ersten Laden in `data/*.json` gespeichert
- **Blacklist-System**: Medien ohne Bibliotheks-Treffer werden dauerhaft gespeichert (vermeidet wiederholte Suchanfragen)
- **Schneller Start**: Beim nächsten Start wird automatisch der Cache genutzt
- **Flexible Updates**: Aktualisierung bei Änderungen an den Datenquellen jederzeit möglich

## 🚀 Installation

### Voraussetzungen
- Python 3.8 oder höher
- Internetverbindung für Bibliothekskatalog und Google-Suche

### 1. Repository klonen
```bash
git clone https://github.com/dgaida/library-recommender.git
cd library-recommender
```

### 2. Abhängigkeiten installieren

#### Option A: pip (empfohlen)
```bash
pip install -r requirements.txt
```

#### Option B: Anaconda
```bash
conda env create -f environment.yaml
conda activate koeln-library-search
```

### 3. Groq API Key einrichten (optional, für Google-Suche)
Kostenlosen Account erstellen: https://groq.com

Erstelle eine `secrets.env` mit dem Eintrag:
```
GROQ_API_KEY=gsk_...
```

> **Hinweis**: Ohne Groq API Key funktioniert die Google-Suche nicht, alle anderen Features bleiben verfügbar.

### 4. MP3-Archiv Pfad anpassen (optional)
Für personalisierte Musikempfehlungen bearbeite `data_sources/mp3_analysis.py`:
```python
add_top_artist_albums_to_collection("PFAD/ZU/DEINEM/MP3/ARCHIV", top_n=10)
```

Und in `data_sources/albums.py`:
```python
albums = filter_existing_albums(albums, "PFAD/ZU/DEINEM/MP3/ARCHIV")
```

## 🎮 Verwendung

### App starten
```bash
python main.py
```

Die App öffnet sich automatisch im Browser unter `http://localhost:7860`

### 🎬 **Filme-Tab**
1. **Automatische Vorschläge** beim Start mit Quellen-Emojis (🏆 Oscar, ⭐ FBW, 🎬 BBC)
2. **Film auswählen** → Google-Button wird aktiv
3. **🔍 Google-Suche** → KI-generierte Kurzzusammenfassung (1-2 Sätze)
4. **Mehrere Filme auswählen** → "Entfernen" → Neue Vorschläge werden automatisch nachgeladen
5. **Details anzeigen**: Regie, Verfügbarkeit und Herkunftsquelle

### 🎵 **Musik-Tab**
1. **Vielfältige Quellen**: Radio Eins (📻), Oscar-Filmmusik (🎵), Top-Interpreten (💎)
2. **Personalisierte Vorschläge**: Neue Alben deiner Lieblingskünstler
3. **Automatische Filterung**: Nur Alben, die noch nicht in deinem MP3-Archiv sind
4. **Gleiche Funktionalität** wie Filme-Tab

### 📚 **Bücher-Tab**
1. **Premium-Quellen**: NYT Kanon (📚) und beste Ratgeber des 21. Jahrhunderts
2. **Ausführliche Infos**: Titel, Autor und Beschreibungstext
3. **Identische Interaktion**: Mehrfachauswahl, Entfernen, Google-Suche

### 💾 **Empfehlungen speichern**
- **"Alle Empfehlungen speichern"** Button oben
- Erstellt `recommended.md` mit allen aktuellen Vorschlägen
- Übersichtliche Formatierung mit Verfügbarkeitsstatus
- Automatisches Speichern beim App-Start

## 📁 Projektstruktur

```
library-recommender/
├── main.py                        # Hauptanwendung (Gradio UI)
├── requirements.txt               # Python-Abhängigkeiten
├── environment.yaml               # Anaconda Umgebung
├── README.md                      # Diese Datei
├── LICENSE                        # MIT Lizenz
├── .gitignore                     # Git-Ignore-Regeln
│
├── data/                          # Automatisch erstellte Daten
│   ├── films.json                 # Cache: BBC + FBW + Oscar (alphabetisch)
│   ├── albums.json                # Cache: Radio Eins + Oscar + Personalisiert
│   ├── books.json                 # Cache: NYT Kanon + Ratgeber
│   ├── state.json                 # Abgelehnte Medien (persistent)
│   ├── blacklist_films.json       # Filme ohne Bibliotheks-Treffer
│   ├── blacklist_albums.json      # Alben ohne Bibliotheks-Treffer
│   └── blacklist_books.json       # Bücher ohne Bibliotheks-Treffer
│
├── data_sources/                  # Datenquellen-Module
│   ├── __init__.py
│   ├── albums.py                  # Radio Eins Album-Liste
│   ├── films.py                   # BBC Culture Film-Liste
│   ├── fbw_films.py               # FBW + Oscar-Filme
│   ├── oscar_music.py             # Oscar-Filmmusik
│   ├── mp3_analysis.py            # MP3-Archiv Analyse & Top-Interpreten
│   ├── books.py                   # NYT-Buchkanon
│   └── guides.py                  # Ratgeber des 21. Jahrhunderts
│
├── gui/                           # Grafische Benutzeroberfläche
│   ├── __init__.py
│   └── app.py                     # Gradio-App mit Tabs & Event-Handler
│
├── library/                       # Bibliotheks-Integration
│   ├── __init__.py
│   ├── search.py                  # Stadtbibliothek Köln Suchengine
│   └── parsers.py                 # Text-Normalisierung & Fuzzy-Matching
│
├── preprocessing/                 # Datenaufbereitung
│   ├── __init__.py
│   └── filters.py                 # MP3-Archiv Filterung & Duplikatserkennung
│
├── recommender/                   # Empfehlungslogik
│   ├── __init__.py
│   ├── recommender.py             # Haupt-Engine mit Blacklist-Integration
│   └── state.py                   # Zustandsverwaltung (vorgeschlagen/abgelehnt)
│
└── utils/                         # Hilfsfunktionen
    ├── __init__.py
    ├── io.py                      # Datei I/O & Markdown-Export
    ├── search_utils.py            # Google-Suche & KI-Zusammenfassung
    ├── sources.py                 # Quellen-Konstanten & Emoji-Mapping
    └── blacklist.py               # Blacklist-Verwaltung für Nicht-Treffer
```

## ⚙️ Konfiguration

### MP3-Archiv Pfad
In `data_sources/albums.py` und `data_sources/mp3_analysis.py` ändern:
```python
albums = filter_existing_albums(albums, "/path/to/your/mp3/archive")
add_top_artist_albums_to_collection("/path/to/your/mp3/archive", top_n=10)
```

### Bibliothekskatalog
Die App ist für die **Stadtbibliothek Köln** konfiguriert. Für andere Bibliotheken müsste `library/search.py` angepasst werden.

### Anzahl Top-Interpreten
In `data_sources/mp3_analysis.py`:
```python
add_top_artist_albums_to_collection("H:\\MP3 Archiv", top_n=20)  # Standard: 10
```

## 🔧 Technische Details

### Datenquellen
- **Filme (BBC)**: [BBC Culture's 100 Greatest Films](https://de.wikipedia.org/wiki/BBC_Culture%E2%80%99s_100_Greatest_Films_of_the_21st_Century)
- **Filme (FBW)**: [Deutsche Filmbewertungsstelle – Prädikat besonders wertvoll](https://www.fbw-filmbewertung.com/filme)
- **Filme (Oscar)**: [Wikipedia – Oscar/Bester Film](https://de.wikipedia.org/wiki/Oscar/Bester_Film)
- **Musik (Radio Eins)**: [Die 100 besten Alben 2019](https://www.radioeins.de/musik/top_100/die-100-besten-2019/alben/)
- **Musik (Oscar)**: [Wikipedia – Oscar/Beste Filmmusik](https://de.wikipedia.org/wiki/Oscar/Beste_Filmmusik)
- **Bücher (NYT)**: [New York Times Kanon des 21. Jahrhunderts](https://www.die-besten-aller-zeiten.de/buecher/kanon/new-york-times-21-jahrhundert.html)
- **Ratgeber**: [Die besten Ratgeber des 21. Jahrhunderts](https://www.die-besten-aller-zeiten.de/buecher/kanon/buecher-des-21-jahrhunderts.html)
- **Katalog**: [Stadtbibliothek Köln Online-Katalog](https://katalog.stbib-koeln.de)

### Algorithmen
- **Fuzzy Matching**: Intelligente Textnormalisierung für MP3-Archiv-Abgleich
- **Verfügbarkeitsprüfung**: Web Scraping des Bibliothekskatalogs mit Retry-Logik
- **Suchvarianten**: Automatische Generierung alternativer Suchbegriffe
- **Blacklist-System**: Permanente Speicherung von Nicht-Treffern zur Performance-Optimierung
- **Top-Interpreten-Analyse**: Zählt Songs pro Künstler im MP3-Archiv

### APIs & Libraries
- **DuckDuckGo Search**: Kostenlose Websuche für Medien-Informationen
- **Groq API**: Schnelle LLM-Zusammenfassungen (llama-guard-4-12b)
- **BeautifulSoup**: HTML-Parsing für Web Scraping
- **Gradio**: Moderne Web-UI mit Event-Handling

## 📊 Datenfiles

### `state.json` - Abgelehnte Medien
```json
{
  "films": [{"title": "Mulholland Drive", "author": "David Lynch"}],
  "albums": [{"title": "OK Computer", "author": "Radiohead"}],
  "books": []
}
```

### `blacklist_*.json` - Nicht verfügbare Medien
```json
[
  {
    "title": "Beispiel Film",
    "author": "Regisseur Name",
    "type": "DVD",
    "reason": "Keine Treffer in Bibliothekskatalog",
    "added_at": "2025-01-15 14:30:00"
  }
]
```

### `recommended.md` - Export Format
```markdown
# 🎬📀📚 Empfehlungen der Stadtbibliothek Köln

**Erstellt am:** 21.10.2025 14:30:15

## 📊 Übersicht
- **🎬 Filme:** 6 Empfehlungen
- **🎵 Musik/Alben:** 6 Empfehlungen
- **📚 Bücher:** 6 Empfehlungen

## 🎬 Filme
### 1. Mulholland Drive
- **Regie:** David Lynch
- **Verfügbarkeit:** verfügbar in Zentralbibliothek
- **Quelle:** 🎬 BBC 100 Greatest Films of the 21st Century
```

## 🤝 Beitragen

### Neue Datenquellen hinzufügen
1. Neue Datei in `data_sources/` erstellen
2. Funktionen nach dem Pattern `fetch_[source]_[media]()`
3. Quellen-Konstante in `utils/sources.py` definieren
4. In `gui/app.py` integrieren

### Andere Bibliotheken unterstützen
1. `library/search.py` kopieren und anpassen
2. HTML-Parser für die neue Bibliothek implementieren
3. URL und Parameter anpassen

### Neue Features
1. Fork das Repository
2. Feature Branch erstellen: `git checkout -b feature-name`
3. Änderungen committen: `git commit -am 'Add feature'`
4. Push zum Branch: `git push origin feature-name`
5. Pull Request erstellen

## 🐛 Debugging

### Debug-Ausgaben aktivieren
Die App gibt bereits extensive Debug-Informationen in der Konsole aus:
```
DEBUG: Lade Datenquellen...
DEBUG: 100 Filme aus Cache geladen.
DEBUG: Analysiere MP3-Archiv für personalisierte Empfehlungen...
DEBUG: 42 verschiedene Interpreten gefunden
DEBUG: Initialisiere Empfehlungen...
DEBUG: Google-Suche für film: 'Mulholland Drive' von 'David Lynch'
⚫ Keine Treffer für 'Beispiel Album' - wird geblacklistet
```

### Häufige Probleme

**Keine Empfehlungen gefunden**
- Internet-Verbindung prüfen
- Bibliothekskatalog erreichbar? `https://katalog.stbib-koeln.de`
- Cache löschen: `rm data/*.json`
- Blacklist zurücksetzen: `rm data/blacklist_*.json`

**Google-Suche funktioniert nicht**
- Groq API Key gesetzt? Prüfen mit: `echo $GROQ_API_KEY` (Linux/Mac) oder `echo %GROQ_API_KEY%` (Windows)
- `secrets.env` Datei im Projektverzeichnis vorhanden?
- DuckDuckGo erreichbar?
- Firewall-Einstellungen prüfen

**MP3-Archiv wird nicht gefunden**
- Pfad in `data_sources/albums.py` und `data_sources/mp3_analysis.py` korrekt?
- Berechtigung zum Lesen des Ordners?
- Windows-Pfade mit doppelten Backslashes: `H:\\MP3 Archiv`

**Personalisierte Empfehlungen fehlen**
- MP3-Archiv-Pfade in beiden Dateien gesetzt?
- Mindestens 10 verschiedene Interpreten im Archiv?
- Cache löschen und neu laden: `rm data/albums.json`

**Zu viele wiederholte Suchanfragen**
- Blacklist-System sollte automatisch greifen
- Prüfen: `ls -la data/blacklist_*.json`
- Falls nötig manuell zurücksetzen

## 📄 Lizenz

MIT License - Siehe [LICENSE](LICENSE) für Details.

## 🙏 Danksagungen

- **BBC Culture** für die exzellente Filmliste
- **FBW** für die deutschen Qualitätsfilm-Bewertungen
- **Radio Eins** für die Musikempfehlungen
- **New York Times** für den Literatur-Kanon
- **Stadtbibliothek Köln** für den öffentlichen Katalog-Zugang
- **Gradio** für das fantastische UI-Framework
- **Groq** für die schnelle LLM-API
- **DuckDuckGo** für die kostenlose Suchfunktion

---

**Entwickelt mit ❤️ für Bibliotheksliebhaber und Medienentdecker**

## 📦 Release Notes

### Version 2.0.0 (Aktuell)
- ✨ **Personalisierte Musikempfehlungen**: Automatische Analyse deines MP3-Archivs
- 🎵 **Oscar-Filmmusik**: Alle Gewinner der besten Filmmusik integriert
- 📚 **Ratgeber**: Zusätzliche Buchkategorie mit den besten Ratgebern
- ⚫ **Intelligente Blacklist**: Automatisches Filtern nicht verfügbarer Medien
- 🏷️ **Quellen-Tracking**: Emoji-basierte Kennzeichnung aller Empfehlungen
- 🔍 **KI-Powered Search**: Google-Suche mit automatischer Zusammenfassung
- 💾 **Auto-Save**: Empfehlungen werden beim Start automatisch gespeichert
- 🎨 **Verbessertes UI**: Erfolgsmeldungen und besseres Feedback

### Version 1.0.0
- 🎬 Grundfunktionalität für Filme (BBC + FBW)
- 🎵 Musik-Empfehlungen (Radio Eins)
- 📚 Bücher (NYT Kanon)
- 🔍 Verfügbarkeitsprüfung
- 💾 Markdown-Export
