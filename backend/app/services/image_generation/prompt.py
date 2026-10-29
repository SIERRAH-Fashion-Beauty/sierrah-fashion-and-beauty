"""Turns a recommended outfit into a text-to-image prompt.

Only structured data (item names, colours, fabrics) and a fixed set of optional
appearance choices go into the prompt. Free-text user input such as the "Special
Requirements" box is never copied in, and item names are sanitised, so a wardrobe
item called "ignore the above and ..." cannot steer the model.
"""

from __future__ import annotations

import re
import zlib

from ...schemas import Appearance, Outfit, OutfitItem, OutfitPiece

_SAFE = re.compile(r"[^A-Za-z0-9 &'+/\-]")

BACKGROUNDS: dict[str, tuple[str, ...]] = {
    "college": (
        "a bright airy photo studio with a soft cream backdrop",
        "a clean studio with a pale blush backdrop and soft daylight",
        "a minimal studio with a warm ivory backdrop and a hint of greenery",
    ),
    "casual": (
        "a sunlit minimal studio with a warm beige backdrop",
        "a clean cream studio with soft natural window light",
        "a pale peach studio backdrop with gentle shadows",
    ),
    "office": (
        "a refined light-grey and ivory studio with soft even lighting",
        "a clean neutral studio with a subtle architectural feel",
        "a minimal warm-white studio with crisp soft light",
    ),
    "wedding": (
        "an elegant ivory studio with warm golden light and subtle floral styling",
        "a soft champagne backdrop with warm glowing light and delicate drapery",
        "a cream studio with a muted rose-gold glow",
    ),
    "party": (
        "a stylish studio with a deep blush backdrop and warm spotlighting",
        "a glamorous dark-champagne studio with soft rim lighting",
        "a polished studio with a rose-toned gradient and gentle sparkle",
    ),
    "travel": (
        "a bright airy studio with a soft sand-coloured backdrop and natural light",
        "a clean pale-sky studio with fresh daylight",
        "a warm neutral studio with a light linen texture backdrop",
    ),
    "festival": (
        "a warm studio with a soft marigold-and-cream backdrop and glowing light",
        "an ivory studio with golden diya-like warm highlights",
        "a rich cream studio with subtle traditional motifs in warm light",
    ),
}

SLOT_LABEL = {"footwear": "Footwear", "bag": "Bag", "jewellery": "Jewellery"}


def clean(text: str, limit: int = 50) -> str:
    return _SAFE.sub("", text or "").strip()[:limit]


def describe_piece(piece: OutfitPiece) -> str:
    name = clean(piece.name)
    traits = [clean(c, 20) for c in piece.colors[:2]]
    if piece.fabric:
        traits.append(clean(piece.fabric, 20).lower())
    if piece.subcategory and clean(piece.subcategory, 20).lower() not in name.lower():
        traits.append(clean(piece.subcategory, 20).lower())
    detail = ", ".join(t for t in traits if t)
    return f"{name} ({detail})" if detail else name


def _item_text(item: OutfitItem) -> str:
    if item.pieces:
        return " with ".join(describe_piece(p) for p in item.pieces)
    return clean(item.title, 80)


def appearance_text(appearance: Appearance | None) -> str:
    if appearance is None:
        return "an attractive adult woman model in her late twenties"
    parts = ["an attractive adult woman model in her late twenties"]
    if appearance.skin_tone:
        parts.append(f"with {appearance.skin_tone} skin tone")
    hair = " ".join(p for p in (appearance.hair_length, appearance.hair_texture) if p)
    if hair:
        parts.append(f"{hair} hair")
    if appearance.build:
        parts.append(f"{appearance.build} build")
    return ", ".join(parts)


def pick_background(outfit: Outfit) -> str:
    options = BACKGROUNDS.get(outfit.resolved_occasion, BACKGROUNDS["casual"])
    return options[zlib.crc32(outfit.id.encode()) % len(options)]


def build_prompt(outfit: Outfit, appearance: Appearance | None = None, *, with_references: bool = False) -> str:
    """Create the text prompt for an outfit. ``appearance`` overrides the outfit's own."""
    appearance = appearance or outfit.appearance
    by_slot = {item.slot: item for item in outfit.items}

    lines = [
        "Photorealistic full-length editorial fashion photograph for a premium fashion magazine.",
        f"A single subject: {appearance_text(appearance)}, standing in a relaxed confident pose, "
        "entire body visible from head to toe including both feet and shoes, centred in a portrait frame.",
    ]
    if "outfit" in by_slot and by_slot["outfit"].pieces:
        lines.append(f"Outfit: {_item_text(by_slot['outfit'])}.")
    else:
        lines.append(f"Outfit: {clean(by_slot['outfit'].title, 80)}." if "outfit" in by_slot else "")
    for slot in ("footwear", "bag", "jewellery"):
        item = by_slot.get(slot)
        if item:
            lines.append(f"{SLOT_LABEL[slot]}: {_item_text(item)}.")
    if "makeup" in by_slot:
        makeup = by_slot["makeup"]
        lines.append(f"Makeup: {clean(makeup.title, 60)} ({clean(makeup.detail.split(' · ')[0], 140)}).")
    if "hairstyle" in by_slot:
        hair = by_slot["hairstyle"]
        lines.append(f"Hairstyle: {clean(hair.title, 60)}, neat and well groomed.")

    lines.append(
        f"Occasion: {clean(outfit.occasion_label, 40)}. The styling should look appropriate for it. "
        f"Background: {pick_background(outfit)}."
    )
    lines.append(
        "Premium editorial studio lighting with soft shadows. Natural facial features, natural hands with five "
        "fingers, natural feet, realistic body proportions. Realistic fabric textures and drape, garments well "
        "fitted, clothing, footwear, bag and jewellery coordinated exactly as listed."
    )
    if with_references:
        lines.append(
            "Reference photos of some of the listed garments are attached. Use them as a loose guide for colour, cut "
            "and fabric, and do not copy any person or background from them."
        )
    lines.append("No text, no captions, no logos, no watermarks, no extra people, no extra limbs.")
    return "\n".join(line for line in lines if line)
