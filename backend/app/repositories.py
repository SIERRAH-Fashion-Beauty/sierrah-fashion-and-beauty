"""Persistence layer: one small repository class per aggregate."""

from __future__ import annotations

import json
import sqlite3

from .database import INSERT_WARDROBE, db, wardrobe_row_params
from .schemas import GeneratedImage, Outfit, SavedLook, WardrobeItem
from .utils import now_iso


# ---------------------------------------------------------------- Wardrobe
class WardrobeRepository:
    @staticmethod
    def _to_item(row: sqlite3.Row) -> WardrobeItem:
        return WardrobeItem(
            id=row["id"],
            name=row["name"],
            category=row["category"],
            subcategory=row["subcategory"],
            colors=json.loads(row["colors"]),
            styles=json.loads(row["styles"]),
            occasions=json.loads(row["occasions"]),
            fabric=row["fabric"],
            comfort=row["comfort"],
            price=row["price"],
            tags=json.loads(row["tags"]),
            brand=row["brand"],
            notes=row["notes"],
            image=row["image"],
            created_at=row["created_at"],
        )

    def list(self) -> list[WardrobeItem]:
        with db() as conn:
            rows = conn.execute(
                "SELECT * FROM wardrobe_items ORDER BY sort_order ASC, rowid ASC"
            ).fetchall()
        return [self._to_item(r) for r in rows]

    def get(self, item_id: str) -> WardrobeItem | None:
        with db() as conn:
            row = conn.execute("SELECT * FROM wardrobe_items WHERE id = ?", (item_id,)).fetchone()
        return self._to_item(row) if row else None

    def exists(self, item_id: str) -> bool:
        return self.get(item_id) is not None

    def upsert(self, item: WardrobeItem, *, front: bool = False) -> WardrobeItem:
        """Insert or update. ``front`` places a brand-new item first in the list."""
        payload = item.model_dump(by_alias=True)
        with db() as conn:
            existing = conn.execute(
                "SELECT sort_order FROM wardrobe_items WHERE id = ?", (item.id,)
            ).fetchone()
            if existing:
                order = existing["sort_order"]
            elif front:
                lowest = conn.execute("SELECT MIN(sort_order) FROM wardrobe_items").fetchone()[0]
                order = (lowest if lowest is not None else 0) - 1
            else:
                highest = conn.execute("SELECT MAX(sort_order) FROM wardrobe_items").fetchone()[0]
                order = (highest if highest is not None else -1) + 1
            conn.execute(INSERT_WARDROBE, wardrobe_row_params(payload, order))
        saved = self.get(item.id)
        assert saved is not None
        return saved

    def delete(self, item_id: str) -> bool:
        with db() as conn:
            cur = conn.execute("DELETE FROM wardrobe_items WHERE id = ?", (item_id,))
        return cur.rowcount > 0

    def replace_all(self, items: list[WardrobeItem]) -> list[WardrobeItem]:
        with db() as conn:
            conn.execute("DELETE FROM wardrobe_items")
            for index, item in enumerate(items):
                conn.execute(INSERT_WARDROBE, wardrobe_row_params(item.model_dump(by_alias=True), index))
        return self.list()


# ------------------------------------------------------------------ Outfits
class OutfitRepository:
    """Every recommended outfit is stored so images can be generated for it later."""

    def save_many(self, outfits: list[Outfit]) -> None:
        with db() as conn:
            for outfit in outfits:
                conn.execute(
                    "INSERT OR REPLACE INTO outfits (id, request_id, payload, created_at) VALUES (?, ?, ?, ?)",
                    (outfit.id, outfit.request_id, outfit.model_dump_json(by_alias=True), now_iso()),
                )

    def attach_image(self, outfit_id: str, image: GeneratedImage | None) -> None:
        outfit = self.get(outfit_id)
        if outfit is None:
            return
        outfit.image = image
        self.save_many([outfit])

    def get(self, outfit_id: str) -> Outfit | None:
        with db() as conn:
            row = conn.execute("SELECT payload FROM outfits WHERE id = ?", (outfit_id,)).fetchone()
            if row:
                return Outfit.model_validate_json(row["payload"])
            saved = conn.execute("SELECT payload FROM saved_looks WHERE id = ?", (outfit_id,)).fetchone()
        return Outfit.model_validate_json(saved["payload"]) if saved else None


