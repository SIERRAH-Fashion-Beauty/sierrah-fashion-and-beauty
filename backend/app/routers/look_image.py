from __future__ import annotations

from fastapi import APIRouter

from ..config import get_settings
from ..schemas import LookImageRequest, LookImageResponse
from ..services.image_generation import generate_look_image

router = APIRouter(prefix="/api", tags=["image-generation"])


@router.post("/look-image", response_model=LookImageResponse)
def create_look_image(payload: LookImageRequest) -> LookImageResponse:
    """Request an AI model preview for a look (stub until a provider is configured)."""
    return generate_look_image(payload.look, get_settings())
