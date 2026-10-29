from __future__ import annotations

import json
import sqlite3
from collections.abc import Iterator
from contextlib import contextmanager
from pathlib import Path

from .config import get_settings

DATA_DIR = Path(__file__).resolve().parent / "data"
SCHEMA_VERSION = 2

SCHEMA = """
CREATE TABLE IF NOT EXISTS wardrobe_items (
    id           TEXT PRIMARY KEY,
    name         TEXT NOT NULL,
    category     TEXT NOT NULL,
    subcategory  TEXT NOT NULL DEFAULT '',
    colors       TEXT NOT NULL DEFAULT '[]',
    styles       TEXT NOT NULL DEFAULT '[]',
    occasions    TEXT NOT NULL DEFAULT '[]',
    fabric       TEXT NOT NULL DEFAULT '',
    comfort      INTEGER NOT NULL DEFAULT 3,
    price        REAL,
    tags         TEXT NOT NULL DEFAULT '[]',
    brand        TEXT,
    notes        TEXT,
    image        TEXT NOT NULL DEFAULT '',
    created_at   TEXT NOT NULL,
    sort_order   INTEGER NOT NULL DEFAULT 0
);
CREATE INDEX IF NOT EXISTS idx_wardrobe_order ON wardrobe_items (sort_order);

CREATE TABLE IF NOT EXISTS saved_looks (
    id        TEXT PRIMARY KEY,
    payload   TEXT NOT NULL,
    favorite  INTEGER NOT NULL DEFAULT 0,
    saved_at  TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_saved_at ON saved_looks (saved_at);

CREATE TABLE IF NOT EXISTS outfits (
    id          TEXT PRIMARY KEY,
    request_id  TEXT NOT NULL,
    payload     TEXT NOT NULL,
    created_at  TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_outfits_request ON outfits (request_id);

CREATE TABLE IF NOT EXISTS generated_images (
    outfit_id                TEXT PRIMARY KEY,
    provider                 TEXT NOT NULL,
    model                    TEXT NOT NULL,
    file_name                TEXT NOT NULL,
    prompt                   TEXT NOT NULL,
    used_reference_images    INTEGER NOT NULL DEFAULT 0,
    created_at               TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS meta (
    key   TEXT PRIMARY KEY,
    value TEXT NOT NULL
);
"""


def _connect() -> sqlite3.Connection:
    path = get_settings().database_path
    path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(path, timeout=10)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    conn.execute("PRAGMA journal_mode = WAL")
    return conn


@contextmanager
def db() -> Iterator[sqlite3.Connection]:
    """Yield a connection that commits on success and rolls back on error."""
    conn = _connect()
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def load_demo_wardrobe() -> list[dict]:
    seed_file = DATA_DIR / "demo_wardrobe.json"
    return json.loads(seed_file.read_text(encoding="utf-8")) if seed_file.exists() else []


def wardrobe_row_params(item: dict, sort_order: int) -> tuple:
    return (
        item["id"],
        item["name"],
        item["category"],
        item.get("subcategory", ""),
        json.dumps(item.get("colors", [])),
        json.dumps(item.get("styles", [])),
        json.dumps(item.get("occasions", [])),
        item.get("fabric", ""),
        int(item.get("comfort", 3)),
        item.get("price"),
        json.dumps(item.get("tags", [])),
        item.get("brand"),
        item.get("notes"),
        item.get("image", ""),
        item["createdAt"],
        sort_order,
    )


INSERT_WARDROBE = """
INSERT OR REPLACE INTO wardrobe_items
(id, name, category, subcategory, colors, styles, occasions, fabric, comfort, price,
 tags, brand, notes, image, created_at, sort_order)
VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
"""


def _migrate_v1_wardrobe(conn: sqlite3.Connection) -> None:
    """Upgrade the prototype wardrobe table (single ``color``, ``beauty`` category).

    Rows that match a demo item id are replaced by the richer demo definition; other
    rows keep the user's data and gain sensible derived fields.
    """
    from .schemas import WardrobeItem  # local import avoids a cycle at module load

    demo = {d["id"]: d for d in load_demo_wardrobe()}
    old_rows = conn.execute("SELECT * FROM wardrobe_items ORDER BY sort_order, rowid").fetchall()
    conn.execute("ALTER TABLE wardrobe_items RENAME TO wardrobe_items_v1")
    conn.execute("DROP INDEX IF EXISTS idx_wardrobe_order")
    conn.executescript(SCHEMA)
    for index, row in enumerate(old_rows):
        if row["id"] in demo:
            payload = demo[row["id"]]
        else:
            tags = json.loads(row["tags"] or "[]")
            payload = {
                "id": row["id"],
                "name": row["name"],
                "category": row["category"],
                "color": row["color"],
                "tags": tags,
                "brand": row["brand"],
                "notes": row["notes"],
                "image": row["image"],
                "createdAt": row["created_at"],
            }
        item = WardrobeItem.model_validate(payload).model_dump(by_alias=True)
        if row["id"] not in demo:
            from .services.recommendation.normalize import enrich_legacy_item

            item = enrich_legacy_item(item)
        conn.execute(INSERT_WARDROBE, wardrobe_row_params(item, index))
    conn.execute("DROP TABLE wardrobe_items_v1")


def init_db() -> None:
    """Create tables, migrate older databases and, once, seed the sample wardrobe."""
    with db() as conn:
        has_wardrobe = conn.execute(
            "SELECT 1 FROM sqlite_master WHERE type='table' AND name='wardrobe_items'"
        ).fetchone()
        needs_v2 = False
        if has_wardrobe:
            columns = {r["name"] for r in conn.execute("PRAGMA table_info(wardrobe_items)")}
            needs_v2 = "colors" not in columns
        if needs_v2:
            _migrate_v1_wardrobe(conn)
            # Saved looks from the prototype used a different shape; they were sample
            # looks generated in the browser and cannot be upgraded faithfully.
            conn.execute("DELETE FROM saved_looks")
            conn.execute("DELETE FROM meta WHERE key = 'seeded_looks'")
        conn.executescript(SCHEMA)
        conn.execute(
            "INSERT OR REPLACE INTO meta (key, value) VALUES ('schema_version', ?)",
            (str(SCHEMA_VERSION),),
        )

        seeded = conn.execute("SELECT value FROM meta WHERE key = 'seeded'").fetchone()
        if seeded or not get_settings().seed_demo_data:
            return
        for index, item in enumerate(load_demo_wardrobe()):
            conn.execute(INSERT_WARDROBE, wardrobe_row_params(item, index))
        conn.execute("INSERT OR REPLACE INTO meta (key, value) VALUES ('seeded', '1')")
