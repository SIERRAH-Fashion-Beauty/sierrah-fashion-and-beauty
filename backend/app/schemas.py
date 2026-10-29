from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field
from pydantic.alias_generators import to_camel

WardrobeCategory = Literal[
    "tops", "bottoms", "dresses", "footwear", "bags", "jewellery", "beauty"
]
OccasionId = Literal[
    "college", "casual", "office", "wedding", "party", "travel", "festival", "custom"
]
StyleId = Literal["casual", "traditional", "western", "elegant", "trendy"]
BudgetId = Literal["under-500", "500-1500", "1500-3000", "3000-plus"]
PreferenceId = Literal["comfortable", "minimal", "trendy", "simple"]
LookSlot = Literal["outfit", "footwear", "bag", "jewellery", "makeup", "hairstyle"]
LookSource = Literal["wardrobe", "suggested", "tip"]

# Uploaded photos are stored as compact data URLs; cap them to protect the DB.
MAX_IMAGE_CHARS = 2_000_000


class CamelModel(BaseModel):
    """Accepts and emits camelCase JSON to match the React frontend."""

    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True)


# ---------------------------------------------------------------- Wardrobe
class WardrobeItem(CamelModel):
    id: str = Field(min_length=1, max_length=80)
    name: str = Field(min_length=1, max_length=80)
    category: WardrobeCategory
    color: str = Field(default="", max_length=40)
    tags: list[str] = Field(default_factory=list, max_length=40)
    brand: str | None = Field(default=None, max_length=60)
    notes: str | None = Field(default=None, max_length=300)
    image: str = Field(default="", max_length=MAX_IMAGE_CHARS)
    created_at: str = Field(min_length=1, max_length=40)


class WardrobeSync(CamelModel):
    items: list[WardrobeItem] = Field(max_length=500)


# ------------------------------------------------------------- Saved looks
class LookItem(CamelModel):
    slot: LookSlot
    title: str = Field(max_length=120)
    subtitle: str = Field(default="", max_length=300)
    image: str = Field(default="", max_length=MAX_IMAGE_CHARS)
    source: LookSource
    wardrobe_item_ids: list[str] | None = None
    shop_item_id: str | None = None


class LookPreferences(CamelModel):
    occasion: OccasionId
    custom_occasion: str | None = Field(default=None, max_length=80)
    style: StyleId | None = None
    colors: list[str] = Field(default_factory=list, max_length=30)
    budget: BudgetId
    traits: list[PreferenceId] = Field(default_factory=list)
    notes: str = Field(default="", max_length=400)


class SavedLook(CamelModel):
    id: str = Field(min_length=1, max_length=80)
    title: str = Field(min_length=1, max_length=120)
    occasion: OccasionId
    occasion_label: str = Field(max_length=80)
    model_image: str = Field(default="", max_length=MAX_IMAGE_CHARS)
    preferences: LookPreferences
    items: list[LookItem] = Field(max_length=12)
    tips: list[str] = Field(default_factory=list, max_length=20)
    generated_at: str
    favorite: bool = False
    saved_at: str


class SavedLookSync(CamelModel):
    looks: list[SavedLook] = Field(max_length=500)


class FavoritePatch(CamelModel):
    favorite: bool


# ------------------------------------------------------------- Misc
class HealthResponse(CamelModel):
    status: Literal["ok"] = "ok"
    service: str = "sierrah-api"
    version: str


class LookImageRequest(CamelModel):
    """The frontend sends the look it wants a generated model image for."""

    look: dict


class LookImageResponse(CamelModel):
    status: Literal["not_configured", "queued", "ready", "error"]
    provider: str
    image_url: str | None = None
    message: str
