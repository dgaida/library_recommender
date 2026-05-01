# 🎬📀📚 Bibliothek-Empfehlungs-App

Eine intelligente Empfehlungs-App für die **Stadtbibliothek Köln**, die verfügbare Filme, Alben und Bücher basierend auf kuratierten Listen hochwertiger Medien vorschlägt.

![Python](https://img.shields.io/badge/python-3.9+-blue.svg)
[![Version](https://img.shields.io/github/v/tag/dgaida/library_recommender?label=version)](https://github.com/dgaida/library_recommender/tags)
![Gradio](https://img.shields.io/badge/gradio-4.0+-green.svg)
![License](https://img.shields.io/badge/license-MIT-blue.svg)
[![Tests](https://github.com/dgaida/library_recommender/actions/workflows/tests.yml/badge.svg)](https://github.com/dgaida/library_recommender/actions/workflows/tests.yml)
[![Code Quality](https://github.com/dgaida/library_recommender/actions/workflows/lint.yml/badge.svg)](https://github.com/dgaida/library_recommender/actions/workflows/lint.yml)
[![CodeQL](https://github.com/dgaida/library_recommender/actions/workflows/codeql.yml/badge.svg)](https://github.com/dgaida/library_recommender/actions/workflows/codeql.yml)
[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)
[![Ruff](https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/astral-sh/ruff/main/assets/badge/v2.json)](https://github.com/astral-sh/ruff)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![codecov](https://codecov.io/gh/dgaida/library_recommender/branch/main/graph/badge.svg)](https://codecov.io/gh/dgaida/library_recommender)
[![Maintenance](https://img.shields.io/badge/Maintained%3F-yes-green.svg)](https://github.com/dgaida/library_recommender/graphs/commit-activity)
![Last commit](https://img.shields.io/github/last-commit/dgaida/library_recommender)
[![Docs](https://img.shields.io/badge/docs-GitHub%20Pages-blue)](https://dgaida.github.io/library_recommender/)

## ✨ Features

### 🎯 **Intelligente Empfehlungen**

#### 🎬 **Filme** - Premium-Quellen kombiniert  
- **BBC Culture**: *100 Greatest Films of the 21st Century*  
- **FBW**: Deutsche Filme mit Prädikat „besonders wertvoll"  
- **Oscar**: Alle Gewinner „Bester Film"  

#### 🎵 **Musik** - Vielfältige Quellen  
- **Radio Eins**: Top 100 Alben 2019  
- **Oscar**: Beste Filmmusik aller Zeiten  
- **💎 Personalisiert**: Basierend auf deinem MP3-Archiv (analysiert deine Top-30-Interpreten)  

#### 📚 **Bücher & Ratgeber** - Hochwertige Literatur  
- **New York Times**: Kanon des 21. Jahrhunderts  
- **📖 Die besten Ratgeber**: Sachbücher des 21. Jahrhunderts  

### 🔍 **Live-Verfügbarkeitsprüfung**  
- Automatische Suche im Online-Katalog der Stadtbibliothek Köln  
- Echtzeit-Status der Zentralbibliothek  
- **Intelligente Blacklist**: Medien ohne Treffer werden gespeichert  

### 💎 **Personalisierte Empfehlungen**  
- **MP3-Archiv-Analyse**: Erkennt automatisch deine Lieblingskünstler  
- **Top-30-Tracking**: Identifiziert deine meist gehörten Interpreten  
- **Neue Alben**: Sucht gezielt nach weiteren Werken deiner Favoriten  

### 🎮 **Moderne Benutzeroberfläche**  
- **Mehrfachauswahl**: Mehrere Titel gleichzeitig verwalten  
- **🏷️ Quellen-Emojis**: Zeigen Herkunft jeder Empfehlung (🏆 Oscar, ⭐ FBW, 📻 Radio, 💎 Personalisiert, 📖 Ratgeber)  
- **🔍 KI-Google-Suche**:  
  - 1-2 Sätze Zusammenfassung zu jedem Medium  
  - 🎬 YouTube-Trailer für Filme  
  - 🖼️ Cover-Images für alle Medien  
- **Persistente Ablehnungen**: Abgelehnte Titel nie wieder angezeigt  

<p align="center">
   <img src="images/GUI%20Bibliothek%20Filme.png"
       alt="Screenshot der Bibliothek GUI - Tab Filme"
       width="800">
   </p>

### 💾 **Export & Caching**  
- Empfehlungen als übersichtliche Markdown-Datei  
- Automatisches Speichern beim App-Start  
- Intelligentes Caching aller Datenquellen  

## 🚀 Installation

### Voraussetzungen  
- Python 3.9 oder höher  
- Internetverbindung  

### 1. Repository klonen
```bash
git clone https://github.com/dgaida/library_recommender.git
cd library_recommender
```

### 2. Abhängigkeiten installieren
```bash
pip install -r requirements.txt
```

### 3. Groq API Key einrichten (optional, für Google-Suche mit visuellen Medien)
Kostenlosen Account erstellen: https://groq.com

Erstelle eine `secrets.env` mit:
```
GROQ_API_KEY=gsk_...
```

> **Hinweis**: Ohne Groq API Key funktioniert die Google-Suche mit Zusammenfassungen,
> Trailer-Suche und Cover-Images nicht. Alle anderen Features bleiben verfügbar.

### 4. MP3-Archiv Pfad anpassen (optional)
Für personalisierte Musikempfehlungen bearbeite `data_sources/mp3_analysis.py`:
```python
add_top_artist_albums_to_collection("PFAD/ZU/DEINEM/MP3/ARCHIV", top_n=30)
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

### Workflow  
1. **Automatische Vorschläge** beim Start mit Quellen-Emojis (dynamisch 5 pro Quelle)  
2. **Medium auswählen** → Google-Button wird aktiv  
3. **🔍 Google-Suche** →  
   - KI-generierte Kurzzusammenfassung (1-2 Sätze)  
   - 🎬 YouTube-Trailer (nur Filme)  
   - 🖼️ Cover-Image (alle Medien)  
4. **Mehrere auswählen** → "Entfernen" → Neue Vorschläge automatisch nachgeladen  
5. **"Alle Empfehlungen speichern"** → Erstellt `recommended.md`  
   - Filme werden nach Genre sortiert  

## 📁 Projektstruktur

```
library_recommender/
├── main.py                        # Hauptanwendung (Gradio UI)
├── requirements.txt               # Python-Abhängigkeiten
├── README.md                      # Diese Datei
├── CONTRIBUTING.md                # Richtlinien für Beiträge
├── CHANGELOG.md                   # Änderungshistorie
│
├── data/                          # Automatisch erstellte Daten
│   ├── films.json                 # Cache: BBC + FBW + Oscar
│   ├── albums.json                # Cache: Radio Eins + Oscar + Personalisiert
│   ├── books.json                 # Cache: NYT Kanon + Ratgeber
│   ├── state.json                 # Abgelehnte Medien
│   └── blacklist_*.json           # Nicht verfügbare Medien
│
├── data_sources/                  # Datenquellen-Module
│   ├── films.py                   # BBC Culture Film-Liste
│   ├── fbw_films.py               # FBW + Oscar-Filme
│   ├── oscar_music.py             # Oscar-Filmmusik
│   ├── mp3_analysis.py            # MP3-Archiv Analyse & Top-Interpreten
│   ├── albums.py                  # Radio Eins Album-Liste
│   ├── books.py                   # NYT-Buchkanon
│   └── guides.py                  # Ratgeber des 21. Jahrhunderts
│
├── gui/                           # Grafische Benutzeroberfläche
│   └── app.py                     # Gradio-App
│
├── library/                       # Bibliotheks-Integration
│   ├── search.py                  # Stadtbibliothek Köln Suchengine
│   └── parsers.py                 # Text-Normalisierung & Fuzzy-Matching
│
├── preprocessing/                 # Datenaufbereitung
│   └── filters.py                 # MP3-Archiv Filterung & Duplikatserkennung
│
├── recommender/                   # Empfehlungslogik
│   ├── recommender.py             # Haupt-Engine mit Blacklist-Integration
│   └── state.py                   # Zustandsverwaltung
│
└── utils/                         # Hilfsfunktionen
    ├── io.py                      # Datei I/O & Markdown-Export
    ├── search_utils.py            # Google-Suche & KI-Zusammenfassung
    ├── sources.py                 # Quellen-Konstanten & Emoji-Mapping
    ├── blacklist.py               # Blacklist-Verwaltung
    ├── artist_blacklist.py        # Artist-Blacklist für MP3-Analyse
    └── logging_config.py          # Zentrales Logging
```

## ⚙️ Konfiguration

### MP3-Archiv Pfad
In `data_sources/albums.py` und `data_sources/mp3_analysis.py` ändern:
```python
albums = filter_existing_albums(albums, "/path/to/your/mp3/archive")
add_top_artist_albums_to_collection("/path/to/your/mp3/archive", top_n=30)
```

### Anzahl Top-Interpreten
In `data_sources/mp3_analysis.py`:
```python
add_top_artist_albums_to_collection("H:\\MP3 Archiv", top_n=40)  # Standard: 30
```

## 🔧 Technische Details

### Datenquellen  
- **Filme**: [BBC Culture](https://de.wikipedia.org/wiki/BBC_Culture%E2%80%99s_100_Greatest_Films_of_the_21st_Century), [FBW](https://www.fbw-filmbewertung.com/filme), [Oscar](https://de.wikipedia.org/wiki/Oscar/Bester_Film)  
- **Musik**: [Radio Eins](https://www.radioeins.de/musik/top_100/die-100-besten-2019/alben/), [Oscar Filmmusik](https://de.wikipedia.org/wiki/Oscar/Beste_Filmmusik)  
- **Bücher**: [NYT Kanon](https://www.die-besten-aller-zeiten.de/buecher/kanon/new-york-times-21-jahrhundert.html), [Ratgeber](https://www.die-besten-aller-zeiten.de/buecher/kanon/buecher-des-21-jahrhunderts.html)  
- **Katalog**: [Stadtbibliothek Köln](https://katalog.stbib-koeln.de)  

### Algorithmen  
- **Fuzzy Matching**: Intelligente Textnormalisierung für MP3-Archiv-Abgleich  
- **Blacklist-System**: Permanente Speicherung von Nicht-Treffern  
- **Top-Interpreten-Analyse**: Zählt Songs pro Künstler im MP3-Archiv  
- **Balancierte Empfehlungen**: Gleichmäßige Verteilung aus allen Quellen (z.B. 5 pro Quelle)  

### APIs & Libraries  
- **DuckDuckGo Search**: Kostenlose Websuche  
- **Groq API**: Schnelle LLM-Zusammenfassungen  
- **BeautifulSoup**: HTML-Parsing für Web Scraping  
- **Gradio**: Moderne Web-UI  

## 🤝 Beitragen

Beiträge sind willkommen! Bitte lies [CONTRIBUTING.md](CONTRIBUTING.md) für Details.

### Neue Datenquellen hinzufügen  
1. Neue Datei in `data_sources/` erstellen  
2. Quellen-Konstante in `utils/sources.py` definieren (inkl. Emoji)  
3. In `gui/app.py` integrieren  

## 🐛 Debugging

### Häufige Probleme

**Keine Empfehlungen gefunden**  
- Internet-Verbindung prüfen  
- Cache löschen: `rm data/*.json`  
- Blacklist zurücksetzen: `rm data/blacklist_*.json`  

**Google-Suche funktioniert nicht**  
- Groq API Key gesetzt? `secrets.env` vorhanden?  
- DuckDuckGo erreichbar?  

**MP3-Archiv wird nicht gefunden**  
- Pfad korrekt in `data_sources/albums.py` und `data_sources/mp3_analysis.py`?  
- Windows-Pfade mit doppelten Backslashes: `H:\\MP3 Archiv`  

## 🧪 Tests

```bash
# Alle Tests
pytest tests/ -v

# Mit Coverage
pytest tests/ --cov=.

# Einzelne Datei
pytest tests/test_filters.py -v
```

**CI/CD**: Tests laufen automatisch bei Push/PR auf GitHub Actions (Python 3.9, 3.10, 3.11)

## 📄 Lizenz

MIT License - Siehe [LICENSE](LICENSE) für Details.

## 🙏 Danksagungen

- **BBC Culture, FBW, Oscar** für exzellente Film-Listen  
- **Radio Eins** für Musikempfehlungen  
- **New York Times** für Literatur-Kanon  
- **die-besten-aller-zeiten.de** für Ratgeber-Listen  
- **Stadtbibliothek Köln** für öffentlichen Katalog-Zugang  
- **Gradio, Groq, DuckDuckGo** für fantastische Tools  

---

**Entwickelt mit ❤️ für Bibliotheksliebhaber und Medienentdecker**

## 📦 Version

**Aktuelle Version:** 2.0.0 - *Personalized Recommendations* (20.01.2025)

### Highlights  
- 💎 Personalisierte Musikempfehlungen aus MP3-Archiv  
- 🎵 Oscar-Filmmusik Integration  
- 📖 Ratgeber-Kategorie  
- ⚫ Intelligente Blacklist-Systeme  
- 🏷️ Quellen-Tracking mit Emojis  
- 🔍 KI-Powered Google-Suche  

Details: [CHANGELOG.md](CHANGELOG.md)
