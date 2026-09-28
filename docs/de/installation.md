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

### LLM Konfiguration (für KI-Zusammenfassungen)

Die KI-Zusammenfassungen werden über die [llm_client](https://dgaida.github.io/llm_client/dev/) Bibliothek bereitgestellt. Sie können Ihren bevorzugten Anbieter (z. B. Groq, OpenAI, Gemini oder Ollama) in `llm_config.yaml` angeben.

1. Erstellen oder bearbeiten Sie die Datei `llm_config.yaml`:
```yaml
default_provider: groq

providers:
  groq:
    model: llama-3.3-70b-versatile
  openai:
    model: gpt-4o-mini
  gemini:
    model: gemini-2.5-flash
  ollama:
    model: llama3.2:1b
```

2. Erstellen Sie eine `secrets.env` Datei im Hauptverzeichnis für API-Keys:

```env
GROQ_API_KEY=gsk_...
# OPENAI_API_KEY=sk-...
# GEMINI_API_KEY=...
```
