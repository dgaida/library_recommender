"""
Text-Verarbeitungs-Utilities
"""

import re


def remove_emoji(text: str) -> str:
    """
    Entfernt Emojis aus einem String unter Verwendung eines Unicode-Regex.

    Args:
        text: Der Eingabestring mit möglichen Emojis.

    Returns:
        String ohne Emojis.
    """
    if not text:
        return ""
    # Regex für Emoji-Bereiche
    emoji_pattern = re.compile(
        "["
        "\U0001f600-\U0001f64f"  # emoticons
        "\U0001f300-\U0001f5ff"  # symbols & pictographs
        "\U0001f680-\U0001f6ff"  # transport & map symbols
        "\U0001f1e0-\U0001f1ff"  # flags (iOS)
        "\U00002702-\U000027b0"
        "\U000024c2-\U0001f251"
        "\U0001f900-\U0001f9ff"  # Supplemental Symbols and Pictographs
        "\U0001fa70-\U0001faff"  # Symbols and Pictographs Extended-A
        "\U00002122"
        "\U0000263a"
        "\U000026a1"
        "\U0001f004"
        "\U0001f0cf"
        "\U0001f170-\U0001f171"
        "\U0001f17e"
        "\U0001f17f"
        "\U0001f18e"
        "\U0001f191-\U0001f19a"
        "\U0001f201"
        "\U0001f202"
        "\U0001f21a"
        "\U0001f22f"
        "\U0001f232-\U0001f23a"
        "\U0001f250"
        "\U0001f251"
        "\U00003030"
        "\U0000303d"
        "\U00003297"
        "\U00003299"
        "\U0000231a"
        "\U0000231b"
        "\U00002328"
        "\U000023cf"
        "\U000023e9-\U000023f3"
        "\U000023f8-\U000023fa"
        "\U000024c2"
        "\U000025aa"
        "\U000025ab"
        "\U000025b6"
        "\U000025c0"
        "\U000025fb-\U000025fe"
        "\U00002600-\U00002604"
        "\U0000260e"
        "\U00002611"
        "\U00002614"
        "\U00002615"
        "\U00002618"
        "\U0000261d"
        "\U00002620"
        "\U00002622"
        "\U00002623"
        "\U00002626"
        "\U0000262a"
        "\U0000262e"
        "\U0000262f"
        "\U00002638"
        "\U00002639"
        "\U0000263a"
        "\U00002640"
        "\U00002642"
        "\U00002648-\U00002653"
        "\U00002660"
        "\U00002663"
        "\U00002665"
        "\U00002666"
        "\U00002668"
        "\U0000267b"
        "\U0000267f"
        "\U00002692"
        "\U00002693"
        "\U00002694"
        "\U00002696"
        "\U00002697"
        "\U00002699"
        "\U0000269b"
        "\U0000269c"
        "\U000026a0"
        "\U000026a1"
        "\U000026aa"
        "\U000026ab"
        "\U000026b0"
        "\U000026b1"
        "\U000026bd"
        "\U000026be"
        "\U000026c4"
        "\U000026c5"
        "\U000026c8"
        "\U000026ce"
        "\U000026cf"
        "\U000026d1"
        "\U000026d3"
        "\U000026d4"
        "\U000026e9"
        "\U000026ea"
        "\U000026f0-\U000026f5"
        "\U000026f7-\U000026fa"
        "\U000026fd"
        "]+",
        flags=re.UNICODE,
    )
    return emoji_pattern.sub("", text)
