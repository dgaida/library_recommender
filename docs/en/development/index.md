# 👨‍💻 Development

This section is for developers who want to contribute to the project.

## 1. Setting Up the Environment

Ensure you have all dependencies installed:

```bash
pip install -r requirements.txt
pip install -r requirements-dev.txt
```

## 2. Docstring Standard

We use the **Google Python Style Guide** for docstrings. All functions and classes should be documented:

```python
def my_function(x: int) -> int:
    """
    Short description.

    Args:
        x: An integer.

    Returns:
        The result.
    """
```

## 3. Running Tests

We use `pytest` for automated tests:

```bash
pytest tests/ -v
```

For coverage reports:

```bash
pytest tests/ --cov=.
```

## 4. Pre-commit Hooks

Please install pre-commit hooks to verify the code style before each commit:

```bash
pre-commit install
```
