# 🎵 Artist-Blacklist System - Dokumentation

## Übersicht

Das Artist-Blacklist System verhindert wiederholte erfolglose Suchanfragen für Künstler, für die keine neuen CDs in der Bibliothek verfügbar sind.

### Kernfunktionalität

- **Automatische Blacklistung**: Künstler ohne verfügbare CDs werden geblacklistet  
- **Jährlicher Re-Check**: Nach 365 Tagen erfolgt automatisch eine erneute Überprüfung  
- **Top-10-Nachrücken**: Geblacklistete Künstler werden übersprungen, weitere rücken nach  
- **Persistente Speicherung**: Alle Daten werden in `data/blacklist_artists.json` gespeichert  

---

## 📋 Datenstruktur

### blacklist_artists.json Format

```json
{
  "radiohead": {
    "artist_name": "Radiohead",
    "song_count": 42,
    "reason": "Keine neuen CDs in Bibliothek gefunden",
    "added_at": "2025-01-15T14:30:00",
    "last_checked": "2025-01-15T14:30:00",
    "check_count": 1
  },
  "pink floyd": {
    "artist_name": "Pink Floyd",
    "song_count": 38,
    "reason": "Keine neuen CDs in Bibliothek gefunden",
    "added_at": "2024-03-20T10:15:00",
    "last_checked": "2025-01-10T11:00:00",
    "check_count": 3
  }
}
```

### Felder-Beschreibung

| Feld | Typ | Beschreibung |
|------|-----|--------------|
| `artist_name` | string | Original-Schreibweise des Künstlernamens |
| `song_count` | integer | Anzahl Songs im MP3-Archiv |
| `reason` | string | Grund für die Blacklistung |
| `added_at` | ISO datetime | Zeitpunkt der ersten Blacklistung |
| `last_checked` | ISO datetime | Zeitpunkt der letzten Überprüfung |
| `check_count` | integer | Anzahl durchgeführter Checks |

---

## 🔧 API-Referenz

### ArtistBlacklist Klasse

#### `__init__()`

```python
blacklist = ArtistBlacklist()
```

Initialisiert die Blacklist und lädt existierende Daten.

#### `is_blacklisted(artist_name: str) -> bool`

```python
if blacklist.is_blacklisted("Radiohead"):
    print("Künstler ist geblacklistet")
```

Prüft, ob ein Künstler auf der Blacklist steht **und** der letzte Check < 365 Tage zurückliegt.

**Returns:**  
- `True`: Künstler ist geblacklistet, Re-Check noch nicht fällig  
- `False`: Künstler nicht geblacklistet oder Re-Check fällig  

#### `add_to_blacklist(artist_name: str, song_count: int, reason: str)`

```python
blacklist.add_to_blacklist(
    "Pink Floyd",
    38,
    "Keine neuen CDs in Bibliothek gefunden"
)
```

Fügt einen Künstler zur Blacklist hinzu oder aktualisiert existierenden Eintrag.

**Args:**  
- `artist_name`: Name des Künstlers  
- `song_count`: Anzahl Songs im MP3-Archiv  
- `reason`: Grund für die Blacklistung  

#### `remove_from_blacklist(artist_name: str) -> bool`

```python
removed = blacklist.remove_from_blacklist("Radiohead")
if removed:
    print("Erfolgreich entfernt")
```

Entfernt einen Künstler von der Blacklist.

**Returns:** `True` wenn entfernt, `False` wenn nicht gefunden

#### `get_artists_due_for_recheck() -> List[Dict[str, Any]]`

```python
due_artists = blacklist.get_artists_due_for_recheck()

for artist in due_artists:
    print(f"{artist['artist_name']}: {artist['days_since_check']} Tage")
```

Gibt alle Künstler zurück, die für einen Re-Check fällig sind (> 365 Tage).

**Returns:** Liste von Artist-Dictionaries mit Re-Check-Status

#### `get_stats() -> Dict[str, Any]`

