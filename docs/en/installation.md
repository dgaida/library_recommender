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

### Groq API (for AI Summaries)

1. Get an API key from [Groq](https://groq.com).
2. Create a `secrets.env` file in the root directory:

```env
GROQ_API_KEY=gsk_...
```
