# 🛠️ Troubleshooting

Frequently asked questions and solutions.

## ❓ No recommendations found

- **Internet connection**: Check if you are online.  
- **Cache**: Clear the cache with `rm data/*.json` and restart the app.  
- **Blacklist**: Reset the blacklist with `rm data/blacklist_*.json`.  

## ❓ Google Search doesn't work

- **Groq API Key**: Verify the key in `secrets.env` is correctly set.  
- **DuckDuckGo**: Check if DuckDuckGo is accessible from your location.  

## ❓ MP3 archive not found

- **Path**: Double-check paths in `data_sources/albums.py` and `data_sources/mp3_analysis.py`.  
- **Windows paths**: Use double backslashes: `C:\\Music\\Archive`.  
