from __future__ import annotations

import json
import sqlite3

from fastapi import APIRouter, HTTPException, Response, status

from ..database import db
from ..schemas import WardrobeItem, WardrobeSync

router = APIRouter(prefix="/api/wardrobe", tags=["wardrobe"])


def _row_to_item(row: sqlite3.Row) -> WardrobeItem:
    return WardrobeItem(
        id=row["id"],
        name=row["name"],
        category=row["category"],
        color=row["color"],
        tags=json.loads(row["tags"] or "[]"),
        brand=row["brand"],
        notes=row["notes"],
        image=row["image"],
        created_at=row["created_at"],
    )


def _params(item: WardrobeItem) -> tuple:
    return (
        item.id,
        item.name,
        item.category,
        item.color,
        json.dumps(item.tags),
        item.brand,
        item.notes,
        item.image,
        item.created_at,
    )


_UPSERT = """
INSERT INTO wardrobe_items (id, name, category, color, tags, brand, notes, image, created_at, sort_order)
VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
ON CONFLICT(id) DO UPDATE SET
    name = excluded.name, category = excluded.category, color = excluded.color,
    tags = excluded.tags, brand = excluded.brand, notes = excluded.notes,
    image = excluded.image
"""


@router.get("", response_model=list[WardrobeItem])
def list_wardrobe() -> list[WardrobeItem]:
    with db() as conn:
        rows = conn.execute(
            "SELECT * FROM wardrobe_items ORDER BY sort_order ASC, rowid ASC"
        ).fetchall()
    return [_row_to_item(r) for r in rows]


@router.post("", response_model=WardrobeItem, status_code=status.HTTP_201_CREATED)
def create_wardrobe_item(item: WardrobeItem) -> WardrobeItem:
    """Create an item. Posting an existing id updates it, so retries are safe."""
    with db() as conn:
        # New items appear first, matching the frontend's ordering.
        lowest = conn.execute("SELECT MIN(sort_order) FROM wardrobe_items").fetchone()[0]
        order = (lowest if lowest is not None else 0) - 1
        conn.execute(_UPSERT, (*_params(item), order))
        row = conn.execute("SELECT * FROM wardrobe_items WHERE id = ?", (item.id,)).fetchone()
    return _row_to_item(row)


@router.put("/sync", response_model=list[WardrobeItem])
def replace_wardrobe(payload: WardrobeSync) -> list[WardrobeItem]:
    """Replace the whole wardrobe with the client's copy (used by 'Save Wardrobe')."""
    with db() as conn:
        conn.execute("DELETE FROM wardrobe_items")
        for index, item in enumerate(payload.items):
            conn.execute(_UPSERT, (*_params(item), index))
        rows = conn.execute(
            "SELECT * FROM wardrobe_items ORDER BY sort_order ASC, rowid ASC"
        ).fetchall()
    return [_row_to_item(r) for r in rows]


@router.put("/{item_id}", response_model=WardrobeItem)
def update_wardrobe_item(item_id: str, item: WardrobeItem) -> WardrobeItem:
    if item.id != item_id:
        raise HTTPException(status_code=400, detail="Item id in the URL and body must match.")
    with db() as conn:
        exists = conn.execute("SELECT 1 FROM wardrobe_items WHERE id = ?", (item_id,)).fetchone()
        if not exists:
            raise HTTPException(status_code=404, detail="Wardrobe item not found.")
        conn.execute(_UPSERT, (*_params(item), 0))
        row = conn.execute("SELECT * FROM wardrobe_items WHERE id = ?", (item_id,)).fetchone()
    return _row_to_item(row)


@router.delete("/{item_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_wardrobe_item(item_id: str) -> Response:
    with db() as conn:
        conn.execute("DELETE FROM wardrobe_items WHERE id = ?", (item_id,))
    return Response(status_code=status.HTTP_204_NO_CONTENT)
