from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, Query

from ..dependencies import get_catalog_service, get_wardrobe_repo
from ..repositories import WardrobeRepository
from ..schemas import ConcreteOccasion, ShopProduct, WardrobeCategory
from ..services.catalog import CatalogService

router = APIRouter(prefix="/api/catalog", tags=["catalog"])


@router.get("", response_model=list[ShopProduct])
def list_catalog(
    catalog: CatalogService = Depends(get_catalog_service),
    wardrobe: WardrobeRepository = Depends(get_wardrobe_repo),
    category: WardrobeCategory | None = None,
    max_price: Annotated[float | None, Query(alias="maxPrice", ge=0)] = None,
    occasion: ConcreteOccasion | None = None,
    q: Annotated[str | None, Query(max_length=60)] = None,
) -> list[ShopProduct]:
    """Browse the demo catalog. Prices are sample data. ``ownedSimilar`` flags products
    the stored wardrobe already has an equivalent of."""
    wanted = {p.id for p in catalog.filter(category=category, max_price=max_price, occasion=occasion, query=q)}
    return [p for p in catalog.annotate_ownership(wardrobe.list()) if p.id in wanted]