```python
stats = blacklist.get_stats()

print(f"Gesamt: {stats['total_artists']}")
print(f"Fällig für Re-Check: {stats['due_for_recheck']}")
print(f"Neue (30 Tage): {stats['recent_additions']}")
```

Gibt Statistiken über die Blacklist zurück.

**Returns:** Dictionary mit:  
- `total_artists`: Gesamtzahl geblacklisteter Künstler  
- `due_for_recheck`: Anzahl Künstler fällig für Re-Check  
- `recent_additions`: Neue Einträge der letzten 30 Tage  
- `most_checked`: Top 5 am häufigsten geprüfte Künstler  

#### `clear_old_entries(days: int = 730) -> int`

```python
removed_count = blacklist.clear_old_entries(days=730)
print(f"{removed_count} alte Einträge entfernt")
```

Entfernt Einträge älter als die angegebenen Tage.

**Args:**  
- `days`: Maximales Alter in Tagen (default: 730 = 2 Jahre)  

**Returns:** Anzahl entfernter Einträge

---

### Hilfsfunktionen

#### `get_filtered_top_artists()`

```python
from collections import Counter

artist_counter = Counter({
    "Artist A": 100,
    "Artist B": 90,
    "Artist C": 80
})

blacklist = ArtistBlacklist()
blacklist.add_to_blacklist("Artist B", 90)

top_artists = get_filtered_top_artists(
    artist_counter,
    blacklist,
    top_n=10,
    max_total=20
)

# Ergebnis: [("Artist A", 100), ("Artist C", 80)]
# Artist B wurde übersprungen
```

Gibt die Top N Künstler zurück, **ohne** geblacklistete Künstler.

**Args:**  
- `artist_counter`: Counter mit Anzahl Songs pro Künstler  
- `artist_blacklist`: ArtistBlacklist-Instanz  
- `top_n`: Gewünschte Anzahl Top-Künstler  
- `max_total`: Maximale Anzahl zu prüfender Künstler  

**Returns:** Liste von (Künstler, Anzahl) Tupeln

#### `update_artist_blacklist_from_search_results()`

```python
update_artist_blacklist_from_search_results(
    artist_name="Radiohead",
    song_count=42,
    found_new_albums=False,  # Keine neuen Alben gefunden
    artist_blacklist=blacklist
)
# → Künstler wird geblacklistet

update_artist_blacklist_from_search_results(
    artist_name="Pink Floyd",
    song_count=38,
    found_new_albums=True,  # Neue Alben gefunden!
    artist_blacklist=blacklist
)
# → Künstler wird von Blacklist entfernt (falls vorhanden)
```

Aktualisiert die Blacklist basierend auf Suchergebnissen.

**Args:**  
- `artist_name`: Name des Künstlers  
- `song_count`: Anzahl Songs im MP3-Archiv  
- `found_new_albums`: True wenn neue Alben gefunden wurden  
- `artist_blacklist`: ArtistBlacklist-Instanz  

#### `get_artist_blacklist()` (Singleton)

```python
# Erste Instanz
blacklist1 = get_artist_blacklist()

# Zweite "Instanz" - identisch mit erster
blacklist2 = get_artist_blacklist()

assert blacklist1 is blacklist2  # True
```

Gibt die globale Artist-Blacklist-Instanz zurück (Singleton-Pattern).

---

## 💡 Verwendungsbeispiele

### Beispiel 1: Grundlegende Verwendung

```python
from utils.artist_blacklist import ArtistBlacklist

# Initialisieren
blacklist = ArtistBlacklist()

# Künstler hinzufügen
blacklist.add_to_blacklist("Radiohead", 42)

# Prüfen
if blacklist.is_blacklisted("Radiohead"):
    print("Überspringe Radiohead - keine neuen CDs verfügbar")
else:
    print("Suche nach Radiohead-Alben...")
```

### Beispiel 2: Integration in MP3-Analyse