# -------------------------------------------------------------- Saved looks
class SavedLookRepository:
    @staticmethod
    def _to_look(row: sqlite3.Row) -> SavedLook:
        look = SavedLook.model_validate_json(row["payload"])
        look.favorite = bool(row["favorite"])
        return look

    def list(self) -> list[SavedLook]:
        with db() as conn:
            rows = conn.execute("SELECT * FROM saved_looks ORDER BY saved_at DESC, rowid DESC").fetchall()
        return [self._to_look(r) for r in rows]

    def get(self, look_id: str) -> SavedLook | None:
        with db() as conn:
            row = conn.execute("SELECT * FROM saved_looks WHERE id = ?", (look_id,)).fetchone()
        return self._to_look(row) if row else None

    def upsert(self, look: SavedLook) -> SavedLook:
        with db() as conn:
            conn.execute(
                """INSERT INTO saved_looks (id, payload, favorite, saved_at) VALUES (?, ?, ?, ?)
                   ON CONFLICT(id) DO UPDATE SET payload = excluded.payload,
                       favorite = excluded.favorite, saved_at = excluded.saved_at""",
                (look.id, look.model_dump_json(by_alias=True), int(look.favorite), look.saved_at),
            )
        saved = self.get(look.id)
        assert saved is not None
        return saved

    def set_favorite(self, look_id: str, favorite: bool) -> SavedLook | None:
        look = self.get(look_id)
        if look is None:
            return None
        look.favorite = favorite
        return self.upsert(look)

    def delete(self, look_id: str) -> bool:
        with db() as conn:
            cur = conn.execute("DELETE FROM saved_looks WHERE id = ?", (look_id,))
        return cur.rowcount > 0

    def replace_all(self, looks: list[SavedLook]) -> list[SavedLook]:
        with db() as conn:
            conn.execute("DELETE FROM saved_looks")
            for look in looks:
                conn.execute(
                    "INSERT INTO saved_looks (id, payload, favorite, saved_at) VALUES (?, ?, ?, ?)",
                    (look.id, look.model_dump_json(by_alias=True), int(look.favorite), look.saved_at),
                )
        return self.list()

    def attach_image(self, look_id: str, image: GeneratedImage | None) -> None:
        """Keep a saved look in step when its image is (re)generated after saving."""
        look = self.get(look_id)
        if look is None:
            return
        look.image = image
        self.upsert(look)


# ------------------------------------------------------------ Image records
class ImageRepository:
    def get(self, outfit_id: str) -> tuple[GeneratedImage, str] | None:
        """Return the stored image info and file name for an outfit, if any."""
        with db() as conn:
            row = conn.execute("SELECT * FROM generated_images WHERE outfit_id = ?", (outfit_id,)).fetchone()
        if not row:
            return None
        image = GeneratedImage(
            url=f"/media/generated/{row['file_name']}",
            provider=row["provider"],
            model=row["model"],
            generated_at=row["created_at"],
            used_reference_images=bool(row["used_reference_images"]),
        )
        return image, row["file_name"]

    def save(
        self,
        outfit_id: str,
        *,
        provider: str,
        model: str,
        file_name: str,
        prompt: str,
        used_reference_images: bool,
    ) -> GeneratedImage:
        with db() as conn:
            conn.execute(
                """INSERT OR REPLACE INTO generated_images
                   (outfit_id, provider, model, file_name, prompt, used_reference_images, created_at)
                   VALUES (?, ?, ?, ?, ?, ?, ?)""",
                (outfit_id, provider, model, file_name, prompt, int(used_reference_images), now_iso()),
            )
        found = self.get(outfit_id)
        assert found is not None
        return found[0]
