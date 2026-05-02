import sys

content = open('gui/app.py', 'r').read()

# Update import
search_import = "from data_sources.mp3_analysis import add_top_artist_albums_to_collection"
replace_import = "from data_sources.mp3_analysis import add_top_artist_albums_to_collection, get_top_artists_from_archive"

content = content.replace(search_import, replace_import)

# Update personal_artists calculation
search_logic = """# Extrahiere Lieblingsinterpreten aus personalisierten Alben
personal_artists = sorted(
    list(
        set(
            a["author"]
            for a in albums
            if "Interessant für dich" in a.get("source", "") or "Personalisiert" in a.get("source", "")
        )
    )
)"""

replace_logic = """# Extrahiere Lieblingsinterpreten aus dem MP3-Archiv (Top 30)
personal_artists = sorted(get_top_artists_from_archive("H:\\MP3 Archiv", top_n=30))"""

if search_logic in content:
    content = content.replace(search_logic, replace_logic)
    with open('gui/app.py', 'w') as f:
        f.write(content)
    print("Successfully updated gui/app.py")
else:
    print("Search logic not found")
    # Let's try to be more flexible with whitespace if exact match fails
    import re
    pattern = re.compile(r'# Extrahiere Lieblingsinterpreten aus personalisierten Alben\s+personal_artists = sorted\(\s+list\(\s+set\(\s+a\["author"\]\s+for a in albums\s+if "Interessant für dich" in a\.get\("source", ""\) or "Personalisiert" in a\.get\("source", ""\)\s+\)\s+\)\s+\)')
    if pattern.search(content):
        new_content = pattern.sub(replace_logic, content)
        with open('gui/app.py', 'w') as f:
            f.write(new_content)
        print("Successfully updated gui/app.py using regex")
    else:
        print("Regex match also failed")
        sys.exit(1)