```python
from collections import Counter
from utils.artist_blacklist import (
    get_artist_blacklist,
    get_filtered_top_artists
)

# Analysiere MP3-Archiv
artist_counter = Counter({
    "Radiohead": 42,
    "Pink Floyd": 38,
    "The Beatles": 50,
    "Queen": 35
})

# Hole Blacklist
blacklist = get_artist_blacklist()

# Hole gefilterte Top-10 (ohne geblacklistete)
top_artists = get_filtered_top_artists(
    artist_counter,
    blacklist,
    top_n=10,
    max_total=20  # Prüfe bis zu 20 Kandidaten
)

print(f"Top-10 (nach Filterung): {len(top_artists)} Künstler")

for artist, song_count in top_artists:
    print(f"  - {artist}: {song_count} Songs")
    # Suche nach neuen Alben für diesen Künstler...
```

### Beispiel 3: Nach Alben-Suche aktualisieren

```python
from utils.artist_blacklist import (
    get_artist_blacklist,
    update_artist_blacklist_from_search_results
)

blacklist = get_artist_blacklist()

# Für jeden Top-Künstler
for artist, song_count in top_artists:
    # Suche in Bibliothek
    found_albums = search_artist_albums_in_library(artist)

    # Prüfe ob neue Alben (die nicht im MP3-Archiv sind)
    new_albums = filter_existing_albums(found_albums, mp3_archive_path)

    # Aktualisiere Blacklist
    update_artist_blacklist_from_search_results(
        artist,
        song_count,
        found_new_albums=len(new_albums) > 0,
        artist_blacklist=blacklist
    )
```

### Beispiel 4: Wartung durchführen

```python
from utils.artist_blacklist import get_artist_blacklist

blacklist = get_artist_blacklist()

# Entferne sehr alte Einträge (> 2 Jahre)
removed = blacklist.clear_old_entries(days=730)
print(f"{removed} alte Einträge entfernt")

# Zeige Statistiken
blacklist.print_stats()

# Liste Künstler für Re-Check
due_artists = blacklist.get_artists_due_for_recheck()

for artist in due_artists:
    print(f"Re-Check fällig: {artist['artist_name']}")
    # Führe Re-Check durch...
```

---

## 🔄 Workflow-Diagramm

```
┌─────────────────────────────────────────────────────────────┐
│ START: Personalisierte Album-Empfehlungen                  │
└────────────────────┬────────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────────┐
│ 1. Analysiere MP3-Archiv                                    │
│    └─> Zähle Songs pro Künstler                            │
└────────────────────┬────────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────────┐
│ 2. Lade Artist-Blacklist                                    │
│    └─> Prüfe welche Künstler geblacklistet sind           │
└────────────────────┬────────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────────┐
│ 3. Hole gefilterte Top-10 Künstler                         │
│    ├─> Überspringe geblacklistete (< 365 Tage)            │
│    ├─> Inkludiere Re-Check-fällige (≥ 365 Tage)           │
│    └─> Rücke weitere Künstler nach                         │
└────────────────────┬────────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────────┐
│ 4. Für jeden Top-10 Künstler:                              │
│    ├─> Suche in Bibliothekskatalog                         │
│    ├─> Filtere bereits vorhandene Alben                    │
│    └─> Sammle neue Alben                                   │
└────────────────────┬────────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────────┐
│ 5. Aktualisiere Artist-Blacklist:                          │
│    ├─> Neue Alben gefunden?                                │
│    │   ├─> JA: Entferne von Blacklist                      │
│    │   └─> NEIN: Auf Blacklist setzen/aktualisieren        │
│    └─> Speichere Datum des Checks                          │
└────────────────────┬────────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────────┐
│ 6. Speichere neue Alben in albums.json                     │
└────────────────────┬────────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────────┐
│ ENDE: Empfehlungen verfügbar                               │
└─────────────────────────────────────────────────────────────┘
```

---

## 📊 Szenarien & Beispiele

### Szenario 1: Erster Durchlauf (keine Blacklist)

**Ausgangssituation:**  
- MP3-Archiv mit 15 Künstlern analysiert  
- Keine Artist-Blacklist vorhanden  
- Top 3: Radiohead (42 Songs), Pink Floyd (38), Beatles (50)  

