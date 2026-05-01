# 📝 Docstring Style Guide

Wir verwenden den **Google Python Style Guide** für alle Dokumentationen im Code.

## Beispiel

```python
def funktion(param1: str, param2: int = 10) -> bool:
    """
    Kurze Beschreibung (eine Zeile).

    Längere Beschreibung über mehrere Zeilen.

    Args:
        param1 (str): Beschreibung von param1.
        param2 (int): Beschreibung von param2 (default: 10).

    Returns:
        bool: Beschreibung des Rückgabewerts.

    Raises:
        ValueError: Wenn param1 leer ist.
    """
    if not param1:
        raise ValueError("param1 darf nicht leer sein")
    return True
```

## Warum dieser Standard?

- **Lesbarkeit**: Einheitliche Struktur für alle Entwickler.  
- **Automatisierung**: Ermöglicht die automatische Generierung der API-Dokumentation mit `mkdocstrings`.  
- **Klarheit**: Explizite Angabe von Typen und Standardwerten.  
