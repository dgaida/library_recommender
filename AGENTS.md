# Guidelines for AI Agents

## Coding Conventions
- Use `from ddgs import DDGS` for DuckDuckGo search. Do **not** use `from duckduckgo_search ...`. This project uses the `ddgs` package directly. See: https://pypi.org/project/ddgs/
- Follow the Google Python Style Guide for docstrings.
- German is the authoritative source for in-code documentation.
- Maintain a minimum of 95% API coverage as enforced by `interrogate`.

## Documentation
- Bilingual support (German and English) via MkDocs.
- API documentation is automated via `mkdocstrings`.
- Relative links in documentation must consider the language-specific subdirectories (`de/`, `en/`).

## Testing
- Core logic is prioritized over GUI components.
- Coverage reports omit `gui/`, `main.py`, etc.
- Always run `pytest` to verify changes.

## Performance
- Avoid heavy initialization in utility modules. `gui/app.py` triggers data fetching on import.
