# 🎬📀📚 Bibliothek-Empfehlungs-App

Eine intelligente Empfehlungs-App für die **Stadtbibliothek Köln**, die verfügbare Filme, Alben und Bücher basierend auf kuratierten Listen hochwertiger Medien vorschlägt.

![Python](https://img.shields.io/badge/python-3.8+-blue.svg)
![Gradio](https://img.shields.io/badge/gradio-4.0+-green.svg)
![License](https://img.shields.io/badge/license-MIT-blue.svg)

## ✨ Features

### 🎯 **Intelligente Empfehlungen**
- **Filme**: Kombination aus
  - BBC Culture’s *100 Greatest Films of the 21st Century*
  - FBW-Filme mit „Prädikat besonders wertvoll“
  - Oscar-prämierte Filme („Bester Film“)
  - Automatische Zusammenführung und alphabetische Sortierung
  - Lokaler JSON-Cache für schnelleren Start
- **Musik**: Basiert auf Radio Eins Top 100 Alben 2019
- **Bücher**: Basiert auf *New York Times Kanon des 21. Jahrhunderts*  
  (von [die-besten-aller-zeiten.de](https://www.die-besten-aller-zeiten.de/buecher/kanon/new-york-times-21-jahrhundert.html))  
  Mit Autorenangaben und Beschreibungstexten

### 🔍 **Verfügbarkeitsprüfung**
- Automatische Suche im Online-Katalog der Stadtbibliothek Köln
- Nur verfügbare Medien werden vorgeschlagen
- Live-Verfügbarkeitsstatus für die Zentralbibliothek

### 🎮 **Interaktive GUI**
- **Mehrfachauswahl**: Mehrere Titel gleichzeitig auswählen und entfernen
- **Google-Suche**: 1-2 Sätze Zusammenfassung zu jedem Medium
- **Automatischer Start**: Vorschläge werden beim App-Start geladen
- **Persistente Ablehnungen**: Abgelehnte Titel werden nie wieder vorgeschlagen

### 💾 **Export-Funktionen**
- Empfehlungen als übersichtliche Markdown-Datei speichern
- Automatische Dokumentation mit Verfügbarkeitsstatus
- Zeitstempel und Kategorien-Übersicht

### 🧠 **Daten-Caching**
- Alle Film- und Albumdaten werden nach dem ersten Laden in `data/*.json` gespeichert
- Beim nächsten Start wird automatisch der Cache genutzt (schneller Start)
- Aktualisierung bei Änderungen an den Datenquellen möglich

### 🎵 **MP3-Archiv Integration**
- Filtert bereits vorhandene Alben aus dem lokalen MP3-Archiv
- Intelligente Fuzzy-Matching Algorithmen
- Normalisierung von Titel- und Künstlernamen

## 🚀 Installation

### Voraussetzungen
- Python 3.8 oder höher
- Internetverbindung für Bibliothekskatalog und Google-Suche

### 1. Repository klonen
```bash
git clone <repository-url>
cd library-recommender
```

### 2. Abhängigkeiten installieren
```bash
pip install -r requirements.txt
```

### 3. Groq API Key einrichten (optional, für Google-Suche)
Kostenlosen Account erstellen: https://groq.com

Erstelle eine secrets.env mit dem Eintrag GROQ_API_KEY=gsk_...

> **Hinweis**: Ohne Groq API Key funktioniert die Google-Suche nicht, alle anderen Features bleiben verfügbar.

### 4. MP3-Archiv Pfad anpassen (optional)
Bearbeiten Sie `data_sources/albums.py` und passen Sie den Pfad an:
```python
albums = filter_existing_albums(albums, "PFAD/ZU/IHREM/MP3/ARCHIV")
```

## 🎮 Verwendung

### App starten
```bash
python main.py
```

Die App öffnet sich automatisch im Browser unter `http://localhost:7860`

### 🎬 **Filme-Tab**
1. **Automatische Vorschläge** beim Start
2. **Film auswählen** → Google-Button wird aktiv
3. **🔍 Google-Suche** → Kurze Zusammenfassung wird angezeigt
4. **Mehrere Filme auswählen** → "Entfernen" → Neue Vorschläge

### 🎵 **Musik-Tab**
1. Nur Alben, die **nicht** in Ihrem MP3-Archiv sind
2. Gleiche Funktionalität wie Filme
3. Basiert auf Radio Eins Empfehlungen

### 📚 **Bücher-Tab**
1. Automatische Vorschläge aus dem *New York Times Kanon des 21. Jahrhunderts*
2. Jedes Buch enthält **Titel**, **Autor** und **Kurzbeschreibung**
3. Identische Interaktion wie bei Filmen und Musik:
   - Mehrfachauswahl
   - Entfernen und Neuvorschläge
   - Google-Suche zur weiteren Information

### 💾 **Empfehlungen speichern**
- **"Alle Empfehlungen speichern"** Button oben
- Erstellt `recommended.md` mit allen aktuellen Vorschlägen
- Übersichtliche Formatierung mit Verfügbarkeitsstatus

## 📁 Projektstruktur

```
library-recommender/
├── main.py                        # Hauptanwendung (Gradio UI)
├── requirements.txt               # Python-Abhängigkeiten
├── environment.yml                # Erstellung einer Anaconda Umgebung mit Python-Abhängigkeiten
├── README.md                      # Diese Datei
├── 
├── data/                          # Automatisch erstellte Daten
│   ├── films.json                 # Cache für Filme (BBC + FBW + Oscar, alphabetisch sortiert)
│   ├── albums.json                # Cache für Albumempfehlungen
│   ├── books.json                 # Cache für Bücher (New York Times Kanon, mit Beschreibung)
│   └── state.json                 # Abgelehnte Medien (persistent)
│
├── data_sources/                  # Datenquellen
│   ├── albums.py                  # Radio Eins Album-Liste
│   ├── films.py                   # BBC Culture Film-Liste
│   ├── fbw_films.py               # Deutsche Filme mit Prädikat „besonders wertvoll“ und Oscar-prämierte Filme (Bester Film)
│   └── books.py                   # NYT-Buchkanon (21. Jahrhundert, mit Beschreibung)
│
├── gui/                           # GUI
│   └── app.py                     # Hauptanwendung (Gradio UI)  
│
├── library/                       # Bibliothekskatalog-Integration
│   ├── search.py                  # Stadtbibliothek Köln Suchengine
│   └── parsers.py                 # Text-Normalisierung und Matching
│
├── preprocessing/                 # Datenaufbereitung
│   └── filters.py                 # MP3-Archiv Filterung
│
├── recommender/                   # Empfehlungslogik
│   ├── recommender.py             # Hauptempfehlungs-Engine
│   └── state.py                   # Zustandsverwaltung
│
└── utils/                         # Hilfsfunktionen
    ├── io.py                      # Datei I/O und Markdown-Export
    └── search_utils.py            # Google-Suche und Zusammenfassung
```

## ⚙️ Konfiguration

### MP3-Archiv Pfad
In `data_sources/albums.py` ändern:
```python
albums = filter_existing_albums(albums, "/path/to/your/mp3/archive")
```

### Bibliothekskatalog
Die App ist für die **Stadtbibliothek Köln** konfiguriert. Für andere Bibliotheken müsste `library/search.py` angepasst werden.

## 🔧 Technische Details

### Datenquellen
- **Filme (BBC)**: [BBC Culture’s 100 Greatest Films](https://de.wikipedia.org/wiki/BBC_Culture%E2%80%99s_100_Greatest_Films_of_the_21st_Century)
- **Filme (FBW)**: [Deutsche Filmbewertungsstelle – Prädikat besonders wertvoll](https://www.fbw-filmbewertung.com/filme)
- **Filme (Oscar)**: [Wikipedia – Oscar/Bester Film](https://de.wikipedia.org/wiki/Oscar/Bester_Film)
- **Musik**: [Radio Eins Die 100 besten Alben 2019](https://www.radioeins.de/musik/top_100/die-100-besten-2019/alben/)
- **Bücher**: [Die besten Bücher – New York Times Kanon des 21. Jahrhunderts](https://www.die-besten-aller-zeiten.de/buecher/kanon/new-york-times-21-jahrhundert.html)
- **Katalog**: [Stadtbibliothek Köln Online-Katalog](https://katalog.stbib-koeln.de)

### Algorithmen
- **Fuzzy Matching**: Intelligente Textnormalisierung für MP3-Archiv
- **Verfügbarkeitsprüfung**: Web Scraping des Bibliothekskatalogs
- **Suchvarianten**: Automatische Generierung alternativer Suchbegriffe

### APIs
- **DuckDuckGo Search**: Kostenlose Websuche
- **Groq API**: Schnelle LLM-Zusammenfassungen (gemma2-9b-it)

## 📊 Datenfiles

### `state.json` - Abgelehnte Medien
```json
{
  "films": [{"title": "Mulholland Drive"}],
  "albums": [{"title": "OK Computer"}],
  "books": []
}
```

### `recommended.md` - Export Format
```markdown
# 🎬📀📚 Empfehlungen der Stadtbibliothek Köln

**Erstellt am:** 21.09.2025 14:30:15

## 📊 Übersicht
- **🎬 Filme:** 4 Empfehlungen
- **🎵 Musik/Alben:** 4 Empfehlungen

## 🎬 Filme
### 1. Mulholland Drive
- **Regie:** David Lynch
- **Verfügbarkeit:** verfügbar in Zentralbibliothek
```

## 🤝 Beitragen

### Neue Datenquellen hinzufügen
1. Neue Datei in `data_sources/` erstellen
2. Funktionen nach dem Pattern `fetch_[source]_[media]()`
3. In `app.py` integrieren

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
DEBUG: Initialisiere Empfehlungen...
DEBUG: Google-Suche für film: 'Mulholland Drive' von 'David Lynch'
```

### Häufige Probleme

**Keine Empfehlungen gefunden**
- Internet-Verbindung prüfen
- Bibliothekskatalog erreichbar? `https://katalog.stbib-koeln.de`
- Cache löschen: `rm data/*.json`

**Google-Suche funktioniert nicht**
- Groq API Key gesetzt? `echo $GROQ_API_KEY`
- DuckDuckGo erreichbar?
- Firewall-Einstellungen prüfen

**MP3-Archiv wird nicht gefunden**
- Pfad in `data_sources/albums.py` korrekt?
- Berechtigung zum Lesen des Ordners?

## 📄 Lizenz

MIT License - Siehe [LICENSE](LICENSE) für Details.

## 🙏 Danksagungen

- **BBC Culture** für die exzellente Filmliste
- **Radio Eins** für die Musikempfehlungen  
- **Stadtbibliothek Köln** für den öffentlichen Katalog-Zugang
- **Gradio** für das fantastische UI-Framework
- **Groq** für die schnelle LLM-API

---

**Entwickelt mit ❤️ für Bibliotheksliebhaber und Medienentdecker**