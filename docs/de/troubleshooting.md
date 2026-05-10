# 🛠️ Fehlerbehebung

Häufig gestellte Fragen und Lösungen.

## ❓ Keine Empfehlungen gefunden

- **Internet-Verbindung**: Prüfen Sie, ob Sie online sind.
- **Cache**: Löschen Sie den Cache mit `rm data/*.json` und starten Sie die App neu.
- **Blacklist**: Setzen Sie die Blacklist mit `rm data/blacklist_*.json` zurück.

## ❓ Google-Suche funktioniert nicht

- **Groq API Key**: Überprüfen Sie, ob der Key in `secrets.env` korrekt gesetzt ist.
- **DuckDuckGo**: Prüfen Sie, ob DuckDuckGo von Ihrem Standort aus erreichbar ist.

## ❓ MP3-Archiv wird nicht gefunden

- **Pfad**: Überprüfen Sie die Pfade in `data_sources/albums.py` und `data_sources/mp3_analysis.py`.
- **Windows-Pfade**: Verwenden Sie doppelte Backslashes: `C:\\Musik\\Archiv`.
