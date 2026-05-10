# 📝 Docstring Style Guide

We use the **Google Python Style Guide** for all in-code documentation.

## Example

```python
def function(param1: str, param2: int = 10) -> bool:
    """
    Short description (one line).

    Longer description spanning multiple lines.

    Args:
        param1 (str): Description of param1.
        param2 (int): Description of param2 (default: 10).

    Returns:
        bool: Description of the return value.

    Raises:
        ValueError: When param1 is empty.
    """
    if not param1:
        raise ValueError("param1 cannot be empty")
    return True
```

## Why This Standard?

- **Readability**: Consistent structure for all developers.
- **Automation**: Enables automatic API documentation generation with `mkdocstrings`.
- **Clarity**: Explicit specification of types and default values.
