"""Dependency providers (FastAPI ``Depends``). Tests override these to inject fakes."""

from __future__ import annotations

from functools import lru_cache

from .config import get_settings
from .repositories import ImageRepository, OutfitRepository, SavedLookRepository, WardrobeRepository
from .services.catalog import CatalogService, get_catalog
from .services.image_generation import ImageGenerationService
from .services.image_generation.storage import MediaStore
from .services.recommendation import RecommendationEngine


def get_wardrobe_repo() -> WardrobeRepository:
    return WardrobeRepository()


def get_saved_repo() -> SavedLookRepository:
    return SavedLookRepository()


def get_outfit_repo() -> OutfitRepository:
    return OutfitRepository()


def get_image_repo() -> ImageRepository:
    return ImageRepository()


def get_catalog_service() -> CatalogService:
    return get_catalog()


def get_engine() -> RecommendationEngine:
    return RecommendationEngine(get_catalog())


@lru_cache(maxsize=1)
def _image_service() -> ImageGenerationService:
    settings = get_settings()
    return ImageGenerationService(
        settings,
        outfits=OutfitRepository(),
        images=ImageRepository(),
        saved=SavedLookRepository(),
        wardrobe=WardrobeRepository(),
        store=MediaStore(settings.media_dir),
    )


def get_image_service() -> ImageGenerationService:
    return _image_service()
