# 🛠️ Installation

This section describes the installation process for the **Library Recommender App**.

## 1. Prerequisites

- **Python 3.9 or higher**: Ensure Python is installed.  
- **Git**: To clone the repository.  

## 2. Cloning the Repository

```bash
git clone https://github.com/dgaida/library_recommender.git
cd library_recommender
```

## 3. Virtual Environment (Recommended)

It is highly recommended to use a virtual environment:

```bash
python -m venv venv
source venv/bin/activate  # Linux/Mac
# or
venv\Scripts\activate     # Windows
```

## 4. Install Dependencies

```bash
pip install -r requirements.txt
```

## 5. Optional Features

### LLM Configuration (for AI Summaries)

AI summaries use the [llm_client](https://dgaida.github.io/llm_client/dev/) library. You can configure your preferred provider (e.g., Groq, OpenAI, Gemini, or Ollama) in `llm_config.yaml`.

1. Create or edit `llm_config.yaml`:
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

2. Create a `secrets.env` file in the root directory for API keys:

```env
GROQ_API_KEY=gsk_...
# OPENAI_API_KEY=sk-...
# GEMINI_API_KEY=...
```
