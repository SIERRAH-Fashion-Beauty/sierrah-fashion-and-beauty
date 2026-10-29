from __future__ import annotations

import sqlite3

from fastapi import APIRouter, HTTPException, Response, status

from ..database import db
from ..schemas import FavoritePatch, SavedLook, SavedLookSync

router = APIRouter(prefix="/api/saved-looks", tags=["saved-looks"])


def _row_to_look(row: sqlite3.Row) -> SavedLook:
    look = SavedLook.model_validate_json(row["payload"])
    # `favorite` lives in its own column so it can be toggled cheaply.
    return look.model_copy(update={"favorite": bool(row["favorite"])})


def _upsert(conn: sqlite3.Connection, look: SavedLook) -> None:
    conn.execute(
        """INSERT INTO saved_looks (id, payload, favorite, saved_at) VALUES (?, ?, ?, ?)
           ON CONFLICT(id) DO UPDATE SET payload = excluded.payload,
               favorite = excluded.favorite, saved_at = excluded.saved_at""",
        (look.id, look.model_dump_json(by_alias=True), int(look.favorite), look.saved_at),
    )


@router.get("", response_model=list[SavedLook])
def list_saved_looks() -> list[SavedLook]:
    with db() as conn:
        rows = conn.execute("SELECT * FROM saved_looks ORDER BY saved_at DESC, rowid DESC").fetchall()
    return [_row_to_look(r) for r in rows]


@router.post("", response_model=SavedLook, status_code=status.HTTP_201_CREATED)
def create_saved_look(look: SavedLook) -> SavedLook:
    """Save a look. Posting an existing id updates it, so retries are safe."""
    with db() as conn:
        _upsert(conn, look)
        row = conn.execute("SELECT * FROM saved_looks WHERE id = ?", (look.id,)).fetchone()
    return _row_to_look(row)


@router.put("/sync", response_model=list[SavedLook])
def replace_saved_looks(payload: SavedLookSync) -> list[SavedLook]:
    """Replace every saved look with the client's copy."""
    with db() as conn:
        conn.execute("DELETE FROM saved_looks")
        for look in payload.looks:
            _upsert(conn, look)
        rows = conn.execute("SELECT * FROM saved_looks ORDER BY saved_at DESC, rowid DESC").fetchall()
    return [_row_to_look(r) for r in rows]


@router.patch("/{look_id}", response_model=SavedLook)
def set_favorite(look_id: str, patch: FavoritePatch) -> SavedLook:
    with db() as conn:
        cur = conn.execute(
            "UPDATE saved_looks SET favorite = ? WHERE id = ?", (int(patch.favorite), look_id)
        )
        if cur.rowcount == 0:
            raise HTTPException(status_code=404, detail="Saved look not found.")
        row = conn.execute("SELECT * FROM saved_looks WHERE id = ?", (look_id,)).fetchone()
    return _row_to_look(row)


@router.delete("/{look_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_saved_look(look_id: str) -> Response:
    with db() as conn:
        conn.execute("DELETE FROM saved_looks WHERE id = ?", (look_id,))
    return Response(status_code=status.HTTP_204_NO_CONTENT)
