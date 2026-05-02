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

## MP3 Analysis & Top Artists
- Top artists are determined by the number of MP3 files found in the archive.
- The folder structure is expected to be either `Artist/Album/Title.mp3` or `A/Artist/Album/Title.mp3` (where "A" is a single-letter grouping folder).
- Single-character folder names (A-Z) and the "#" folder are treated as grouping folders and skipped when identifying the artist name, provided there is a subfolder level below them.
- If no subfolders exist, the filename format `Artist - Title.mp3` is used as a fallback.
