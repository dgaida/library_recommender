# Changelog

Alle wichtigen Änderungen an diesem Projekt werden in dieser Datei dokumentiert.

Das Format basiert auf [Keep a Changelog](https://keepachangelog.com/de/1.0.0/),
und dieses Projekt folgt [Semantic Versioning](https://semver.org/lang/de/).

## [2.0.0] - 2025-01-20

### ✨ Hinzugefügt  
- **Personalisierte Musikempfehlungen**: Automatische Analyse des MP3-Archivs zur Identifikation von Top-Interpreten  
  - Neue Datei `data_sources/mp3_analysis.py` für Archiv-Analyse  
  - Findet die 10 meist gehörten Interpreten  
  - Sucht automatisch nach weiteren Alben dieser Künstler in der Bibliothek  
  - Emoji-Kennzeichnung mit 💎 für personalisierte Empfehlungen  
- **Oscar-Filmmusik Integration**: Alle Oscar-Gewinner der Kategorie "Beste Filmmusik"  
  - Neue Datei `data_sources/oscar_music.py`  
  - Automatische Integration in `albums.json`  
  - Quellen-Tracking mit 🎵 Emoji  
- **Ratgeber-Kategorie**: Zusätzliche Buchempfehlungen  
  - Neue Datei `data_sources/guides.py`  
  - Die besten Ratgeber des 21. Jahrhunderts  
  - Integration in Bücher-Tab  
- **Intelligentes Blacklist-System**: Performance-Optimierung  
  - Neue Datei `utils/blacklist.py`  
  - Speichert Medien ohne Bibliotheks-Treffer dauerhaft  
  - Vermeidet wiederholte erfolglose Suchanfragen  
  - Separate Blacklists für Filme, Alben und Bücher  
  - Statistik-Funktionen zur Überwachung  
- **Quellen-Tracking System**: Nachvollziehbare Empfehlungen  
  - Neue Datei `utils/sources.py` mit Quellen-Konstanten  
  - Emoji-basierte Kennzeichnung aller Empfehlungen  
  - 🏆 Oscar (Bester Film)  
  - 🎵 Oscar (Beste Filmmusik)  
  - ⭐ FBW Prädikat besonders wertvoll  
  - 🎬 BBC 100 Greatest Films  
  - 📻 Radio Eins Top 100  
  - 📚 New York Times Kanon  
  - 💎 Personalisierte Empfehlungen  
- **KI-gestützte Google-Suche**: Automatische Zusammenfassungen  
  - Neue Datei `utils/search_utils.py`  
  - Integration von DuckDuckGo Search API  
  - Groq LLM für 1-2 Satz Zusammenfassungen  
  - Google-Button pro Medium in der GUI  
- **Automatisches Speichern**: Empfehlungen beim App-Start  
  - Initiale Vorschläge werden automatisch in `recommended.md` gespeichert  
  - Zeitstempel und vollständige Metadaten  
- **Erfolgs-Feedback**: Visuelle Bestätigung in der GUI  
  - Grüne Erfolgsmeldungen nach Aktionen  
  - Temporäre Anzeige, verschwindet automatisch  
  - Verbesserte Benutzererfahrung  

### 🔄 Geändert  
- **Erweiterte Film-Datenquellen**: Zusätzlich zu BBC jetzt auch FBW und Oscar  
  - `data_sources/fbw_films.py` mit Web-Scraping der FBW-Seite  
  - Oscar-Integration mit allen "Bester Film"-Gewinnern  
  - Automatische Duplikats-Bereinigung und Sortierung  
- **Verbessertes Daten-Caching**: Strukturierte JSON-Dateien  
  - Alle Quellen werden in entsprechenden Cache-Dateien gespeichert  
  - Schnellerer Start durch intelligentes Caching  
- **Optimierte GUI-Performance**: Effizienteres Event-Handling  
  - Mehrfachauswahl ohne Performance-Einbußen  
  - Verbesserte Reaktionszeiten  
- **Detailliertere Debug-Ausgaben**: Besseres Tracking  
  - Konsolen-Ausgaben für alle wichtigen Operationen  
  - Blacklist-Status-Meldungen  
  - Quellen-Information bei jedem Vorschlag  

### 🐛 Behoben  
- **Duplikate in Empfehlungen**: Verschiedene Quellen führten zu Duplikaten  
  - Implementierung von Title-basiertem Deduplication  
  - Case-insensitive Vergleiche  
- **Wiederholte Suchanfragen**: Gleiche erfolglose Suchen mehrfach  
  - Blacklist-System verhindert wiederholte Nicht-Treffer-Suchen  
- **Fehlende Autor-Informationen**: Nicht alle Medien hatten Autor-Angaben  
  - Robustere Extraktion aus verschiedenen Quellen  
  - Fallback-Mechanismen  

### 🔒 Sicherheit  
- **API-Key-Verwaltung**: Sichere Speicherung in separater Datei  
  - `secrets.env` für Groq API Key  
  - Dotenv-Integration für Umgebungsvariablen  
  - `.gitignore` Eintrag für secrets.env  

## [1.0.0] - 2024-12-01

### ✨ Hinzugefügt  
- **Grundfunktionalität**: Erste Version der App  
  - Filmempfehlungen basierend auf BBC Culture Liste  
  - Musikempfehlungen von Radio Eins Top 100  
  - Buchempfehlungen aus New York Times Kanon  
- **Verfügbarkeitsprüfung**: Integration mit Stadtbibliothek Köln  
  - Web-Scraping des Bibliothekskatalogs  
  - Live-Verfügbarkeitscheck  
- **Interaktive GUI**: Gradio-basierte Benutzeroberfläche  
  - Drei separate Tabs für Filme, Musik, Bücher  
  - Mehrfachauswahl von Medien  
  - Ablehnen und Neuvorschläge  
- **Persistente Ablehnungen**: State-Management  
  - `state.json` für abgelehnte Medien  
  - Automatisches Laden beim Start  
- **Markdown-Export**: Speichern von Empfehlungen  
  - `recommended.md` mit übersichtlicher Formatierung  
  - Verfügbarkeitsstatus inklusive  
- **MP3-Archiv-Filterung**: Duplikatserkennung für Musik  
  - Fuzzy-Matching-Algorithmen  
  - Normalisierung von Titel- und Künstlernamen  

### 🏗️ Architektur  
- Modulare Struktur mit separaten Packages:  
  - `data_sources/`: Datenquellen-Module  
  - `gui/`: Gradio-App  
  - `library/`: Bibliotheks-Integration  
  - `preprocessing/`: Datenaufbereitung  
  - `recommender/`: Empfehlungslogik  
  - `utils/`: Hilfsfunktionen  
- Python 3.8+ Kompatibilität  
- Requirements-Management mit pip und conda  

---

## Geplante Features (Roadmap)

### Version 2.1.0  
- [ ] Multi-Bibliothek-Support (andere Städte)  
- [ ] Erweiterte Filteroptionen (Genre, Jahr, Bewertung)  
- [ ] Watchlist/Merkliste-Funktion  
- [ ] Export in andere Formate (PDF, CSV)  

### Version 2.2.0  
- [ ] Benutzerprofile und Präferenzen  
- [ ] Empfehlungs-Algorithmus mit Machine Learning  
- [ ] Benachrichtigungen bei Verfügbarkeit  
- [ ] Mobile App (iOS/Android)  

### Version 3.0.0  
- [ ] Kollaborative Filter-Empfehlungen  
- [ ] Social Features (Teilen, Bewerten)  
- [ ] API für Drittanbieter  
- [ ] Cloud-Synchronisation  
- [ ] Nutzung von [OpenLibrary API](https://openlibrary.org/developers/api)  

---

## Upgrade-Hinweise

### Von 1.x auf 2.0  
1. **Neue Abhängigkeiten installieren**:  
   ```bash
   pip install -r requirements.txt
   ```

2. **Neue Konfigurationen** (optional):  
   - `secrets.env` für Groq API Key erstellen  
   - MP3-Archiv-Pfade in beiden Dateien aktualisieren:  
     - `data_sources/albums.py`  
     - `data_sources/mp3_analysis.py`  

3. **Cache neu aufbauen** (empfohlen):  
   ```bash
   rm data/*.json
   python main.py
   ```

4. **Blacklist-System**: Läuft automatisch, keine Aktion nötig  

---

## Mitwirkende

- **dgaida** - Hauptentwickler und Maintainer  

Danke an alle, die Issues gemeldet und Feature-Requests eingereicht haben!

---

## Links

- [GitHub Repository](https://github.com/dgaida/library_recommender)  
- [Issue Tracker](https://github.com/dgaida/library_recommender/issues)  
- [Releases](https://github.com/dgaida/library_recommender/releases)  
- [Stadtbibliothek Köln](https://www.stbib-koeln.de/)  
