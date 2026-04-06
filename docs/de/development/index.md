# 👨‍💻 Entwicklung

Dieser Bereich ist für Entwickler gedacht, die an dem Projekt mitarbeiten möchten.

## 1. Einrichten der Umgebung

Stellen Sie sicher, dass Sie alle Abhängigkeiten installiert haben:

```bash
pip install -r requirements.txt
pip install -r requirements-dev.txt
```

## 2. Docstring Standard

Wir verwenden den **Google Python Style Guide** für Docstrings. Alle Funktionen und Klassen sollten dokumentiert sein:

```python
def meine_funktion(x: int) -> int:
    """
    Kurze Beschreibung.

    Args:
        x: Eine Ganzzahl.

    Returns:
        Das Ergebnis.
    """
```

## 3. Tests ausführen

Wir verwenden `pytest` für automatisierte Tests:

```bash
pytest tests/ -v
```

Für Coverage-Berichte:

```bash
pytest tests/ --cov=.
```

## 4. Pre-commit Hooks

Bitte installieren Sie pre-commit Hooks, um den Code-Stil vor jedem Commit zu überprüfen:

```bash
pre-commit install
```
