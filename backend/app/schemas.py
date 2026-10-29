from __future__ import annotations

from typing import Any, Literal, get_args

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator
from pydantic.alias_generators import to_camel

WardrobeCategory = Literal[
    "tops",
    "bottoms",
    "dresses",
    "kurtis",
    "sarees",
    "footwear",
    "bags",
    "jewellery",
    "makeup",
    "skincare",
]
WARDROBE_CATEGORIES: tuple[str, ...] = get_args(WardrobeCategory)

OccasionId = Literal[
    "college", "casual", "office", "wedding", "party", "travel", "festival", "custom"
]
ConcreteOccasion = Literal["college", "casual", "office", "wedding", "party", "travel", "festival"]
CONCRETE_OCCASIONS: tuple[str, ...] = get_args(ConcreteOccasion)

StyleId = Literal["casual", "traditional", "western", "elegant", "trendy"]
BudgetId = Literal["under-500", "500-1500", "1500-3000", "3000-plus"]
PreferenceId = Literal["comfortable", "minimal", "trendy", "simple"]
ComfortLevel = Literal["low", "medium", "high"]
LookSlot = Literal["outfit", "footwear", "bag", "jewellery", "makeup", "hairstyle"]
LookSource = Literal["wardrobe", "shopping", "tip"]

# Uploaded photos are stored as compact data URLs; cap them to protect the DB.
MAX_IMAGE_CHARS = 2_000_000


class CamelModel(BaseModel):
    """Accepts and emits camelCase JSON to match the React frontend."""

    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True)


def _clean_list(values: list[str], limit: int = 60) -> list[str]:
    seen: dict[str, None] = {}
    for value in values:
        text = str(value).strip()[:limit]
        if text:
            seen.setdefault(text, None)
    return list(seen)


# ---------------------------------------------------------------- Wardrobe
class WardrobeItem(CamelModel):
    id: str = Field(min_length=1, max_length=80)
    name: str = Field(min_length=1, max_length=80)
    category: WardrobeCategory
    subcategory: str = Field(default="", max_length=40)
    colors: list[str] = Field(default_factory=list, max_length=6)
    styles: list[StyleId] = Field(default_factory=list, max_length=5)
    occasions: list[ConcreteOccasion] = Field(default_factory=list, max_length=7)
    fabric: str = Field(default="", max_length=40)
    comfort: int = Field(default=3, ge=1, le=5)
    price: float | None = Field(default=None, ge=0, le=10_000_000)
    brand: str | None = Field(default=None, max_length=60)
    notes: str | None = Field(default=None, max_length=300)
    tags: list[str] = Field(default_factory=list, max_length=40)
    image: str = Field(default="", max_length=MAX_IMAGE_CHARS)
    created_at: str = Field(min_length=1, max_length=40)

    @model_validator(mode="before")
    @classmethod
    def _upgrade_legacy(cls, data: Any) -> Any:
        """Accept the first-generation shape (single ``color``, ``beauty`` category)."""
        if not isinstance(data, dict):
            return data
        data = dict(data)
        if "colors" not in data and data.get("color"):
            data["colors"] = [data["color"]]
        data.pop("color", None)
        if data.get("category") == "beauty":
            data["category"] = legacy_beauty_category(data)
        return data

    @field_validator("colors", "tags")
    @classmethod
    def _dedupe(cls, value: list[str]) -> list[str]:
        return _clean_list(value)


def legacy_beauty_category(data: dict[str, Any]) -> str:
    """Old ``beauty`` items become ``makeup`` or ``skincare`` based on what they are."""
    text = " ".join([str(data.get("name", "")), *map(str, data.get("tags", []) or [])]).lower()
    makeup_words = ("lip", "foundation", "compact", "kajal", "mascara", "blush", "eye", "makeup")
    return "makeup" if any(w in text for w in makeup_words) else "skincare"


class WardrobeSync(CamelModel):
    items: list[WardrobeItem] = Field(max_length=500)


# ------------------------------------------------------------- Appearance
class Appearance(CamelModel):
    """Optional model-appearance preferences used only to build the image prompt."""

    skin_tone: Literal["fair", "wheatish", "medium", "olive", "tan", "deep"] | None = None
    hair_length: Literal["short", "medium", "long"] | None = None
    hair_texture: Literal["straight", "wavy", "curly"] | None = None
    build: Literal["slim", "athletic", "average", "curvy", "plus-size"] | None = None


# ---------------------------------------------------------- Recommendation
class LookPreferences(CamelModel):
    occasion: OccasionId
    custom_occasion: str | None = Field(default=None, max_length=80)
    style: StyleId | None = None
    colors: list[str] = Field(default_factory=list, max_length=30)
    budget: BudgetId = "500-1500"
    comfort: ComfortLevel = "medium"
    traits: list[PreferenceId] = Field(default_factory=list)
    notes: str = Field(default="", max_length=400)

    @field_validator("colors")
    @classmethod
    def _colors(cls, value: list[str]) -> list[str]:
        return _clean_list(value, 30)


