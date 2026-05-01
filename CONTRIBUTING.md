# 🤝 Contributing to Library Recommender

Vielen Dank für dein Interesse, zur **Bibliothek-Empfehlungs-App** beizutragen! Wir freuen uns über jeden Beitrag – sei es durch Bug-Reports, Feature-Vorschläge, Code-Beiträge oder Dokumentations-Verbesserungen.

## 📋 Inhaltsverzeichnis

- [Code of Conduct](#code-of-conduct)  
- [Wie kann ich beitragen?](#wie-kann-ich-beitragen)  
- [Development Setup](#development-setup)  
- [Coding Guidelines](#coding-guidelines)  
- [Pull Request Process](#pull-request-process)  
- [Neue Features hinzufügen](#neue-features-hinzufügen)  
- [Testing](#testing)  

## 🤝 Code of Conduct

Dieses Projekt folgt einem **Code of Conduct** basierend auf dem [Contributor Covenant](https://www.contributor-covenant.org/):

- Sei respektvoll und inklusiv  
- Akzeptiere konstruktive Kritik  
- Konzentriere dich auf das Beste für die Community  
- Zeige Empathie gegenüber anderen  

## 🚀 Wie kann ich beitragen?

### 🐛 Bug Reports

Wenn du einen Bug findest, erstelle bitte ein [Issue](https://github.com/dgaida/library_recommender/issues) mit:

- **Klarer Titel**: Beschreibe das Problem kurz und prägnant  
- **Schritte zur Reproduktion**: Wie kann der Bug nachgestellt werden?  
- **Erwartetes Verhalten**: Was sollte passieren?  
- **Aktuelles Verhalten**: Was passiert stattdessen?  
- **Environment**: Python-Version, OS, relevante Logs  
- **Screenshots**: Falls hilfreich  

**Template:**
```markdown
### Bug Beschreibung
Kurze Beschreibung des Problems

### Schritte zur Reproduktion
1. App starten mit `python main.py`
2. Klicke auf "Neue Filme vorschlagen"
3. Wähle Film X aus
4. Fehler tritt auf

### Erwartetes Verhalten
Film sollte zur Ablehnungs-Liste hinzugefügt werden

### Aktuelles Verhalten
App stürzt ab mit Error: ...

### Environment
- Python: 3.10.5
- OS: Windows 11
- Browser: Chrome 120
```

### 💡 Feature Requests

Hast du eine Idee für ein neues Feature? Erstelle ein Issue mit:

- **Beschreibung**: Was soll das Feature tun?  
- **Motivation**: Warum ist es nützlich?  
- **Alternativen**: Gibt es andere Ansätze?  
- **Zusätzlicher Kontext**: Screenshots, Mockups, Links  

### 📝 Dokumentations-Verbesserungen

Dokumentation ist genauso wichtig wie Code! Du kannst helfen durch:

- Tippfehler korrigieren  
- Unklare Abschnitte verbessern  
- Beispiele hinzufügen  
- Übersetzungen beisteuern  

### 💻 Code-Beiträge

1. **Fork** das Repository  
2. **Clone** deinen Fork: `git clone https://github.com/DEIN_USERNAME/library_recommender.git`  
3. **Branch erstellen**: `git checkout -b feature/mein-neues-feature`  
4. **Änderungen vornehmen** (siehe [Coding Guidelines](#coding-guidelines))  
5. **Tests schreiben** (siehe [Testing](#testing))  
6. **Commit**: `git commit -am 'Add: Mein neues Feature'`  
7. **Push**: `git push origin feature/mein-neues-feature`  
8. **Pull Request erstellen**  

## 🛠️ Development Setup

### 1. Repository Setup

```bash
# Repository clonen
git clone https://github.com/dgaida/library_recommender.git
cd library_recommender

# Virtuelle Umgebung erstellen
python -m venv venv
source venv/bin/activate  # Linux/Mac
# oder
venv\Scripts\activate     # Windows

# Dependencies installieren
pip install -r requirements.txt
pip install -r requirements-dev.txt  # Für Tests & Linting
```

### 2. Pre-commit Hooks einrichten (optional)

```bash
pip install pre-commit
pre-commit install
```

Dies führt automatisch vor jedem Commit folgende Checks durch:  
- Code-Formatierung mit Black  
- Linting mit Flake8  
- YAML-Syntax-Check  
- Trailing Whitespace entfernen  

### 3. Secrets konfigurieren (optional)

Für Google-Suche Feature:
```bash
cp secrets.env.template secrets.env
# Trage deinen Groq API Key in secrets.env ein
```

### 4. Tests ausführen

```bash
# Alle Tests
pytest tests/ -v

# Mit Coverage
pytest tests/ --cov=. --cov-report=html

# Einzelne Test-Datei
pytest tests/test_filters.py -v
```

### 5. App starten

```bash
python main.py
```

## 📐 Coding Guidelines

### Python Style Guide

Wir folgen [PEP 8](https://peps.python.org/pep-0008/) mit einigen Anpassungen:

#### Formatierung

- **Line Length**: 127 Zeichen (nicht 80)  
- **Formatter**: Black (automatisch via pre-commit)  
- **Linter**: Flake8 mit angepasster `.flake8` Config  
- **Type Hints**: Verwende Type Hints für alle Funktionen  

**Beispiel:**

```python
from typing import List, Dict, Any, Optional
from utils.logging_config import get_logger

logger = get_logger(__name__)


def process_media_items(
    items: List[Dict[str, Any]],
    category: str,
    max_items: Optional[int] = None
) -> List[Dict[str, Any]]:
    """
    Verarbeitet Medien-Items für eine Kategorie.

    Args:
        items: Liste von Medien-Dictionaries
        category: Kategorie ('films', 'albums', 'books')
        max_items: Maximale Anzahl zu verarbeitender Items (optional)

    Returns:
        Verarbeitete und gefilterte Items

    Raises:
        ValueError: Wenn category ungültig ist

    Example:
        >>> items = [{"title": "Film 1", "author": "Director 1"}]
        >>> result = process_media_items(items, "films", max_items=10)
        >>> len(result)
        1
    """
    if category not in ["films", "albums", "books"]:
        raise ValueError(f"Ungültige Kategorie: {category}")

    logger.info(f"Verarbeite {len(items)} Items für Kategorie '{category}'")

    # Implementation...
    processed_items: List[Dict[str, Any]] = []

    for item in items[:max_items]:
        # Verarbeitung
        processed_items.append(item)

    logger.debug(f"{len(processed_items)} Items verarbeitet")
    return processed_items
```

#### Docstrings

**Alle Funktionen** müssen Google-Style Docstrings haben:

```python
def my_function(param1: str, param2: int = 10) -> bool:
    """
    Kurze Beschreibung (eine Zeile).

    Längere Beschreibung über mehrere Zeilen, falls nötig.
    Erkläre was die Funktion tut, nicht wie.

    Args:
        param1: Beschreibung von param1
        param2: Beschreibung von param2 (default: 10)

    Returns:
        Beschreibung des Rückgabewerts

    Raises:
        ValueError: Wann diese Exception geworfen wird
        IOError: Wann diese Exception geworfen wird

    Example:
        >>> my_function("test", 5)
        True
        >>> my_function("invalid")
        False
    """
    pass
```

#### Logging statt Print

**NIEMALS** `print()` verwenden! Stattdessen Logger:

```python
from utils.logging_config import get_logger

logger = get_logger(__name__)

# ❌ Falsch
print("Verarbeite Daten...")
print(f"DEBUG: {variable}")

# ✅ Richtig
logger.info("Verarbeite Daten...")
logger.debug(f"Variable: {variable}")
logger.warning("Potentielles Problem erkannt")
logger.error(f"Fehler aufgetreten: {error}", exc_info=True)
```

**Logging-Levels:**  
- `DEBUG`: Detaillierte Informationen für Debugging  
- `INFO`: Allgemeine Informationsmeldungen  
- `WARNING`: Warnung über unerwartete Ereignisse  
- `ERROR`: Fehler, die behandelt werden können  
- `CRITICAL`: Schwere Fehler, App kann nicht fortfahren  

#### Naming Conventions

- **Variablen & Funktionen**: `snake_case`  
- **Klassen**: `PascalCase`  
- **Konstanten**: `UPPER_SNAKE_CASE`  
- **Private**: `_leading_underscore`  

```python
# Variablen
user_name: str = "Alice"
max_items: int = 100

# Funktionen
def get_media_items() -> List[Dict[str, Any]]:
    pass

# Klassen
class MediaRecommender:
    pass

# Konstanten
MAX_RETRIES: int = 3
API_BASE_URL: str = "https://api.example.com"

# Private
_internal_cache: Dict[str, Any] = {}
```

#### Imports

```python
# Standard Library
import os
import json
from datetime import datetime
from typing import List, Dict, Any, Optional

# Third Party
import requests
from bs4 import BeautifulSoup
import gradio as gr

# Local
from utils.logging_config import get_logger
from library.search import KoelnLibrarySearch
```

### Projektspezifische Patterns

#### 1. Datenquellen-Module

Neue Datenquelle in `data_sources/`:

```python
#!/usr/bin/env python3
"""
Kurze Beschreibung der Datenquelle.
"""

import os
import json
from typing import List, Dict, Any

from utils.logging_config import get_logger
from utils.sources import SOURCE_MY_NEW_SOURCE  # Definiere in sources.py!

logger = get_logger(__name__)

DATA_DIR = os.path.join(os.path.dirname(__file__), "..", "data")
CACHE_FILE = os.path.join(DATA_DIR, "my_source.json")


def fetch_items_from_source() -> List[Dict[str, Any]]:
    """
    Lädt Items von der Datenquelle.

    Returns:
        Liste von Items mit title, author, source
    """
    logger.info("Lade Items von Quelle...")

    items: List[Dict[str, Any]] = []

    # Datenquelle abfragen...

    logger.info(f"{len(items)} Items geladen")
    return items
```

#### 2. Quellen-Konstanten

In `utils/sources.py` definieren:

```python
# Neue Quelle hinzufügen
SOURCE_MY_NEW_SOURCE = "Meine Neue Quelle Beschreibung"

# Emoji hinzufügen
SOURCE_EMOJIS = {
    # ... existierende Emojis ...
    SOURCE_MY_NEW_SOURCE: "🆕",
}
```

#### 3. Tests schreiben

Für jede neue Funktion einen Test in `tests/`:

```python
#!/usr/bin/env python3
"""
Unit Tests für my_module.
"""

import pytest
from unittest.mock import Mock, patch


class TestMyFunction:
    """Tests für my_function."""

    def test_basic_functionality(self):
        """Test grundlegende Funktionalität."""
        result = my_function("input")
        assert result == "expected_output"

    def test_edge_case_empty_input(self):
        """Test mit leerem Input."""
        result = my_function("")
        assert result == ""

    def test_with_mock(self):
        """Test mit Mock-Objekten."""
        with patch('module.dependency') as mock_dep:
            mock_dep.return_value = "mocked"
            result = my_function("test")
            assert result == "mocked"
```

## 🔄 Pull Request Process

### 1. Vor dem PR

- [ ] Code folgt [Coding Guidelines](#coding-guidelines)  
- [ ] Alle Tests bestehen: `pytest tests/ -v`  
- [ ] Type Hints vorhanden  
- [ ] Docstrings geschrieben  
- [ ] Logging statt Print  
- [ ] Neue Features haben Tests  
- [ ] README/Docs aktualisiert (falls nötig)  

### 2. PR erstellen

**Titel:** Nutze Conventional Commits Format:

```
feat: Add support for Spotify API integration
fix: Resolve issue with album filtering
docs: Update installation instructions
test: Add tests for blacklist system
refactor: Improve recommender performance
```

**Beschreibung:**

```markdown
## Beschreibung
Kurze Zusammenfassung der Änderungen

## Typ der Änderung
- [ ] Bug Fix
- [ ] Neues Feature
- [ ] Breaking Change
- [ ] Dokumentation

## Motivation und Kontext
Warum ist diese Änderung notwendig?

## Wie wurde es getestet?
- [ ] Manuelle Tests durchgeführt
- [ ] Unit Tests hinzugefügt
- [ ] Integration Tests hinzugefügt

## Screenshots (falls relevant)
[Bild einfügen]

## Checklist
- [ ] Code folgt Style Guidelines
- [ ] Self-review durchgeführt
- [ ] Code kommentiert (komplexe Stellen)
- [ ] Dokumentation aktualisiert
- [ ] Keine neuen Warnings
- [ ] Tests hinzugefügt
- [ ] Alle Tests bestehen
```

### 3. Review-Prozess

1. **Automatische Checks**: GitHub Actions führt Tests & Linting durch  
2. **Code Review**: Maintainer prüfen den Code  
3. **Feedback**: Änderungen können angefordert werden  
4. **Approval**: Nach erfolgreicher Review wird der PR gemergt  

### 4. Nach dem Merge

- Branch kann gelöscht werden  
- Feature erscheint im nächsten Release  
- Dein Name wird in CHANGELOG.md erwähnt! 🎉  

## ✨ Neue Features hinzufügen

### Neue Datenquelle

**Beispiel: Neue Film-Datenquelle "IMDb Top 250"**

#### 1. Quellen-Konstante definieren

`utils/sources.py`:
```python
SOURCE_IMDB_TOP_250 = "IMDb Top 250"

SOURCE_EMOJIS = {
    # ...
    SOURCE_IMDB_TOP_250: "⭐",
}
```

#### 2. Datenquellen-Modul erstellen

`data_sources/imdb_films.py`:
```python
#!/usr/bin/env python3
"""
IMDb Top 250 Film-Datenquelle.
"""

from typing import List, Dict, Any
from utils.logging_config import get_logger
from utils.sources import SOURCE_IMDB_TOP_250

logger = get_logger(__name__)


def fetch_imdb_top_250() -> List[Dict[str, Any]]:
    """
    Lädt IMDb Top 250 Filme.

    Returns:
        Liste von Filmen mit title, author, source
    """
    logger.info("Lade IMDb Top 250...")

    films: List[Dict[str, Any]] = []

    # Web Scraping oder API Call...

    return films
```

#### 3. In app.py integrieren

`gui/app.py`:
```python
from data_sources.imdb_films import fetch_imdb_top_250

def load_or_fetch_films():
    # ...
    imdb_films = fetch_imdb_top_250()
    combined = wiki_films + fbw_films + oscar_films + imdb_films
    # ...
```

#### 4. Tests schreiben

`tests/test_imdb_films.py`:
```python
def test_fetch_imdb_top_250():
    films = fetch_imdb_top_250()
    assert len(films) > 0
    assert films[0]['source'] == SOURCE_IMDB_TOP_250
```

#### 5. Dokumentation aktualisieren

`README.md`:
```markdown
#### 🎬 **Filme** - Premium-Quellen kombiniert
- **BBC Culture**: ...
- **IMDb**: Top 250 Filme aller Zeiten ⭐
```

### Neue Bibliothek unterstützen

Um andere Bibliotheken als Köln zu unterstützen:

1. **Neue Search-Klasse**: `library/search_bibliothek.py`  
2. **HTML-Parser anpassen**: Für die spezifische Bibliotheks-Website  
3. **Konfiguration**: ENV-Variable für Bibliotheks-Auswahl  
4. **Tests**: Mock-Tests für neue Bibliothek  

## 🧪 Testing

### Test-Struktur

```
tests/
├── __init__.py
├── test_filters.py          # Unit Tests für filters.py
├── test_recommender.py      # Unit Tests für recommender.py
├── test_blacklist.py        # Unit Tests für blacklist.py
├── test_sources.py          # Unit Tests für sources.py
└── test_integration.py      # Integration Tests
```

### Test schreiben

```python
import pytest
from unittest.mock import Mock, patch, MagicMock


class TestMyFeature:
    """Tests für my_feature."""

    @pytest.fixture
    def sample_data(self):
        """Fixture mit Sample-Daten."""
        return [
            {"title": "Item 1", "author": "Author 1"},
            {"title": "Item 2", "author": "Author 2"}
        ]

    def test_basic_case(self, sample_data):
        """Test Basis-Funktionalität."""
        result = process_items(sample_data)
        assert len(result) == 2

    def test_empty_input(self):
        """Test mit leerem Input."""
        result = process_items([])
        assert result == []

    @patch('module.external_api')
    def test_with_mock(self, mock_api):
        """Test mit externem API-Mock."""
        mock_api.return_value = {"status": "ok"}
        result = call_api()
        assert result["status"] == "ok"
        mock_api.assert_called_once()
```

### Coverage

Strebe mindestens **80% Code Coverage** an:

```bash
pytest tests/ --cov=. --cov-report=html
# Öffne htmlcov/index.html im Browser
```

## 📚 Weitere Ressourcen

- [Python Style Guide (PEP 8)](https://peps.python.org/pep-0008/)  
- [Google Python Style Guide](https://google.github.io/styleguide/pyguide.html)  
- [Conventional Commits](https://www.conventionalcommits.org/)  
- [Pytest Documentation](https://docs.pytest.org/)  
- [Type Hints (PEP 484)](https://peps.python.org/pep-0484/)  

## 💬 Fragen?

- **Issues**: [GitHub Issues](https://github.com/dgaida/library_recommender/issues)  
- **Email**: daniel.gaida@th-koeln.de  

---

**Vielen Dank für deinen Beitrag! 🙏**

Jeder Beitrag, egal wie klein, macht das Projekt besser. Wir schätzen deine Zeit und Mühe sehr!
