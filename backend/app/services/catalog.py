"""Demo shopping catalog.

Products and prices are sample data (``priceIsDemo`` is always true). SIERRAH is not
connected to a live retailer, so nothing here is real stock, price or availability.
"""

from __future__ import annotations

import json
import re
from functools import lru_cache
from pathlib import Path

from ..schemas import ShopProduct, WardrobeItem

CATALOG_FILE = Path(__file__).resolve().parent.parent / "data" / "shop_catalog.json"


def _stem(word: str) -> str:
    word = word.lower()
    return word[:-1] if word.endswith("s") and len(word) > 3 else word


def _words(text: str) -> set[str]:
    return {_stem(w) for w in re.findall(r"[a-z\-]+", text.lower()) if len(w) > 2}


def is_similar(subcategory_a: str, name_a: str, subcategory_b: str, name_b: str) -> bool:
    """Do two products look like the same kind of thing (e.g. both sneakers)?"""
    a = _words(subcategory_a) or _words(name_a)
    b = _words(subcategory_b) or _words(name_b)
    return bool(a & b)


class CatalogService:
    def __init__(self, products: list[ShopProduct]) -> None:
        self._products = products
        self._by_id = {p.id: p for p in products}

    @classmethod
    def load(cls, path: Path = CATALOG_FILE) -> "CatalogService":
        raw = json.loads(path.read_text(encoding="utf-8"))
        return cls([ShopProduct.model_validate(p) for p in raw])

    def all(self) -> list[ShopProduct]:
        return list(self._products)

    def get(self, product_id: str) -> ShopProduct | None:
        return self._by_id.get(product_id)

    def filter(
        self,
        *,
        category: str | None = None,
        max_price: float | None = None,
        occasion: str | None = None,
        query: str | None = None,
    ) -> list[ShopProduct]:
        results = self._products
        if category:
            results = [p for p in results if p.category == category]
        if max_price is not None:
            results = [p for p in results if p.price <= max_price]
        if occasion:
            results = [p for p in results if occasion in p.occasions]
        if query:
            q = query.lower().strip()
            results = [
                p for p in results if q in p.name.lower() or q in p.subcategory.lower() or q in p.description.lower()
            ]
        return list(results)

    def annotate_ownership(self, wardrobe: list[WardrobeItem]) -> list[ShopProduct]:
        """Flag products the user already owns something similar to (never hides them)."""
        annotated = []
        for product in self._products:
            owned = any(
                w.category == product.category
                and is_similar(w.subcategory, w.name, product.subcategory, product.name)
                for w in wardrobe
            )
            annotated.append(product.model_copy(update={"owned_similar": owned}))
        return annotated


@lru_cache(maxsize=1)
def get_catalog() -> CatalogService:
    return CatalogService.load()
