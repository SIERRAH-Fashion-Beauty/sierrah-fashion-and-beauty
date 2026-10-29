"""Database persistence, restarts and the v1 -> v2 schema migration."""

import dataclasses
import json
import sqlite3

from fastapi.testclient import TestClient

from app import database
from app.config import get_settings
from app.main import app
from factories import item, recommendation_request

V1_SCHEMA = """
CREATE TABLE wardrobe_items (
    id TEXT PRIMARY KEY, name TEXT NOT NULL, category TEXT NOT NULL, color TEXT NOT NULL DEFAULT '',
    tags TEXT NOT NULL DEFAULT '[]', brand TEXT, notes TEXT, image TEXT NOT NULL DEFAULT '',
    created_at TEXT NOT NULL, sort_order INTEGER NOT NULL DEFAULT 0
);
CREATE TABLE saved_looks (id TEXT PRIMARY KEY, payload TEXT NOT NULL, favorite INTEGER NOT NULL DEFAULT 0, saved_at TEXT NOT NULL);
CREATE TABLE meta (key TEXT PRIMARY KEY, value TEXT NOT NULL);
"""


def test_data_survives_an_application_restart(client):
    client.post("/api/wardrobe", json=item("persist-1", "Persistent Kurti", "kurtis", subcategory="kurti", colors=["Teal"]))
    outfit = client.post("/api/recommendations", json=recommendation_request(occasion="office")).json()["outfits"][0]
    client.post("/api/saved-looks", json={**outfit, "favorite": True, "savedAt": "2026-10-29T12:00:00.000Z"})
    client.delete("/api/wardrobe/demo-lavender-kurti")

    with TestClient(app) as restarted:  # runs the startup lifespan again on the same database file
        names = {i["name"] for i in restarted.get("/api/wardrobe").json()}
        assert "Persistent Kurti" in names
        assert "Lavender Kurti" not in names, "deleted demo items must not come back after a restart"
        looks = {s["id"]: s for s in restarted.get("/api/saved-looks").json()}
        assert looks[outfit["id"]]["favorite"] is True and looks[outfit["id"]]["title"] == outfit["title"]
        assert {"seed-college", "seed-office", "seed-wedding", "seed-party"} <= set(looks)
        assert len([s for s in restarted.get("/api/saved-looks").json() if s["id"] == "seed-college"]) == 1


def test_deleted_sample_looks_stay_deleted_after_restart(client):
    client.delete("/api/saved-looks/seed-party")
    with TestClient(app) as restarted:
        assert all(s["id"] != "seed-party" for s in restarted.get("/api/saved-looks").json())


def test_init_db_is_idempotent(client):
    before = client.get("/api/wardrobe").json()
    database.init_db()
    database.init_db()
    assert client.get("/api/wardrobe").json() == before


def test_stored_data_is_visible_in_sqlite_directly(client):
    client.post("/api/wardrobe", json=item("raw-1", "Raw Check", colors=["Teal", "Gold"], occasions=["college"], price=799))
    path = get_settings().database_path
    row = sqlite3.connect(path).execute("SELECT name, colors, occasions, price FROM wardrobe_items WHERE id='raw-1'").fetchone()
    assert row == ("Raw Check", '["Teal", "Gold"]', '["college"]', 799.0)


def test_v1_database_is_migrated_without_losing_user_items(tmp_path, monkeypatch):
    old = tmp_path / "old.db"
    conn = sqlite3.connect(old)
    conn.executescript(V1_SCHEMA)
    rows = [
        ("demo-lavender-kurti", "Lavender Kurti", "tops", "Purple", "[]", "", "2026-01-01T00:00:00Z", 1),
        ("user-1", "My Silk Saree", "tops", "Red", '["saree","festive"]', "", "2026-01-02T00:00:00Z", 2),
        ("user-2", "Matte Lipstick", "beauty", "Red", '["lipstick"]', "data:image/jpeg;base64,AAAA", "2026-01-03T00:00:00Z", 3),
        ("user-3", "Face Serum", "beauty", "", '["serum","skincare"]', "", "2026-01-04T00:00:00Z", 4),
    ]
    conn.executemany("INSERT INTO wardrobe_items (id,name,category,color,tags,image,created_at,sort_order) VALUES (?,?,?,?,?,?,?,?)", rows)
    conn.execute("INSERT INTO saved_looks VALUES ('old-look', ?, 0, '2026-01-01')", (json.dumps({"id": "old-look"}),))
    conn.execute("INSERT INTO meta VALUES ('seeded', '1')")
    conn.commit()
    conn.close()

    settings = dataclasses.replace(get_settings(), database_path=old)
    monkeypatch.setattr(database, "get_settings", lambda: settings)
    database.init_db()

    with database.db() as c:
        items = {r["id"]: dict(r) for r in c.execute("SELECT * FROM wardrobe_items")}
        tables = {r[0] for r in c.execute("SELECT name FROM sqlite_master WHERE type='table'")}
        looks = c.execute("SELECT COUNT(*) FROM saved_looks WHERE id='old-look'").fetchone()[0]
    assert "wardrobe_items_v1" not in tables and {"outfits", "generated_images"} <= tables
    lavender = items["demo-lavender-kurti"]  # replaced by the richer demo definition
    assert lavender["category"] == "kurtis" and lavender["fabric"] == "Cotton" and lavender["comfort"] == 5
    assert "college" in json.loads(lavender["occasions"])
    assert items["user-1"]["name"] == "My Silk Saree" and json.loads(items["user-1"]["colors"]) == ["Red"]
    assert items["user-2"]["category"] == "makeup" and items["user-2"]["image"].startswith("data:image/jpeg")
    assert items["user-3"]["category"] == "skincare"
    assert items["user-1"]["comfort"] in range(1, 6)
    assert looks == 0, "v1 saved looks have an incompatible shape and are cleared by the migration"
    database.init_db()  # second run is a no-op
    with database.db() as c:
        assert c.execute("SELECT COUNT(*) FROM wardrobe_items WHERE id='user-1'").fetchone()[0] == 1
