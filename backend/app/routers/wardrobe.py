from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Response, status

from ..dependencies import get_wardrobe_repo
from ..repositories import WardrobeRepository
from ..schemas import WardrobeItem, WardrobeSync

router = APIRouter(prefix="/api/wardrobe", tags=["wardrobe"])


@router.get("", response_model=list[WardrobeItem])
def list_wardrobe(repo: WardrobeRepository = Depends(get_wardrobe_repo)) -> list[WardrobeItem]:
    return repo.list()


@router.post("", response_model=WardrobeItem, status_code=status.HTTP_201_CREATED)
def create_wardrobe_item(
    item: WardrobeItem, repo: WardrobeRepository = Depends(get_wardrobe_repo)
) -> WardrobeItem:
    """Create an item. Posting an existing id updates it, so retries are safe."""
    return repo.upsert(item, front=True)


@router.put("/sync", response_model=list[WardrobeItem])
def replace_wardrobe(
    payload: WardrobeSync, repo: WardrobeRepository = Depends(get_wardrobe_repo)
) -> list[WardrobeItem]:
    """Replace the whole wardrobe with the client's copy (used by 'Save Wardrobe')."""
    return repo.replace_all(payload.items)


@router.put("/{item_id}", response_model=WardrobeItem)
def update_wardrobe_item(
    item_id: str, item: WardrobeItem, repo: WardrobeRepository = Depends(get_wardrobe_repo)
) -> WardrobeItem:
    if item.id != item_id:
        raise HTTPException(status_code=400, detail="Item id in the URL and body must match.")
    if not repo.exists(item_id):
        raise HTTPException(status_code=404, detail="Wardrobe item not found.")
    return repo.upsert(item)


@router.delete("/{item_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_wardrobe_item(item_id: str, repo: WardrobeRepository = Depends(get_wardrobe_repo)) -> Response:
    """Idempotent: deleting an item that is already gone still returns 204."""
    repo.delete(item_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