**Ablauf:**

```python
# 1. Analysiere Archiv
artist_counter = analyze_mp3_archive("H:\\MP3 Archiv")
# → Counter({'Beatles': 50, 'Radiohead': 42, 'Pink Floyd': 38, ...})

# 2. Lade Blacklist (leer)
blacklist = get_artist_blacklist()
# → blacklist.blacklist = {}

# 3. Hole gefilterte Top-10
top_artists = get_filtered_top_artists(artist_counter, blacklist, top_n=10)
# → [('Beatles', 50), ('Radiohead', 42), ('Pink Floyd', 38), ...]

# 4. Suche für jeden Künstler
# Beatles: 3 neue Alben gefunden
# Radiohead: 0 neue Alben gefunden
# Pink Floyd: 1 neues Album gefunden

# 5. Aktualisiere Blacklist
# Beatles: NICHT geblacklistet (neue Alben gefunden)
# Radiohead: AUF BLACKLIST (keine neuen Alben)
# Pink Floyd: NICHT geblacklistet (neue Alben gefunden)
```

**Ergebnis:**
```json
{
  "radiohead": {
    "artist_name": "Radiohead",
    "song_count": 42,
    "added_at": "2025-01-15T14:30:00",
    "last_checked": "2025-01-15T14:30:00",
    "check_count": 1
  }
}
```

### Szenario 2: Zweiter Durchlauf (mit Blacklist)

**Ausgangssituation:**  
- Radiohead ist auf Blacklist (seit 100 Tagen)  
- Neue Top-Künstler: U2 (25 Songs), Queen (35 Songs)  

**Ablauf:**

```python
# 1. Analysiere Archiv
artist_counter = analyze_mp3_archive("H:\\MP3 Archiv")

# 2. Lade Blacklist
blacklist = get_artist_blacklist()
# → Radiohead auf Blacklist (100 Tage alt)

# 3. Hole gefilterte Top-10
top_artists = get_filtered_top_artists(artist_counter, blacklist, top_n=10)
# → Radiohead wird ÜBERSPRUNGEN (< 365 Tage)
# → U2 und Queen rücken nach

# Ergebnis: [('Beatles', 50), ('Pink Floyd', 38), ('U2', 25), ('Queen', 35), ...]
```

**Logging-Output:**
```
INFO: Filtere Top 10 Künstler, prüfe maximal 30 Kandidaten
DEBUG: Überspringe 'Radiohead' (geblacklistet, 42 Songs)
DEBUG: Akzeptiert: 'Beatles' (50 Songs) - Position 1
DEBUG: Akzeptiert: 'Pink Floyd' (38 Songs) - Position 2
DEBUG: Akzeptiert: 'U2' (25 Songs) - Position 3
DEBUG: Akzeptiert: 'Queen' (35 Songs) - Position 4
INFO: Gefilterte Top 4: 5 geprüft, 1 übersprungen
```

### Szenario 3: Re-Check nach 1 Jahr

**Ausgangssituation:**  
- Radiohead seit 400 Tagen auf Blacklist  
- Re-Check ist fällig  

**Ablauf:**

```python
# 1. Prüfe Blacklist-Status
is_blacklisted = blacklist.is_blacklisted("Radiohead")
# → False (Re-Check fällig, da > 365 Tage)

# 2. Radiohead ist in gefilterten Top-10
top_artists = get_filtered_top_artists(artist_counter, blacklist, top_n=10)
# → Radiohead ist INKLUDIERT (Re-Check fällig)

# 3. Suche erneut nach Alben
found_albums = search_artist_albums_in_library("Radiohead")
# → 2 neue Alben gefunden!

# 4. Aktualisiere Blacklist
update_artist_blacklist_from_search_results(
    "Radiohead", 42, found_new_albums=True, artist_blacklist=blacklist
)
# → Radiohead wird VON BLACKLIST ENTFERNT
```

