# gui/__init__.py

"""
GUI-Package für das Bibliothek-Recommender-System.

Dieses Package stellt die Gradio-App bereit und bietet eine
bequeme Startfunktion.
"""

from .app import demo


def launch_app(*args, **kwargs):
    """
    Startet die Gradio-App.

    Args:
        *args: Beliebige Positionsargumente für `demo.launch()`.
        **kwargs: Beliebige Keyword-Argumente für `demo.launch()`.

    Returns:
        None
    """
    demo.launch(*args, **kwargs)


__all__ = ["demo", "launch_app"]
