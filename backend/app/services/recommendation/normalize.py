"""Helpers for upgrading first-generation wardrobe rows."""

from __future__ import annotations

from typing import Any

from ...schemas import CONCRETE_OCCASIONS

STYLE_IDS = ("casual", "traditional", "western", "elegant", "trendy")

_SUBCATEGORY_HINTS: tuple[tuple[str, str], ...] = (
    ("sneaker", "sneakers"), ("heel", "heels"), ("flat", "flats"), ("sandal", "sandals"),
    ("jutti", "juttis"), ("handbag", "handbag"), ("sling", "sling bag"), ("clutch", "clutch"),
    ("backpack", "backpack"), ("tote", "tote"), ("earring", "earrings"), ("watch", "watch"),
    ("necklace", "necklace"), ("bangle", "bangles"), ("lipstick", "lipstick"),
    ("foundation", "foundation"), ("compact", "compact"), ("kajal", "kajal"),
    ("jeans", "jeans"), ("trouser", "trousers"), ("skirt", "skirt"), ("legging", "leggings"),
    ("palazzo", "palazzo"), ("kurti", "kurti"), ("kurta", "kurta"), ("saree", "saree"),
    ("lehenga", "lehenga"), ("dress", "dress"), ("shirt", "shirt"), ("t-shirt", "t-shirt"),
    ("serum", "hair care"), ("perfume", "fragrance"),
)


def enrich_legacy_item(item: dict[str, Any]) -> dict[str, Any]:
    """Derive occasions, styles, subcategory and comfort from a prototype item's tags."""
    tags = [str(t).lower() for t in item.get("tags", [])]
    text = f"{item.get('name', '')} {' '.join(tags)}".lower()
    enriched = dict(item)
    if not enriched.get("occasions"):
        enriched["occasions"] = [o for o in CONCRETE_OCCASIONS if o in tags]
    if not enriched.get("styles"):
        enriched["styles"] = [s for s in STYLE_IDS if s in tags]
    if not enriched.get("subcategory"):
        enriched["subcategory"] = next((label for key, label in _SUBCATEGORY_HINTS if key in text), "")
    if enriched.get("category") == "tops" and "kurti" in text:
        enriched["category"] = "kurtis"
    if "comfortable" in tags and enriched.get("comfort", 3) == 3:
        enriched["comfort"] = 5
    return enriched
