"""REST contract tests: health, CORS, wardrobe CRUD, saved looks, catalog, validation."""

from factories import item, recommendation_request


def test_health_reports_status_and_image_setup(client):
    res = client.get("/health")
    assert res.status_code == 200
    body = res.json()
    assert body["status"] == "ok" and body["service"] == "sierrah-api"
    assert body["imageGeneration"]["configured"] is False
    assert "IMAGE_API_KEY" in body["imageGeneration"]["message"]
    assert "apiKey" not in str(body)


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


# ----------------------------------------------------------------- wardrobe
def test_wardrobe_is_seeded_with_rich_items(client):
    res = client.get("/api/wardrobe")
    assert res.status_code == 200
    items = {i["name"]: i for i in res.json()}
    assert len(items) == 18
    kurti = items["Lavender Kurti"]
    assert kurti["category"] == "kurtis" and kurti["colors"] == ["Purple"]
    assert "college" in kurti["occasions"] and kurti["fabric"] == "Cotton" and kurti["comfort"] == 5
    assert items["Lipstick"]["category"] == "makeup"
    assert items["Hair Serum"]["category"] == "skincare"


def test_wardrobe_create_update_delete_with_all_fields(client):
    payload = item(
        "test-1", "Silk Saree", "sarees", subcategory="saree", colors=["Red", "Gold"],
        styles=["traditional", "elegant"], occasions=["wedding"], fabric="Silk", comfort=3, price=2500,
        tags=["festive"], image="/images/items/blue-kurti.jpg",
    )
    created = client.post("/api/wardrobe", json=payload)
    assert created.status_code == 201
    body = created.json()
    assert body["colors"] == ["Red", "Gold"] and body["price"] == 2500 and body["fabric"] == "Silk"
    assert client.get("/api/wardrobe").json()[0]["id"] == "test-1"  # newest first

    payload["name"] = "Renamed Saree"
    payload["comfort"] = 2
    updated = client.put("/api/wardrobe/test-1", json=payload)
    assert updated.status_code == 200 and updated.json()["name"] == "Renamed Saree"
    assert client.get("/api/wardrobe").json()[0]["comfort"] == 2

    assert client.delete("/api/wardrobe/test-1").status_code == 204
    assert all(i["id"] != "test-1" for i in client.get("/api/wardrobe").json())
    assert client.delete("/api/wardrobe/test-1").status_code == 204  # idempotent


def test_wardrobe_supports_all_ten_categories(client):
    categories = ["tops", "bottoms", "dresses", "kurtis", "sarees", "footwear", "bags", "jewellery", "makeup", "skincare"]
    for index, category in enumerate(categories):
        res = client.post("/api/wardrobe", json=item(f"cat-{index}", f"Item {category}", category))
        assert res.status_code == 201, category
    stored = {i["category"] for i in client.get("/api/wardrobe").json() if i["id"].startswith("cat-")}
    assert stored == set(categories)


def test_wardrobe_accepts_uploaded_image_data_url(client):
    data_url = "data:image/jpeg;base64,/9j/4AAQSkZJRgABAQ=="
    res = client.post("/api/wardrobe", json=item("up-1", "Uploaded", image=data_url))
    assert res.status_code == 201 and res.json()["image"] == data_url


def test_wardrobe_accepts_legacy_payload_shape(client):
    legacy = {"id": "old-1", "name": "Old Lipstick", "category": "beauty", "color": "Red",
              "tags": ["lipstick"], "image": "", "createdAt": "2026-10-29T10:00:00.000Z"}
    res = client.post("/api/wardrobe", json=legacy)
    assert res.status_code == 201
    assert res.json()["category"] == "makeup" and res.json()["colors"] == ["Red"]


def test_wardrobe_validation_errors(client):
    assert client.post("/api/wardrobe", json=item("bad-1", category="hats")).status_code == 422
    assert client.post("/api/wardrobe", json={**item("bad-2"), "name": ""}).status_code == 422
    assert client.post("/api/wardrobe", json={**item("bad-3"), "comfort": 9}).status_code == 422
    assert client.post("/api/wardrobe", json={**item("bad-4"), "price": -5}).status_code == 422
    assert client.post("/api/wardrobe", json={**item("bad-5"), "occasions": ["moon-landing"]}).status_code == 422
    assert client.post("/api/wardrobe", content=b"not json", headers={"Content-Type": "application/json"}).status_code == 422


def test_wardrobe_update_errors(client):
    assert client.put("/api/wardrobe/nope", json=item("nope")).status_code == 404
    assert client.put("/api/wardrobe/a", json=item("b")).status_code == 400


def test_wardrobe_sync_replaces_everything(client):
    res = client.put("/api/wardrobe/sync", json={"items": [item("only-1"), item("only-2")]})
    assert res.status_code == 200 and {i["id"] for i in res.json()} == {"only-1", "only-2"}
    assert len(client.get("/api/wardrobe").json()) == 2


