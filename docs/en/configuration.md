# ⚙️ Configuration

This section describes how to customize the app to your needs.

## 1. MP3 Archive Path

Personalized music recommendations analyze your local MP3 archive. To configure this, modify the following files:

- `data_sources/mp3_analysis.py`: Change the path in `add_top_artist_albums_to_collection("PATH/TO/YOUR/MP3/ARCHIVE", top_n=30)`.  
- `data_sources/albums.py`: Adjust the filter path in `filter_existing_albums(albums, "PATH/TO/YOUR/MP3/ARCHIVE")`.  

## 2. Groq API Key

Create a file named `secrets.env` in the root directory with the following content:

```env
GROQ_API_KEY=gsk_...
```

This key is used for AI-generated summaries (via the Groq model).

## 3. Number of Recommendations

By default, the app suggests 25 titles per category (5 per data source). This can be adjusted in `recommender/recommender.py`.
