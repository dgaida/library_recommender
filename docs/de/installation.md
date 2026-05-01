# 🛠️ Installation

Dieser Abschnitt beschreibt die Installation der **Bibliothek-Empfehlungs-App**.

## 1. Voraussetzungen

- **Python 3.9 oder höher**: Stellen Sie sicher, dass Python installiert ist.  
- **Git**: Zum Klonen des Repositories.  

## 2. Klonen des Repositories

```bash
git clone https://github.com/dgaida/library_recommender.git
cd library_recommender
```

## 3. Virtuelle Umgebung (Empfohlen)

Es wird dringend empfohlen, eine virtuelle Umgebung zu verwenden:

```bash
python -m venv venv
source venv/bin/activate  # Linux/Mac
# oder
venv\Scripts\activate     # Windows
```

## 4. Abhängigkeiten installieren

```bash
pip install -r requirements.txt
```

## 5. Optionale Features

### Groq API (für KI-Zusammenfassungen)

1. Holen Sie sich einen API-Key von [Groq](https://groq.com).  
2. Erstellen Sie eine `secrets.env` Datei im Hauptverzeichnis:  

```env
GROQ_API_KEY=gsk_...
```