# -------------------------------------------------------------- saved looks
def _outfit(client, **overrides) -> dict:
    res = client.post("/api/recommendations", json=recommendation_request(**overrides))
    assert res.status_code == 200
    return res.json()["outfits"][0]


def test_saved_looks_roundtrip(client):
    seeded = client.get("/api/saved-looks").json()
    assert {s["id"] for s in seeded} == {"seed-college", "seed-office", "seed-wedding", "seed-party"}
    assert all(s["isSample"] for s in seeded)

    outfit = _outfit(client, occasion="office")
    body = {**outfit, "favorite": False, "savedAt": "2026-10-29T10:05:00.000Z"}
    assert client.post("/api/saved-looks", json=body).status_code == 201
    listed = client.get("/api/saved-looks").json()
    assert listed[0]["id"] == outfit["id"] and listed[0]["occasionLabel"] == "Office"

    fav = client.patch(f"/api/saved-looks/{outfit['id']}", json={"favorite": True})
    assert fav.status_code == 200 and fav.json()["favorite"] is True
    assert client.delete(f"/api/saved-looks/{outfit['id']}").status_code == 204
    assert all(s["id"] != outfit["id"] for s in client.get("/api/saved-looks").json())
    assert client.delete(f"/api/saved-looks/{outfit['id']}").status_code == 204


def test_saved_look_keeps_original_recommendation(client):
    outfit = _outfit(client, occasion="party", colors=["Black"])
    body = {**outfit, "favorite": False, "savedAt": "2026-10-29T10:05:00.000Z"}
    client.post("/api/saved-looks", json=body)
    reopened = next(s for s in client.get("/api/saved-looks").json() if s["id"] == outfit["id"])
    for key in ("title", "score", "whyItWorks", "items", "stylingTips", "missingItems", "preferences", "breakdown"):
        assert reopened[key] == outfit[key], key


def test_saved_look_is_idempotent_and_patch_404(client):
    outfit = _outfit(client)
    body = {**outfit, "favorite": False, "savedAt": "2026-10-29T10:05:00.000Z"}
    assert client.post("/api/saved-looks", json=body).status_code == 201
    assert client.post("/api/saved-looks", json=body).status_code == 201
    assert sum(1 for s in client.get("/api/saved-looks").json() if s["id"] == outfit["id"]) == 1
    assert client.patch("/api/saved-looks/missing", json={"favorite": True}).status_code == 404


def test_saved_look_validation(client):
    assert client.post("/api/saved-looks", json={"id": "x"}).status_code == 422


def test_saved_look_fills_uploaded_photo_from_wardrobe(client):
    data_url = "data:image/jpeg;base64,/9j/4AAQSkZJRgABAQ=="
    wardrobe = [
        item("up-top", "Photo Top", "tops", occasions=["college"], image=data_url),
        item("up-bottom", "Photo Jeans", "bottoms", subcategory="jeans", occasions=["college"]),
    ]
    client.put("/api/wardrobe/sync", json={"items": wardrobe})
    res = client.post("/api/recommendations", json=recommendation_request(wardrobe=wardrobe, maxOutfits=1))
    outfit = res.json()["outfits"][0]
    piece = outfit["items"][0]["pieces"][0]
    assert piece["image"] == ""  # uploaded photos are not echoed back in the recommendation
    client.post("/api/saved-looks", json={**outfit, "favorite": False, "savedAt": "2026-10-29T10:05:00.000Z"})
    saved = next(s for s in client.get("/api/saved-looks").json() if s["id"] == outfit["id"])
    assert saved["items"][0]["pieces"][0]["image"] == data_url


# ------------------------------------------------------------------ catalog
def test_catalog_lists_demo_products_with_filters(client):
    everything = client.get("/api/catalog").json()
    assert len(everything) >= 20 and all(p["priceIsDemo"] for p in everything)
    cheap_bags = client.get("/api/catalog", params={"category": "bags", "maxPrice": 1000}).json()
    assert cheap_bags and all(p["category"] == "bags" and p["price"] <= 1000 for p in cheap_bags)
    wedding = client.get("/api/catalog", params={"occasion": "wedding"}).json()
    assert {"Maroon Silk Saree"} <= {p["name"] for p in wedding}
    assert client.get("/api/catalog", params={"category": "hats"}).status_code == 422


def test_catalog_flags_products_the_user_already_has_similar(client):
    sneakers = next(p for p in client.get("/api/catalog", params={"category": "footwear"}).json() if p["name"] == "White Sneakers")
    assert sneakers["ownedSimilar"] is True  # the demo wardrobe has sneakers
    saree = next(p for p in client.get("/api/catalog").json() if p["name"] == "Maroon Silk Saree")
    assert saree["ownedSimilar"] is False


def test_unknown_route_and_media_are_404(client):
    assert client.get("/api/nope").status_code == 404
    assert client.get("/media/generated/missing.jpg").status_code == 404
