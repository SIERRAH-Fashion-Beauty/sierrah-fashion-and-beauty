"""Small colour-theory helper used to judge whether pieces look good together.

Colours are described by hue (0-360). Neutrals (white, black, beige, grey, denim,
metallics...) go with everything; chromatic colours are compared on the colour wheel.
"""

from __future__ import annotations

# name -> hue for chromatic colours
CHROMATIC: dict[str, float] = {
    "red": 0, "scarlet": 5, "coral": 12, "rust": 15, "orange": 28, "peach": 22, "mustard": 45,
    "yellow": 52, "lime": 80, "olive": 70, "green": 130, "emerald": 145, "mint": 150,
    "teal": 178, "turquoise": 175, "aqua": 185, "sky": 200, "blue": 215, "cobalt": 222,
    "indigo": 245, "lavender": 265, "lilac": 270, "purple": 280, "violet": 285, "plum": 295,
    "magenta": 310, "fuchsia": 318, "pink": 340, "rose": 345, "blush": 350, "maroon": 350,
    "burgundy": 348, "wine": 345,
}

NEUTRALS: set[str] = {
    "white", "ivory", "cream", "offwhite", "black", "charcoal", "grey", "gray", "silver",
    "beige", "nude", "tan", "khaki", "camel", "brown", "taupe", "navy", "denim", "gold",
    "rosegold", "bronze", "copper", "multicolor", "multicolour", "multi",
}

# Words that mean "deeper/lighter shade of" and are ignored when classifying.
_MODIFIERS = {"light", "dark", "dusty", "pastel", "deep", "bright", "baby", "soft", "pale", "royal"}


def _tokens(name: str) -> list[str]:
    text = name.lower().replace("-", " ").replace("_", " ")
    return [t for t in text.split() if t and t not in _MODIFIERS]


def _canonical(name: str) -> str:
    return "".join(_tokens(name))


def classify(name: str) -> tuple[str, float | None]:
    """Return ``("neutral", None)`` or ``("chromatic", hue)`` for a colour name."""
    joined = _canonical(name)
    if joined in NEUTRALS:
        return "neutral", None
    for token in _tokens(name):
        if token in CHROMATIC:
            return "chromatic", CHROMATIC[token]
    for token in _tokens(name):
        if token in NEUTRALS:
            return "neutral", None
    # Unknown colour names are treated as neutral so they never cause a false "clash".
    return "neutral", None


def same_color(a: str, b: str) -> bool:
    """True when two colour names refer to the same family (e.g. "Light Blue" and "Blue")."""
    ka, ha = classify(a)
    kb, hb = classify(b)
    if ka == "chromatic" and kb == "chromatic":
        return abs((ha or 0) - (hb or 0)) <= 20 or abs(abs((ha or 0) - (hb or 0)) - 360) <= 20
    ta, tb = set(_tokens(a)), set(_tokens(b))
    return bool(ta & tb) or _canonical(a) == _canonical(b)


def _hue_distance(a: float, b: float) -> float:
    diff = abs(a - b) % 360
    return min(diff, 360 - diff)


def pair_harmony(a: str, b: str) -> float:
    """0..1 score for how well two colours sit together."""
    ka, ha = classify(a)
    kb, hb = classify(b)
    if ka == "neutral" or kb == "neutral":
        return 0.92
    dist = _hue_distance(ha or 0, hb or 0)
    if dist <= 25:
        return 0.88  # tonal / same family
    if dist <= 65:
        return 0.78  # analogous
    if 150 <= dist <= 210:
        return 0.8  # complementary
    if 100 <= dist < 150:
        return 0.5  # triadic: workable but busy
    return 0.4


def outfit_harmony(color_groups: list[list[str]]) -> float:
    """Score the colours of several pieces together.

    Each group holds the colours of one piece. The first colour of a piece is its
    dominant colour. Too many different chromatic colours is penalised.
    """
    dominants = [g[0] for g in color_groups if g]
    if len(dominants) < 2:
        return 0.85
    pair_scores = [
        pair_harmony(dominants[i], dominants[j])
        for i in range(len(dominants))
        for j in range(i + 1, len(dominants))
    ]
    score = sum(pair_scores) / len(pair_scores)
    chromatic_hues: list[float] = []
    for color in dominants:
        kind, hue = classify(color)
        if kind == "chromatic" and hue is not None and all(_hue_distance(hue, h) > 25 for h in chromatic_hues):
            chromatic_hues.append(hue)
    if len(chromatic_hues) > 2:
        score -= 0.12 * (len(chromatic_hues) - 2)
    return max(0.0, min(1.0, score))


def matches_any(color_names: list[str], favourites: list[str]) -> list[str]:
    """Favourite colours that appear among the given colour names."""
    found: list[str] = []
    for fav in favourites:
        if any(same_color(fav, c) for c in color_names) and fav not in found:
            found.append(fav)
    return found
