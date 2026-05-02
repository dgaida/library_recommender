import sys
from unittest.mock import patch, MagicMock

# Setup mocks for all the things gui/app.py does on import
with patch('utils.logging_config.get_logger'),      patch('gradio.Blocks'),      patch('gradio.Tab'),      patch('gradio.Column'),      patch('gradio.Row'),      patch('gradio.Button'),      patch('gradio.CheckboxGroup'),      patch('gradio.Textbox'),      patch('gradio.HTML'),      patch('gradio.Accordion'),      patch('gradio.Markdown'),      patch('gui.app.load_or_fetch_films', return_value=[]),      patch('gui.app.load_or_fetch_albums', return_value=[]),      patch('gui.app.load_or_fetch_books', return_value=[]),      patch('gui.app.initialize_recommendations', return_value=([], [], [])),      patch('gui.app.load_favorites_to_suggestions', return_value=([], [], [])),      patch('gui.app.get_initial_choices', return_value=[]),      patch('data_sources.mp3_analysis.get_top_artists_from_archive') as mock_get:

    mock_get.return_value = ["Artist " + str(i) for i in range(1, 31)]

    import gui.app as app

    print(f"Number of personal artists: {len(app.personal_artists)}")
    print(f"First artist: {app.personal_artists[0]}")
    print(f"Last artist: {app.personal_artists[-1]}")
    print(f"Artists list string sample: {app.artists_list_str[:50]}...")

    if len(app.personal_artists) == 30:
        print("SUCCESS: Found 30 artists")
    else:
        print(f"FAILURE: Found {len(app.personal_artists)} artists")
        sys.exit(1)