class RecommendationRequest(LookPreferences):
    """Everything the stylist needs. ``wardrobe`` is the user's actual wardrobe;
    when omitted the server falls back to the wardrobe stored in its database."""

    wardrobe: list[WardrobeItem] | None = Field(default=None, max_length=500)
    max_outfits: int = Field(default=3, ge=1, le=5)
    appearance: Appearance | None = None


class ShopProduct(CamelModel):
    id: str
    name: str
    category: WardrobeCategory
    subcategory: str = ""
    colors: list[str] = Field(default_factory=list)
    price: float
    price_is_demo: bool = True
    image: str = ""
    occasions: list[ConcreteOccasion] = Field(default_factory=list)
    styles: list[StyleId] = Field(default_factory=list)
    fabric: str = ""
    comfort: int = 3
    description: str = ""
    owned_similar: bool = False


class OutfitPiece(CamelModel):
    category: WardrobeCategory
    name: str
    subcategory: str = ""
    colors: list[str] = Field(default_factory=list)
    fabric: str = ""
    image: str = Field(default="", max_length=MAX_IMAGE_CHARS)
    source: Literal["wardrobe", "shopping"]
    wardrobe_item_id: str | None = None
    shop_item_id: str | None = None
    price: float | None = None


class OutfitItem(CamelModel):
    slot: LookSlot
    title: str
    category: str
    detail: str = ""
    image: str = Field(default="", max_length=MAX_IMAGE_CHARS)
    source: LookSource
    pieces: list[OutfitPiece] = Field(default_factory=list)
    wardrobe_item_ids: list[str] = Field(default_factory=list)
    shop_item_id: str | None = None


class MissingItem(CamelModel):
    slot: LookSlot
    category: str
    label: str
    reason: str
    suggestion: ShopProduct | None = None
    alternatives: list[ShopProduct] = Field(default_factory=list)
    within_budget: bool = True


class ScorePart(CamelModel):
    key: str
    label: str
    points: float
    max_points: float


class GeneratedImage(CamelModel):
    url: str
    provider: str
    model: str
    generated_at: str
    kind: Literal["ai-generated"] = "ai-generated"
    used_reference_images: bool = False


class Outfit(CamelModel):
    id: str = Field(min_length=1, max_length=80)
    request_id: str = ""
    rank: int = 1
    title: str = Field(max_length=120)
    score: float
    score_label: str
    breakdown: list[ScorePart] = Field(default_factory=list)
    why_it_works: list[str] = Field(default_factory=list)
    occasion: OccasionId
    occasion_label: str = Field(max_length=80)
    resolved_occasion: ConcreteOccasion
    preferences: LookPreferences
    appearance: Appearance | None = None
    items: list[OutfitItem] = Field(max_length=12)
    accessories: list[OutfitPiece] = Field(default_factory=list)
    styling_tips: list[str] = Field(default_factory=list, max_length=20)
    missing_items: list[MissingItem] = Field(default_factory=list)
    suggested_total: float = 0
    budget_max: float | None = None
    image: GeneratedImage | None = None
    generated_at: str


class RecommendationResponse(CamelModel):
    request_id: str
    occasion: OccasionId
    occasion_label: str
    resolved_occasion: ConcreteOccasion
    wardrobe_source: Literal["request", "database"]
    wardrobe_size: int
    outfits: list[Outfit]
    limitations: list[str] = Field(default_factory=list)
    engine_version: str
    generated_at: str


# ------------------------------------------------------------- Saved looks
class SavedLook(Outfit):
    favorite: bool = False
    saved_at: str
    is_sample: bool = False


class SavedLookSync(CamelModel):
    looks: list[SavedLook] = Field(max_length=500)


class FavoritePatch(CamelModel):
    favorite: bool


# ------------------------------------------------------- Image generation
class GenerateImageRequest(CamelModel):
    regenerate: bool = False
    appearance: Appearance | None = None
    use_reference_images: bool = False


class GenerateImageResponse(CamelModel):
    status: Literal["ready", "not_configured"]
    outfit_id: str
    image: GeneratedImage | None = None
    cached: bool = False
    message: str = ""
    disclaimer: str = ""


class ErrorDetail(CamelModel):
    code: str
    message: str
    retryable: bool = False


# ------------------------------------------------------------------- Misc
class ImageStatus(CamelModel):
    configured: bool
    provider: str
    model: str | None = None
    message: str = ""


class HealthResponse(CamelModel):
    status: Literal["ok"] = "ok"
    service: str = "sierrah-api"
    version: str
    image_generation: ImageStatus
