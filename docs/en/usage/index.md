# 🎮 Usage Guide

This section describes how to use the app effectively.

## 1. Launch the App

```bash
python main.py
```

## 2. Categories

The app is divided into three main areas:
- **Films**: Recommendations from BBC, FBW, and Oscar winners.
- **Albums**: Music from Radio Eins, Oscar soundtracks, and personalized suggestions.
- **Books**: Recommendations from the New York Times canon and guides.

## 3. Manage Media

- **Get Suggestions**: When starting, new recommendations are automatically loaded.
- **Detail Search**: Click the Google button on a medium to see an AI-generated summary, trailer, and cover image.
- **Remove & Refresh**: Select titles and click "Remove" to clear space for new suggestions.
- **Export**: Use the "Save All Recommendations" button to generate a Markdown file (`recommended.md`).

## 4. Personalized Music Recommendations

The app analyzes your local MP3 archive to identify your top artists.
The system ensures that it **actively searches for available CDs** for these artists until at least **5 available albums** are found. If the local cache file does not contain enough data, the app automatically performs a real-time search in the library catalog.
