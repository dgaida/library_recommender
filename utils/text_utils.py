import re


def remove_emoji(text: str) -> str:
    """
    Entfernt Emojis am Anfang eines Strings.

    Verwendet einen Unicode-Regex-Pattern, um gängige Emoji-Bereiche
    zu identifizieren und zu entfernen.

    Args:
        text: String möglicherweise mit Emoji

    Returns:
        String ohne Emoji
    """
    emoji_pattern = re.compile(
        "["
        "\U0001f300-\U0001f9ff"
        "\U0001f600-\U0001f64f"
        "\U0001f680-\U0001f6ff"
        "\U0001f1e0-\U0001f1ff"
        "\U00002702-\U000027b0"
        "\U000024c2-\U0001f251"
        "\U0001f4f1"  # 📱 Handy/Digital-Emoji
        "]+",
        flags=re.UNICODE,
    )
    return emoji_pattern.sub("", text).strip()
