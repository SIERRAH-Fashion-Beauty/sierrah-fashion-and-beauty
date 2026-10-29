from __future__ import annotations

from fastapi import APIRouter, Depends

from ..dependencies import get_engine, get_outfit_repo, get_wardrobe_repo
from ..repositories import OutfitRepository, WardrobeRepository
from ..schemas import RecommendationRequest, RecommendationResponse
from ..services.recommendation import RecommendationEngine

router = APIRouter(prefix="/api", tags=["recommendations"])


@router.post("/recommendations", response_model=RecommendationResponse)
def create_recommendations(
    request: RecommendationRequest,
    engine: RecommendationEngine = Depends(get_engine),
    wardrobe_repo: WardrobeRepository = Depends(get_wardrobe_repo),
    outfit_repo: OutfitRepository = Depends(get_outfit_repo),
) -> RecommendationResponse:
    """Style outfits for an occasion from the user's wardrobe.

    The wardrobe in the request body is used as-is (it may contain edits not yet saved).
    If it is omitted, the wardrobe stored in the database is used instead.
    """
    if request.wardrobe is not None:
        wardrobe, source = request.wardrobe, "request"
    else:
        wardrobe, source = wardrobe_repo.list(), "database"
    response = engine.recommend(request, wardrobe, source)
    outfit_repo.save_many(response.outfits)
    return response
