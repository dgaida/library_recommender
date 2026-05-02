import sys
from unittest.mock import patch

# Mock the function before importing app
with patch('data_sources.mp3_analysis.get_top_artists_from_archive') as mock_get:
    mock_get.return_value = ["Artist " + str(i) for i in range(1, 31)]

    # We also need to mock other heavy things if they fail
    with patch('gui.app.initialize_recommendations') as mock_init:
        mock_init.return_value = ([], [], [])
        with patch('gui.app.load_or_fetch_films', return_value=[]),              patch('gui.app.load_or_fetch_albums', return_value=[]),              patch('gui.app.load_or_fetch_books', return_value=[]):

            import gui.app as app
            # Modify the global variable that was already set during import if necessary
            # Actually, because of how Gradio works, the components might have been created already.
            # Let's check gui/app.py again to see where artists_list_str is used.

            # Since I'm importing it here, the module-level code runs now.
            app.demo.launch(prevent_thread_lock=True, server_port=7860)

import time
from playwright.sync_api import sync_playwright

def run_verification():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(record_video_dir="/home/jules/verification/videos")
        page = context.new_page()
        try:
            page.goto("http://localhost:7860")
            page.wait_for_timeout(2000)

            # Click on 'Musik' tab. Gradio tabs usually have buttons.
            page.get_by_role("tab", name="🎵 Musik").click()
            page.wait_for_timeout(1000)

            # Find the accordion and click to open
            accordion = page.get_by_text("⭐ Deine Lieblingsinterpreten (MP3-Archiv)")
            accordion.click()
            page.wait_for_timeout(1000)

            # Take screenshot
            page.screenshot(path="/home/jules/verification/screenshots/musik_tab_accordion.png")

            # Check if we see some of our mocked artists
            content = page.content()
            if "Artist 1, Artist 2" in content and "Artist 30" in content:
                print("Verification successful: Found mocked artists in accordion")
            else:
                print("Verification warning: Mocked artists not found in page content")

        finally:
            context.close()
            browser.close()

if __name__ == "__main__":
    import os
    os.makedirs("/home/jules/verification/videos", exist_ok=True)
    os.makedirs("/home/jules/verification/screenshots", exist_ok=True)

    try:
        run_verification()
    finally:
        # We need a way to stop the gradio app, but since it's in this process
        # (or at least started by it without block), we can just exit.
        pass