**Logging-Output:**
```
INFO: Re-Check fällig für 'Radiohead': 400 Tage seit letztem Check
INFO: Suche nach Alben von 'Radiohead'...
INFO: 15 Alben von 'Radiohead' gefunden
INFO: 🎉 'Radiohead' von Blacklist entfernt - neue Alben gefunden!
```

---

## 🔍 Monitoring & Debugging

### Log-Ausgaben verstehen

```log
# Künstler wird geblacklistet
INFO: ⚫ 'Artist Name' auf Blacklist gesetzt - keine neuen Alben verfügbar

# Künstler wird von Blacklist entfernt
INFO: 🎉 'Artist Name' von Blacklist entfernt - neue Alben gefunden!

# Re-Check ist fällig
INFO: Re-Check fällig für 'Artist Name': 400 Tage seit letztem Check

# Künstler wird übersprungen
DEBUG: Überspringe 'Artist Name' (geblacklistet, 42 Songs)

# Künstler wird akzeptiert
DEBUG: Akzeptiert: 'Artist Name' (42 Songs) - Position 5
```

### Blacklist-Status prüfen

```python
from utils.artist_blacklist import get_artist_blacklist

blacklist = get_artist_blacklist()

# Zeige Statistiken
blacklist.print_stats()
```

**Output:**
```
============================================================
ARTIST-BLACKLIST STATISTIKEN
============================================================
Gesamt geblacklistete Künstler: 5
Fällig für Re-Check: 2
Neue Einträge (letzte 30 Tage): 1

Am häufigsten geprüft:
  - Radiohead: 3x geprüft
  - Pink Floyd: 2x geprüft
  - U2: 1x geprüft
============================================================
```

### Liste Re-Check-fällige Künstler

```python
due_artists = blacklist.get_artists_due_for_recheck()

for artist in due_artists:
    print(f"Artist: {artist['artist_name']}")
    print(f"  Tage seit Check: {artist['days_since_check']}")
    print(f"  Letzter Check: {artist['last_checked']}")
    print(f"  Anzahl Checks: {artist['check_count']}")
    print(f"  Songs: {artist['song_count']}")
```

---

## ⚙️ Konfiguration

### Anpassbare Parameter

```python
# In utils/artist_blacklist.py

# Re-Check Intervall (default: 365 Tage = 1 Jahr)
RECHECK_INTERVAL_DAYS: int = 365

# Ändern für häufigere Checks:
RECHECK_INTERVAL_DAYS = 180  # 6 Monate

# Oder seltener:
RECHECK_INTERVAL_DAYS = 730  # 2 Jahre
```

### Alte Einträge bereinigen

```python
# Automatische Bereinigung bei Wartung
def perform_artist_blacklist_maintenance():
    blacklist = get_artist_blacklist()

    # Entferne Einträge älter als 2 Jahre
    removed = blacklist.clear_old_entries(days=730)

    # Oder 3 Jahre
    removed = blacklist.clear_old_entries(days=1095)
```

---

## 🐛 Troubleshooting

### Problem 1: Künstler wird nicht geblacklistet

**Symptom:** Künstler ohne neue Alben erscheint weiterhin in Top-10

**Diagnose:**
```python
blacklist = get_artist_blacklist()

# Prüfe ob auf Blacklist
print(blacklist.is_blacklisted("Artist Name"))

# Prüfe Blacklist-Inhalt
print(blacklist.blacklist)
```

**Lösung:**  
- Prüfen ob `update_artist_blacklist_from_search_results()` aufgerufen wird  
- Prüfen ob `found_new_albums=False` korrekt übergeben wird  

### Problem 2: Re-Check erfolgt nicht

**Symptom:** Künstler bleibt dauerhaft auf Blacklist, trotz > 365 Tagen

**Diagnose:**
```python
artist_data = blacklist.blacklist.get("artist name")
print(f"Last checked: {artist_data['last_checked']}")

from datetime import datetime
last_check = datetime.fromisoformat(artist_data['last_checked'])
days_since = (datetime.now() - last_check).days
print(f"Days since check: {days_since}")
```

**Lösung:**  
- `is_blacklisted()` gibt `False` zurück wenn > 365 Tage  
- Künstler sollte automatisch in gefilterte Top-10 aufgenommen werden  

