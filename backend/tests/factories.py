"""Small builders for test payloads."""

from __future__ import annotations

from typing import Any

CREATED = "2026-10-29T10:00:00.000Z"


def item(
    item_id: str = "test-1",
    name: str = "Test Top",
    category: str = "tops",
    *,
    subcategory: str = "top",
    colors: list[str] | None = None,
    styles: list[str] | None = None,
    occasions: list[str] | None = None,
    fabric: str = "Cotton",
    comfort: int = 4,
    price: float | None = None,
    tags: list[str] | None = None,
    image: str = "",
) -> dict[str, Any]:
    return {
        "id": item_id,
        "name": name,
        "category": category,
        "subcategory": subcategory,
        "colors": colors if colors is not None else ["Blue"],
        "styles": styles or [],
        "occasions": occasions or [],
        "fabric": fabric,
        "comfort": comfort,
        "price": price,
        "tags": tags or [],
        "image": image,
        "createdAt": CREATED,
    }


def recommendation_request(**overrides: Any) -> dict[str, Any]:
    body: dict[str, Any] = {"occasion": "college", "budget": "500-1500", "maxOutfits": 3}
    body.update(overrides)
    return body


def saree_wardrobe() -> list[dict[str, Any]]:
    """A wardrobe that *can* dress a wedding from what it owns."""
    return [
        item("w-saree", "Red Silk Saree", "sarees", subcategory="saree", colors=["Red"], styles=["traditional"],
             occasions=["wedding", "festival"], fabric="Silk", comfort=3),
        item("w-lehenga", "Pink Lehenga", "sarees", subcategory="lehenga", colors=["Pink"], styles=["traditional"],
             occasions=["wedding"], fabric="Net", comfort=2),
        item("w-heels", "Gold Heels", "footwear", subcategory="heels", colors=["Gold"], styles=["elegant"],
             occasions=["wedding", "party"], fabric="Faux leather", comfort=2),
        item("w-clutch", "Gold Clutch", "bags", subcategory="clutch", colors=["Gold"], styles=["elegant"],
             occasions=["wedding", "party"], fabric="Embellished fabric", comfort=3),
        item("w-jhumka", "Gold Jhumkas", "jewellery", subcategory="jhumkas", colors=["Gold"], styles=["traditional"],
             occasions=["wedding", "festival"], fabric="Metal", comfort=3),
        item("w-lip", "Rose Lipstick", "makeup", subcategory="lipstick", colors=["Pink"], styles=["elegant"],
             occasions=["wedding", "party", "festival"], fabric="", comfort=5),
    ]
