import os
import tempfile
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

# Point the app at a throwaway database before it is imported.
_tmp = tempfile.mkdtemp()
os.environ["DATABASE_PATH"] = str(Path(_tmp) / "test.db")
os.environ["SEED_DEMO_DATA"] = "true"

from app.main import app  # noqa: E402


@pytest.fixture(scope="module")
def client():
    with TestClient(app) as c:
        yield c


def item(item_id: str = "test-1", name: str = "Test Top") -> dict:
    return {
        "id": item_id,
        "name": name,
        "category": "tops",
        "color": "Blue",
        "tags": ["casual"],
        "image": "",
        "createdAt": "2026-10-29T10:00:00.000Z",
    }


def look(look_id: str = "look-1") -> dict:
    return {
        "id": look_id,
        "title": "College Casual Look",
        "occasion": "college",
        "occasionLabel": "College",
        "modelImage": "/images/models/college.jpg",
        "preferences": {
            "occasion": "college",
            "style": "casual",
            "colors": ["Purple"],
            "budget": "500-1500",
            "traits": ["comfortable"],
            "notes": "",
        },
        "items": [
            {"slot": "outfit", "title": "Lavender Kurti", "subtitle": "From your wardrobe", "image": "", "source": "wardrobe"}
        ],
        "tips": ["Keep it simple."],
        "generatedAt": "2026-10-29T10:00:00.000Z",
        "favorite": False,
        "savedAt": "2026-10-29T10:05:00.000Z",
    }


def test_health(client):
    res = client.get("/health")
    assert res.status_code == 200
    assert res.json()["status"] == "ok"


def test_cors_allows_vite_origin(client):
    res = client.options(
        "/api/wardrobe",
        headers={"Origin": "http://localhost:5173", "Access-Control-Request-Method": "POST"},
    )
    assert res.status_code == 200
    assert res.headers["access-control-allow-origin"] == "http://localhost:5173"


def test_cors_blocks_unknown_origin(client):
    res = client.get("/health", headers={"Origin": "http://evil.example"})
    assert "access-control-allow-origin" not in res.headers


def test_wardrobe_is_seeded(client):
    res = client.get("/api/wardrobe")
    assert res.status_code == 200
    names = [i["name"] for i in res.json()]
    assert "Floral Dress" in names and "Hair Serum" in names
    assert len(names) == 18


def test_wardrobe_create_update_delete(client):
    created = client.post("/api/wardrobe", json=item())
    assert created.status_code == 201
    assert client.get("/api/wardrobe").json()[0]["id"] == "test-1"  # newest first

    updated = client.put("/api/wardrobe/test-1", json=item(name="Renamed"))
    assert updated.status_code == 200 and updated.json()["name"] == "Renamed"

    assert client.delete("/api/wardrobe/test-1").status_code == 204
    assert all(i["id"] != "test-1" for i in client.get("/api/wardrobe").json())


def test_wardrobe_rejects_invalid_category(client):
    bad = item("bad-1")
    bad["category"] = "hats"
    assert client.post("/api/wardrobe", json=bad).status_code == 422


def test_wardrobe_update_missing_returns_404(client):
    assert client.put("/api/wardrobe/nope", json=item("nope")).status_code == 404


def test_saved_looks_roundtrip(client):
    assert client.get("/api/saved-looks").json() == []
    assert client.post("/api/saved-looks", json=look()).status_code == 201

    listed = client.get("/api/saved-looks").json()
    assert len(listed) == 1 and listed[0]["occasionLabel"] == "College"

    fav = client.patch("/api/saved-looks/look-1", json={"favorite": True})
    assert fav.status_code == 200 and fav.json()["favorite"] is True
    assert client.get("/api/saved-looks").json()[0]["favorite"] is True

    assert client.delete("/api/saved-looks/look-1").status_code == 204
    assert client.get("/api/saved-looks").json() == []


def test_look_image_is_not_configured(client):
    res = client.post("/api/look-image", json={"look": look()})
    assert res.status_code == 200
    assert res.json()["status"] == "not_configured"
