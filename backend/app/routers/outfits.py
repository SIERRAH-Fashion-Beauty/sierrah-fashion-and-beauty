from __future__ import annotations

from fastapi import APIRouter, Body, Depends, HTTPException

from ..dependencies import get_image_service, get_outfit_repo
from ..repositories import OutfitRepository
from ..schemas import GenerateImageRequest, GenerateImageResponse, Outfit
from ..services.image_generation import ImageGenerationService

router = APIRouter(prefix="/api/outfits", tags=["outfits"])


@router.get("/{outfit_id}", response_model=Outfit)
def get_outfit(outfit_id: str, repo: OutfitRepository = Depends(get_outfit_repo)) -> Outfit:
    outfit = repo.get(outfit_id)
    if outfit is None:
        raise HTTPException(status_code=404, detail="Outfit not found.")
    return outfit


@router.post("/{outfit_id}/generate-image", response_model=GenerateImageResponse)
def generate_outfit_image(
    outfit_id: str,
    body: GenerateImageRequest | None = Body(default=None),
    service: ImageGenerationService = Depends(get_image_service),
) -> GenerateImageResponse:
    """Create (or return the already generated) AI model preview for an outfit.

    * Returns ``status: "not_configured"`` with setup instructions when no provider key is set.
    * Returns the stored image (``cached: true``) when one exists, unless ``regenerate`` is set,
      so reopening a look never triggers a second paid generation.
    * Provider problems are reported as ``{"detail": {code, message, retryable}}``.
    """
    return service.generate(outfit_id, body or GenerateImageRequest())
