from __future__ import annotations

import json
import sqlite3
from collections.abc import Iterator
from contextlib import contextmanager
from pathlib import Path

from .config import get_settings

DATA_DIR = Path(__file__).resolve().parent / "data"

SCHEMA = """
CREATE TABLE IF NOT EXISTS wardrobe_items (
    id          TEXT PRIMARY KEY,
    name        TEXT NOT NULL,
    category    TEXT NOT NULL,
    color       TEXT NOT NULL DEFAULT '',
    tags        TEXT NOT NULL DEFAULT '[]',
    brand       TEXT,
    notes       TEXT,
    image       TEXT NOT NULL DEFAULT '',
    created_at  TEXT NOT NULL,
    sort_order  INTEGER NOT NULL DEFAULT 0
);
CREATE INDEX IF NOT EXISTS idx_wardrobe_order ON wardrobe_items (sort_order);

CREATE TABLE IF NOT EXISTS saved_looks (
    id        TEXT PRIMARY KEY,
    payload   TEXT NOT NULL,
    favorite  INTEGER NOT NULL DEFAULT 0,
    saved_at  TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_saved_at ON saved_looks (saved_at);

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


def init_db() -> None:
    """Create tables and, once, seed the sample wardrobe."""
    with db() as conn:
        conn.executescript(SCHEMA)
        seeded = conn.execute("SELECT value FROM meta WHERE key = 'seeded'").fetchone()
        if seeded or not get_settings().seed_demo_data:
            return
        seed_file = DATA_DIR / "demo_wardrobe.json"
        if seed_file.exists():
            items = json.loads(seed_file.read_text(encoding="utf-8"))
            for index, item in enumerate(items):
                conn.execute(
                    """INSERT OR IGNORE INTO wardrobe_items
                       (id, name, category, color, tags, brand, notes, image, created_at, sort_order)
                       VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                    (
                        item["id"],
                        item["name"],
                        item["category"],
                        item.get("color", ""),
                        json.dumps(item.get("tags", [])),
                        item.get("brand"),
                        item.get("notes"),
                        item.get("image", ""),
                        item["createdAt"],
                        index,
                    ),
                )
        conn.execute("INSERT OR REPLACE INTO meta (key, value) VALUES ('seeded', '1')")
