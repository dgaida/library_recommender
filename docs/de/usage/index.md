# 🎮 Bedienung

In diesem Abschnitt erfahren Sie, wie Sie die App effektiv nutzen.

## 1. App starten

```bash
python main.py
```

## 2. Kategorien auswählen

Die App ist in drei Hauptbereiche unterteilt:  
- **Filme**: Empfehlungen von BBC, FBW und Oscar-Gewinnern.  
- **Alben**: Musik von Radio Eins, Oscar-Filmmusik und personalisierte Vorschläge.  
- **Bücher**: Empfehlungen aus dem New York Times Kanon und Ratgebern.  

## 3. Medien verwalten

- **Vorschläge erhalten**: Beim Start werden automatisch neue Empfehlungen geladen.  
- **Detail-Suche**: Klicken Sie auf den Google-Button bei einem Medium, um eine KI-Zusammenfassung, Trailer und Cover zu sehen.  
- **Entfernen & Neu laden**: Wählen Sie Titel aus und klicken Sie auf "Entfernen", um Platz für neue Vorschläge zu schaffen.  
- **Export**: Nutzen Sie den Button "Alle Empfehlungen speichern", um eine Markdown-Datei (`recommended.md`) zu generieren.  

## 4. Personalisierte Musikempfehlungen

Die App analysiert Ihr lokales MP3-Archiv, um Ihre Top-Interpreten zu identifizieren.
Dabei wird sichergestellt, dass für diese Künstler **aktiv nach verfügbaren CDs gesucht wird**, bis mindestens **5 verfügbare Alben** gefunden wurden. Falls keine ausreichenden Daten in der lokalen Cache-Datei vorhanden sind, führt die App automatisch eine Echtzeit-Suche in der Bibliothek durch.