### Problem 3: Zu viele API-Anfragen

**Symptom:** Zu viele Bibliotheks-Suchen, langsame Performance

**Lösung:**
```python
# Reduziere top_n
add_top_artist_albums_to_collection(
    archive_path="H:\\MP3 Archiv",
    top_n=5,  # Statt 10
    use_blacklist=True
)

# Oder erhöhe Re-Check Intervall
RECHECK_INTERVAL_DAYS = 730  # 2 Jahre statt 1
```

### Problem 4: Blacklist-Datei korrupt

**Symptom:** Fehler beim Laden von `blacklist_artists.json`

**Lösung:**
```bash
# Backup erstellen
cp data/blacklist_artists.json data/blacklist_artists.json.backup

# Datei manuell prüfen
cat data/blacklist_artists.json | python -m json.tool

# Im Notfall: Neu erstellen
rm data/blacklist_artists.json
python main.py  # Startet mit leerer Blacklist
```

---

## 📈 Best Practices

### 1. Regelmäßige Wartung

```python
# In main.py oder separatem Wartungs-Script
from data_sources.mp3_analysis import perform_artist_blacklist_maintenance

# Beim App-Start
perform_artist_blacklist_maintenance()
```

### 2. Logging aktivieren

```python
import logging
from utils.logging_config import setup_logging

# Für detailliertes Logging
setup_logging(level=logging.DEBUG)
```

### 3. Monitoring einrichten

```python
from utils.artist_blacklist import get_artist_blacklist

blacklist = get_artist_blacklist()
stats = blacklist.get_stats()

# Alarmierung bei zu vielen Blacklist-Einträgen
if stats['total_artists'] > 50:
    logger.warning(f"Viele Künstler geblacklistet: {stats['total_artists']}")

# Alarmierung bei vielen fälligen Re-Checks
if stats['due_for_recheck'] > 10:
    logger.info(f"Viele Re-Checks fällig: {stats['due_for_recheck']}")
```

### 4. Performance-Optimierung

```python
# Verwende max_total Parameter effizient
top_artists = get_filtered_top_artists(
    artist_counter,
    blacklist,
    top_n=10,
    max_total=20  # Prüfe max. 20 statt alle Künstler
)
```

---

## 🧪 Testing

### Unit Tests ausführen

```bash
# Alle Tests
pytest tests/test_artist_blacklist.py -v

# Spezifischer Test
pytest tests/test_artist_blacklist.py::TestArtistBlacklist::test_is_blacklisted_fresh_entry -v

# Mit Coverage
pytest tests/test_artist_blacklist.py --cov=utils.artist_blacklist
```

### Integration Tests

```python
# In tests/test_mp3_integration.py
def test_full_workflow():
    """Test kompletter Workflow mit Artist-Blacklist."""
    # Setup
    blacklist = ArtistBlacklist()
    artist_counter = Counter({"Artist A": 100})

    # Erste Suche - keine Alben
    top_artists = get_filtered_top_artists(artist_counter, blacklist, top_n=10)
    assert len(top_artists) == 1

    update_artist_blacklist_from_search_results(
        "Artist A", 100, False, blacklist
    )

    # Zweite Suche - sollte übersprungen werden
    top_artists = get_filtered_top_artists(artist_counter, blacklist, top_n=10)
    assert len(top_artists) == 0  # Artist A geblacklistet
```

---

## 📚 Weiterführende Informationen

### Verwandte Module

- `utils/blacklist.py` - Allgemeines Blacklist-System für Medien  
- `data_sources/mp3_analysis.py` - MP3-Archiv Analyse  
- `preprocessing/filters.py` - Album-Filterung  

### Externe Referenzen

- [Python datetime Dokumentation](https://docs.python.org/3/library/datetime.html)  
- [collections.Counter](https://docs.python.org/3/library/collections.html#collections.Counter)  

---

**Version:** 2.0.0
**Zuletzt aktualisiert:** 2025-10-25
