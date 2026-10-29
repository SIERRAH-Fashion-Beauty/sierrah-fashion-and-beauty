from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Response, status

from ..dependencies import get_image_repo, get_outfit_repo, get_saved_repo, get_wardrobe_repo
from ..repositories import ImageRepository, OutfitRepository, SavedLookRepository, WardrobeRepository
from ..schemas import FavoritePatch, SavedLook, SavedLookSync

router = APIRouter(prefix="/api/saved-looks", tags=["saved-looks"])


def _prepare(
    look: SavedLook, wardrobe: WardrobeRepository, images: ImageRepository
) -> SavedLook:
    """Make a saved look self-contained so it reopens exactly as it was recommended.

    * Wardrobe piece photos that were left out of the recommendation (uploaded photos)
      are copied in from the wardrobe.
    * A generated model image that exists on the server is attached.
    """
    for item in look.items:
        for piece in item.pieces:
            if not piece.image and piece.source == "wardrobe" and piece.wardrobe_item_id:
                stored = wardrobe.get(piece.wardrobe_item_id)
                if stored and stored.image:
                    piece.image = stored.image
        if not item.image:
            item.image = next((p.image for p in item.pieces if p.image), "")
    if look.image is None:
        existing = images.get(look.id)
        if existing:
            look.image = existing[0]
    return look


@router.get("", response_model=list[SavedLook])
def list_saved_looks(repo: SavedLookRepository = Depends(get_saved_repo)) -> list[SavedLook]:
    return repo.list()


@router.post("", response_model=SavedLook, status_code=status.HTTP_201_CREATED)
def create_saved_look(
    look: SavedLook,
    repo: SavedLookRepository = Depends(get_saved_repo),
    outfits: OutfitRepository = Depends(get_outfit_repo),
    wardrobe: WardrobeRepository = Depends(get_wardrobe_repo),
    images: ImageRepository = Depends(get_image_repo),
) -> SavedLook:
    """Save a recommended outfit. Saving the same look twice just updates it."""
    prepared = _prepare(look, wardrobe, images)
    saved = repo.upsert(prepared)
    outfits.save_many([prepared])
    return saved


@router.put("/sync", response_model=list[SavedLook])
def replace_saved_looks(
    payload: SavedLookSync, repo: SavedLookRepository = Depends(get_saved_repo)
) -> list[SavedLook]:
    return repo.replace_all(payload.looks)


@router.patch("/{look_id}", response_model=SavedLook)
def set_favorite(
    look_id: str, patch: FavoritePatch, repo: SavedLookRepository = Depends(get_saved_repo)
) -> SavedLook:
    look = repo.set_favorite(look_id, patch.favorite)
    if look is None:
        raise HTTPException(status_code=404, detail="Saved look not found.")
    return look


@router.delete("/{look_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_saved_look(look_id: str, repo: SavedLookRepository = Depends(get_saved_repo)) -> Response:
    """Idempotent: deleting a look that is already gone still returns 204."""
    repo.delete(look_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
