"""Occasion knowledge: what each occasion calls for.

These profiles are the stylist's "rulebook". They are plain data so they are easy to
review, tune and test. Nothing here picks a fixed outfit; the engine scores the
user's real pieces against these preferences.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field


@dataclass(frozen=True)
class MakeupLook:
    name: str
    description: str
    vibe: tuple[str, ...] = ()  # words matched against traits / style: minimal, bold, glam...


@dataclass(frozen=True)
class HairLook:
    name: str
    description: str
    vibe: tuple[str, ...] = ()


@dataclass(frozen=True)
class OccasionProfile:
    key: str
    label: str
    formality: float  # target formality, 1 (relaxed) .. 5 (very dressy)
    comfort_weight: float  # how much comfort matters, 0..1
    # How suitable each garment "mode" is. A mode is a way to build the base outfit.
    modes: dict[str, float]
    # Subcategory keywords that suit / do not suit the occasion, per category.
    prefer: dict[str, tuple[str, ...]]
    avoid: dict[str, tuple[str, ...]]
    good_fabrics: tuple[str, ...] = ()
    avoid_fabrics: tuple[str, ...] = ()
    # Occasions whose wardrobe tags count as a partial match (0..1).
    related: dict[str, float] = field(default_factory=dict)
    accessory_note: str = ""
    makeup: tuple[MakeupLook, ...] = ()
    hair: tuple[HairLook, ...] = ()
    tips: tuple[str, ...] = ()
    # Slots a complete look needs, and whether a jewellery piece is expected.
    wants_jewellery: bool = True
    # Catalog suggestions for this occasion in priority order (subcategory keywords).
    catalog_core: tuple[tuple[str, ...], ...] = ()


PROFILES: dict[str, OccasionProfile] = {
    "college": OccasionProfile(
        key="college",
        label="College",
        formality=2.0,
        comfort_weight=0.9,
        modes={"separates": 1.0, "kurti_set": 1.0, "dress": 0.45, "ethnic": 0.0},
        prefer={
            "tops": ("t-shirt", "tee", "top", "shirt"),
            "kurtis": ("kurti", "kurta"),
            "bottoms": ("jeans", "trouser", "palazzo", "legging"),
            "footwear": ("sneaker", "flat", "sandal", "loafer"),
            "bags": ("backpack", "tote", "sling", "crossbody", "shoulder"),
            "jewellery": ("stud", "earring", "watch", "pendant", "bracelet"),
        },
        avoid={
            "footwear": ("stiletto", "heel", "wedge"),
            "bags": ("clutch", "potli"),
            "jewellery": ("jhumka", "necklace set", "bangles"),
            "sarees": ("saree", "lehenga"),
            "dresses": ("gown", "party", "anarkali"),
        },
        good_fabrics=("cotton", "denim", "linen", "jersey"),
        avoid_fabrics=("silk", "net", "satin", "velvet"),
        related={"casual": 0.85, "office": 0.45, "travel": 0.6},
        accessory_note="Practical bag and simple, small accessories keep the look campus-ready.",
        makeup=(
            MakeupLook("Natural Fresh Look", "Skin tint or compact, a touch of mascara and a soft lip balm.", ("minimal", "simple", "casual")),
            MakeupLook("Soft Pink Glow", "Light base, a dab of blush and a rosy lip tint for lectures and lunch.", ("trendy", "elegant")),
            MakeupLook("Kohl and Gloss", "Smudge-proof kohl with a clear gloss; five minutes, no fuss.", ("trendy", "bold")),
        ),
        hair=(
            HairLook("Soft Waves", "Loose, easy waves finished with a drop of serum.", ("casual", "trendy")),
            HairLook("High Ponytail", "A sleek high ponytail that stays put all day.", ("simple", "comfortable")),
            HairLook("Half-Up Clip", "Half-up with a claw clip; neat and quick.", ("minimal", "trendy")),
        ),
        tips=(
            "Stick to two main colours and let the bag or shoes add the third.",
            "Choose breathable cotton so you stay comfortable between lectures.",
            "Finish with a tiny pair of earrings rather than a big statement piece.",
        ),
        catalog_core=(("kurti",), ("t-shirt", "top"), ("jeans",)),
    ),
    "casual": OccasionProfile(
        key="casual",
        label="Casual",
        formality=1.5,
        comfort_weight=0.85,
        modes={"separates": 1.0, "kurti_set": 0.6, "dress": 0.75, "ethnic": 0.0},
        prefer={
            "tops": ("t-shirt", "tee", "top", "crop"),
            "bottoms": ("jeans", "shorts", "jogger", "legging", "skirt"),
            "footwear": ("sneaker", "sandal", "flat"),
            "bags": ("sling", "crossbody", "tote", "backpack"),
            "jewellery": ("stud", "watch", "bracelet", "earring", "pendant"),
        },
        avoid={
            "footwear": ("stiletto", "juttis"),
            "bags": ("clutch", "potli"),
            "jewellery": ("necklace set", "jhumka"),
            "sarees": ("saree", "lehenga"),
            "dresses": ("gown", "party", "anarkali"),
        },
        good_fabrics=("cotton", "denim", "linen", "jersey", "chiffon"),
        avoid_fabrics=("silk", "net", "velvet", "satin"),
        related={"college": 0.85, "travel": 0.7, "party": 0.35},
        accessory_note="Minimal accessories; one neutral bag ties casual outfits together.",
        makeup=(
            MakeupLook("Fresh Face", "Tinted moisturiser, a glossy lip and a hint of blush.", ("minimal", "simple", "casual")),
            MakeupLook("Sun-Kissed Glow", "Bronzer on the cheeks, mascara and a peachy lip.", ("trendy", "bold")),
        ),
        hair=(
            HairLook("Open Hair", "Loose waves with a little serum for shine.", ("casual", "simple")),
            HairLook("Messy Bun", "A relaxed top-knot with a few face-framing strands.", ("comfortable", "minimal")),
            HairLook("Side Braid", "A loose side braid; easy and photogenic.", ("trendy", "simple")),
        ),
        tips=(
            "Tuck in the front of your top to define your waist.",
            "Mix one textured piece (denim, knit) with one smooth piece.",
            "A neutral bag ties together almost any casual outfit.",
        ),
        catalog_core=(("t-shirt", "top"), ("jeans",), ("dress",)),
    ),
    "office": OccasionProfile(
        key="office",
        label="Office",
        formality=3.6,
        comfort_weight=0.55,
        modes={"separates": 1.0, "kurti_set": 0.85, "dress": 0.6, "ethnic": 0.1},
        prefer={
            "tops": ("formal shirt", "shirt", "blouse", "top"),
            "kurtis": ("kurti", "kurta", "straight"),
            "bottoms": ("trouser", "pants", "skirt", "palazzo"),
            "footwear": ("flat", "loafer", "pump", "block", "heel"),
            "bags": ("tote", "handbag", "satchel", "structured"),
            "jewellery": ("stud", "earring", "watch", "pendant"),
        },
        avoid={
            "footwear": ("flip", "sneaker", "stiletto"),
            "bags": ("backpack", "clutch", "potli"),
            "jewellery": ("jhumka", "necklace set", "bangles"),
            "tops": ("crop", "t-shirt", "tee"),
            "bottoms": ("shorts", "jeans", "jogger", "legging"),
            "sarees": ("lehenga",),
            "dresses": ("gown", "party"),
        },
        good_fabrics=("cotton", "crepe", "linen", "polyester", "cotton blend"),
        avoid_fabrics=("sequin", "net", "velvet"),
        related={"college": 0.5, "casual": 0.35, "party": 0.35},
        accessory_note="Subtle jewellery and a structured bag read polished.",
        makeup=(
            MakeupLook("Soft Neutral", "Matte base, subtle lip and defined brows.", ("minimal", "simple", "elegant")),
            MakeupLook("Polished Berry", "Even base, neutral eyes and a muted berry lip.", ("elegant", "trendy")),
        ),
        hair=(
            HairLook("Sleek Low Ponytail", "Neat and meeting-ready.", ("minimal", "simple", "elegant")),
            HairLook("Smooth Blow-Dry", "Straight, shoulder-skimming hair with a centre or side part.", ("elegant", "trendy")),
            HairLook("Low Bun", "A tidy low bun keeps hair away from your face.", ("comfortable", "minimal")),
        ),
        tips=(
            "Keep the palette tonal: cream, black, navy or soft pastels.",
            "Let one accessory be the focus, not three.",
            "Carry a spare compact for a mid-day refresh.",
        ),
        catalog_core=(("formal shirt", "top"), ("trouser",), ("kurti",)),
    ),
    "wedding": OccasionProfile(
        key="wedding",
        label="Wedding",
        formality=4.7,
        comfort_weight=0.25,
        modes={"ethnic": 1.0, "kurti_set": 0.6, "dress": 0.45, "separates": 0.1},
        prefer={
            "sarees": ("saree", "lehenga"),
            "kurtis": ("anarkali", "kurta set", "silk", "embroider", "kurti"),
            "dresses": ("anarkali", "gown", "lehenga", "suit", "party"),
            "bottoms": ("palazzo", "churidar", "skirt", "trouser", "sharara"),
            "footwear": ("heel", "jutti", "wedge", "embellished", "sandal"),
            "bags": ("clutch", "potli"),
            "jewellery": ("jhumka", "necklace", "bangle", "earring", "set"),
        },
        avoid={
            "footwear": ("sneaker", "flip"),
            "bags": ("backpack", "sling", "tote"),
            "tops": ("t-shirt", "tee"),
            "bottoms": ("jeans", "shorts", "jogger", "legging"),
            "jewellery": ("watch",),
        },
        good_fabrics=("silk", "net", "georgette", "brocade", "velvet", "chiffon", "satin", "organza"),
        avoid_fabrics=("denim", "jersey", "canvas"),
        related={"festival": 0.9, "party": 0.55, "office": 0.15},
        accessory_note="Coordinated jewellery, a clutch and dressy footwear complete a wedding look.",
        makeup=(
            MakeupLook("Radiant Festive Glam", "Luminous base, kohl-lined eyes and a rose or red lip.", ("elegant", "traditional", "bold")),
            MakeupLook("Soft Bridal-Guest Glow", "Champagne eyeshadow, soft contour and a nude-rose lip.", ("minimal", "simple", "soft")),
            MakeupLook("Bold Red Lip", "Classic winged liner with a statement red lip for rich fabrics.", ("bold", "trendy")),
        ),
        hair=(
            HairLook("Low Bun with Flowers", "Classic and camera-ready; pin fresh flowers last.", ("traditional", "elegant")),
            HairLook("Soft Curls", "Brushed-out curls worn open over one shoulder.", ("trendy", "elegant")),
            HairLook("Braided Updo", "A textured braid pinned up with small jewelled clips.", ("traditional", "minimal")),
        ),
        tips=(
            "Pick one hero piece: either heavy jewellery or a heavy outfit, not both.",
            "Break in new footwear at home before the day.",
            "Pin fresh flowers last so they stay crisp.",
        ),
        catalog_core=(("saree", "lehenga"), ("anarkali", "kurti")),
    ),
    "party": OccasionProfile(
        key="party",
        label="Party",
        formality=4.0,
        comfort_weight=0.3,
        modes={"dress": 1.0, "separates": 0.65, "kurti_set": 0.25, "ethnic": 0.2},
        prefer={
            "dresses": ("party", "dress", "co-ord", "gown", "jumpsuit", "satin"),
            "tops": ("top", "blouse", "crop", "shirt"),
            "bottoms": ("skirt", "trouser", "pants"),
            "footwear": ("heel", "stiletto", "wedge", "pump"),
            "bags": ("clutch", "mini", "handbag", "crossbody"),
            "jewellery": ("earring", "statement", "necklace", "bracelet", "jhumka"),
        },
        avoid={
            "footwear": ("flip", "sneaker"),
            "bags": ("backpack", "tote"),
            "bottoms": ("shorts", "jogger", "legging"),
            "tops": ("t-shirt", "tee"),
            "jewellery": ("watch",),
        },
        good_fabrics=("satin", "silk", "velvet", "sequin", "chiffon", "crepe", "georgette"),
        avoid_fabrics=("canvas", "jersey"),
        related={"wedding": 0.55, "festival": 0.5, "office": 0.3, "casual": 0.3},
        accessory_note="Statement accessories and matching footwear do the heavy lifting.",
        makeup=(
            MakeupLook("Defined Eyes and Bold Lip", "Winged liner, highlighter and a rich lip colour.", ("bold", "trendy", "elegant")),
            MakeupLook("Smoky Eye with Nude Lip", "Soft smoked-out eyes balanced by a neutral lip.", ("elegant", "minimal")),
            MakeupLook("Glossy Glam", "Dewy base, bronzed cheeks and a glossy berry lip.", ("trendy", "simple")),
        ),
        hair=(
            HairLook("Sleek Waves", "Glossy, brushed-out curls.", ("elegant", "trendy")),
            HairLook("High Sleek Pony", "A polished high ponytail that shows off statement earrings.", ("minimal", "bold")),
            HairLook("Half-Up Twist", "A twisted half-up style with face-framing pieces.", ("simple", "elegant")),
        ),
        tips=(
            "If the outfit is bold, keep the jewellery to one standout piece.",
            "Carry lipstick for quick touch-ups.",
            "Choose fabrics that do not cling when you dance.",
        ),
        catalog_core=(("party dress", "dress"), ("top",), ("trouser", "skirt")),
    ),
    "travel": OccasionProfile(
        key="travel",
        label="Travel",
        formality=1.4,
        comfort_weight=1.0,
        modes={"separates": 1.0, "kurti_set": 0.85, "dress": 0.55, "ethnic": 0.0},
        prefer={
            "tops": ("t-shirt", "tee", "top", "shirt"),
            "kurtis": ("kurti", "kurta"),
            "bottoms": ("jeans", "legging", "jogger", "trouser", "palazzo"),
            "footwear": ("sneaker", "walking", "sandal", "flat"),
            "bags": ("backpack", "crossbody", "sling", "tote"),
            "jewellery": ("stud", "watch", "bracelet"),
        },
        avoid={
            "footwear": ("stiletto", "heel", "wedge", "jutti"),
            "bags": ("clutch", "potli"),
            "jewellery": ("jhumka", "necklace", "bangle"),
            "sarees": ("saree", "lehenga"),
            "dresses": ("gown", "party", "anarkali"),
        },
        good_fabrics=("cotton", "linen", "jersey", "denim", "cotton blend"),
        avoid_fabrics=("silk", "net", "velvet", "satin", "sequin"),
        related={"casual": 0.8, "college": 0.65},
        accessory_note="Keep accessories minimal and secure for long days on the move.",
        makeup=(
            MakeupLook("Sun-Safe Basics", "SPF, tinted balm and a touch of blush.", ("minimal", "simple", "casual")),
            MakeupLook("Travel Glow", "Light base, cream blush and waterproof mascara.", ("trendy", "elegant")),
        ),
        hair=(
            HairLook("Loose Braid", "Heat-proof and low maintenance.", ("simple", "comfortable")),
            HairLook("Top Knot", "A neat top knot that survives wind and long journeys.", ("minimal", "casual")),
            HairLook("Low Ponytail", "Easy to redo and comfortable under a cap.", ("simple", "minimal")),
        ),
        tips=(
            "Choose pieces that mix and match so one bag of clothes covers several days.",
            "Wear the bulkiest shoes on the journey.",
            "Pack a scarf: it doubles as a layer and an accessory.",
        ),
        catalog_core=(("t-shirt", "top"), ("jeans",), ("kurti",)),
    ),
    "festival": OccasionProfile(
        key="festival",
        label="Festival",
        formality=4.0,
        comfort_weight=0.55,
        modes={"ethnic": 1.0, "kurti_set": 1.0, "dress": 0.4, "separates": 0.1},
        prefer={
            "sarees": ("saree", "lehenga"),
            "kurtis": ("anarkali", "embroider", "silk", "kurti", "kurta set"),
            "dresses": ("anarkali", "suit", "lehenga"),
            "bottoms": ("palazzo", "churidar", "sharara", "trouser", "skirt"),
            "footwear": ("jutti", "sandal", "flat", "heel"),
            "bags": ("potli", "clutch", "sling"),
            "jewellery": ("jhumka", "earring", "bangle", "necklace", "set"),
        },
        avoid={
            "footwear": ("sneaker",),
            "bags": ("backpack",),
            "bottoms": ("jeans", "shorts", "jogger"),
            "tops": ("t-shirt", "tee"),
        },
        good_fabrics=("silk", "cotton silk", "georgette", "chanderi", "brocade", "cotton", "chiffon"),
        avoid_fabrics=("denim", "canvas", "jersey"),
        related={"wedding": 0.9, "party": 0.5, "college": 0.4, "office": 0.3},
        accessory_note="Traditional jewellery and comfortable festive footwear finish the look.",
        makeup=(
            MakeupLook("Warm Festive Glow", "Golden shimmer on the lids and a berry lip.", ("traditional", "elegant")),
            MakeupLook("Kohl and Bindi", "Strong kohl, a small bindi and a soft nude lip.", ("minimal", "simple", "traditional")),
            MakeupLook("Jewel-Tone Eyes", "Teal or plum liner with a bright lip for rich fabrics.", ("bold", "trendy")),
        ),
        hair=(
            HairLook("Braided Half-Up", "Add a gajra or small pins.", ("traditional", "elegant")),
            HairLook("Neat Centre-Part Plait", "A long plait with fresh flowers woven in.", ("traditional", "simple")),
            HairLook("Soft Waves with Clips", "Open waves with embellished clips.", ("trendy", "elegant")),
        ),
        tips=(
            "Echo one colour from the outfit in your lips or bangles.",
            "Contrast a rich outfit with simple makeup, or the reverse.",
            "Keep a small safety-pin kit in your bag for dupatta emergencies.",
        ),
        catalog_core=(("saree", "lehenga"), ("kurti",)),
    ),
}

# ---------------------------------------------------------------- custom text
KEYWORDS: tuple[tuple[re.Pattern[str], str], ...] = (
    (re.compile(r"wedding|shaadi|sangeet|mehendi|mehndi|engagement|reception|haldi|bridal"), "wedding"),
    (re.compile(r"festival|diwali|puja|pooja|eid|navratri|onam|pongal|holi|ganesh|dussehra|lohri|raksha"), "festival"),
    (re.compile(r"office|work|interview|meeting|presentation|corporate|conference|formal"), "office"),
    (re.compile(r"party|club|night|birthday|date|dinner|cocktail|anniversary|prom|farewell"), "party"),
    (re.compile(r"travel|trip|vacation|holiday|flight|beach|hike|trek|airport|road ?trip"), "travel"),
    (re.compile(r"college|campus|class|school|exam|university|lecture|fresher"), "college"),
    (re.compile(r"brunch|casual|coffee|mall|shopping|movie|outing|hangout|walk"), "casual"),
)


def resolve_occasion(occasion: str, custom: str | None, notes: str = "") -> tuple[str, bool]:
    """Map the chosen occasion to a built-in profile key.

    Returns ``(profile_key, matched_by_keyword)``. Custom occasions are matched on
    keywords; when nothing matches, "casual" is used and the caller says so.
    """
    if occasion != "custom":
        return occasion, False
    text = f"{custom or ''} {notes or ''}".lower()
    for pattern, key in KEYWORDS:
        if pattern.search(text):
            return key, True
    return "casual", False


# ------------------------------------------------------------------ formality
# Rough formality (1 relaxed .. 5 very dressy) by subcategory/name keyword.
FORMALITY: tuple[tuple[str, float], ...] = (
    ("lehenga", 5.0), ("saree", 4.8), ("gown", 5.0), ("anarkali", 4.6), ("sharara", 4.5),
    ("party", 4.2), ("co-ord", 3.5), ("jumpsuit", 3.5),
    ("formal shirt", 3.8), ("blouse", 3.5), ("shirt", 3.2), ("crop", 2.0), ("t-shirt", 1.2),
    ("tee", 1.2), ("tank", 1.2), ("top", 2.4), ("sweater", 2.0), ("hoodie", 1.0),
    ("kurta set", 3.8), ("kurti", 2.8), ("kurta", 3.0),
    ("trouser", 3.4), ("pants", 3.2), ("palazzo", 2.6), ("churidar", 3.4), ("skirt", 3.0),
    ("jeans", 1.6), ("legging", 1.4), ("jogger", 1.0), ("shorts", 1.0),
    ("dress", 3.2),
    ("stiletto", 4.6), ("heel", 4.0), ("pump", 3.8), ("wedge", 3.5), ("jutti", 3.6), ("loafer", 3.0),
    ("flat", 2.6), ("sandal", 2.0), ("sneaker", 1.1), ("boots", 2.5), ("flip", 0.8),
    ("clutch", 4.5), ("potli", 4.5), ("handbag", 3.2), ("tote", 3.0), ("satchel", 3.2),
    ("shoulder", 2.6), ("crossbody", 1.8), ("sling", 1.6), ("backpack", 1.0),
    ("jhumka", 4.5), ("necklace", 4.0), ("bangle", 4.0), ("statement", 4.0), ("earring", 3.0),
    ("stud", 2.2), ("watch", 2.4), ("bracelet", 2.6), ("pendant", 2.6),
)


def formality_of(text: str) -> float | None:
    low = text.lower()
    for key, value in FORMALITY:
        if key in low:
            return value
    return None


def keyword_in(text: str, words: tuple[str, ...]) -> bool:
    low = text.lower()
    return any(w in low for w in words)
