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
- The identification follows a two-tier strategy:  
  1. **Filename Strategy**: The filename is checked for separators like " - " or "-". If a separator is found, the artist is extracted (handling optional track numbers like "01-Artist-Title.mp3").  
  2. **Directory Fallback**: If no artist is found in the filename, the directory structure is used.  
- Expected folder structures include:  
  - `Grouping/Album/Artist-Title.mp3` (Primary)  
  - `Artist/Album/Title.mp3` (Fallback)  
  - `Grouping/Artist/Album/Title.mp3` (Fallback)  
- Single-character folder names (A-Z) and the "#" folder are skipped as grouping folders.  
- Generic names like "Various", "Unknown", or "Unbekannt" are ignored.  

## Personalized Music Search
- The recommender must ensure that for personalized music recommendations, a library search is performed until at least 5 available albums from the user's top artists are found.
- If the cached recommendations (from `albums.json`) do not yield enough available items, the system must dynamically query the library for the next artists in the top-artists list until the goal is met.
- Real-time searches should respect the `ArtistBlacklist` to avoid repeatedly searching for artists without available items in the library.
