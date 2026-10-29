"""Occasion engine behaviour through the real HTTP endpoint."""

import pytest

from factories import item, recommendation_request, saree_wardrobe

BUDGET_CAP = {"under-500": 500, "500-1500": 1500, "1500-3000": 3000}


def recommend(client, **overrides):
    res = client.post("/api/recommendations", json=recommendation_request(**overrides))
    assert res.status_code == 200, res.text
    return res.json()


def titles(data):
    return [o["title"] for o in data["outfits"]]


def slot(outfit, name):
    return next((i for i in outfit["items"] if i["slot"] == name), None)


def garment_names(outfit):
    return {p["name"] for p in slot(outfit, "outfit")["pieces"]}


# ------------------------------------------------------------ response shape
def test_every_outfit_has_the_required_fields(client):
    data = recommend(client, occasion="college")
    assert data["engineVersion"] and data["wardrobeSource"] == "database" and data["wardrobeSize"] == 18
    assert 1 <= len(data["outfits"]) <= 3
    for rank, outfit in enumerate(data["outfits"], start=1):
        assert outfit["rank"] == rank and 0 <= outfit["score"] <= 100 and outfit["scoreLabel"]
        assert outfit["title"] and outfit["whyItWorks"] and outfit["stylingTips"]
        slots = {i["slot"] for i in outfit["items"]}
        assert {"outfit", "footwear", "bag", "jewellery", "makeup", "hairstyle"} <= slots
        assert [p["key"] for p in outfit["breakdown"]]
        assert sum(p["points"] for p in outfit["breakdown"]) == pytest.approx(outfit["score"], abs=0.6)
        assert outfit["id"] and outfit["requestId"] == data["requestId"] and outfit["image"] is None
        assert slot(outfit, "outfit")["pieces"][0]["image"].startswith("/images/")
    scores = [o["score"] for o in data["outfits"]]
    assert scores == sorted(scores, reverse=True)


def test_makeup_and_hairstyle_always_come_with_the_look(client):
    outfit = recommend(client, occasion="wedding")["outfits"][0]
    assert slot(outfit, "hairstyle")["source"] == "tip" and slot(outfit, "hairstyle")["title"]
    assert slot(outfit, "makeup")["title"]


# ---------------------------------------------------------------- occasions
def test_college_prefers_comfortable_practical_pieces(client):
    outfit = recommend(client, occasion="college")["outfits"][0]
    assert slot(outfit, "footwear")["title"] in {"Sneakers", "Flats"}
    assert "Heels" not in slot(outfit, "footwear")["title"]
    assert slot(outfit, "bag")["title"] in {"Beige Sling Bag", "Backpack", "Tote Bag"} or "Sling" in slot(outfit, "bag")["title"]
    assert outfit["score"] >= 70


def test_casual_is_relaxed(client):
    outfit = recommend(client, occasion="casual")["outfits"][0]
    assert slot(outfit, "footwear")["title"] in {"Sneakers", "Flats"}
    assert outfit["resolvedOccasion"] == "casual"


def test_office_avoids_sneakers_and_prefers_structured(client):
    outfit = recommend(client, occasion="office")["outfits"][0]
    assert "Sneakers" not in slot(outfit, "footwear")["title"]
    assert slot(outfit, "bag")["title"] == "Handbag"


def test_wedding_demo_wardrobe_explains_it_has_no_ethnic_set(client):
    data = recommend(client, occasion="wedding")
    assert any("None of your garments are tagged for wedding" in text for text in data["limitations"])
    top = data["outfits"][0]
    assert slot(top, "footwear")["title"] == "Heels"
    assert not any(i["slot"] == "footwear" and "Sneaker" in i["title"] for i in top["items"])


def test_wedding_with_big_budget_suggests_ethnic_purchase_marked_as_shopping(client):
    data = recommend(client, occasion="wedding", budget="3000-plus")
    top = data["outfits"][0]
    outfit_slot = slot(top, "outfit")
    assert outfit_slot["source"] == "shopping"
    assert {"Maroon Silk Saree", "Rose Embroidered Lehenga Set"} & {p["name"] for o in data["outfits"] for p in slot(o, "outfit")["pieces"]}
    assert all(p["source"] == "shopping" and p["shopItemId"] for p in outfit_slot["pieces"])
    assert top["suggestedTotal"] > 0


def test_wedding_uses_owned_saree_when_the_wardrobe_has_one(client):
    data = recommend(client, occasion="wedding", wardrobe=saree_wardrobe(), budget="500-1500")
    top = data["outfits"][0]
    assert slot(top, "outfit")["source"] == "wardrobe"
    assert garment_names(top) in ({"Red Silk Saree"}, {"Pink Lehenga"})
    assert slot(top, "footwear")["title"] == "Gold Heels" and slot(top, "bag")["title"] == "Gold Clutch"
    assert slot(top, "jewellery")["title"] == "Gold Jhumkas"
    assert top["suggestedTotal"] == 0 and top["missingItems"] == []
    assert data["limitations"] == [] or all("saree" not in text.lower() for text in data["limitations"])


def test_party_prefers_dress_and_statement_pieces(client):
    outfit = recommend(client, occasion="party")["outfits"][0]
    assert "Dress" in slot(outfit, "outfit")["title"]
    assert slot(outfit, "footwear")["title"] == "Heels"


def test_travel_prefers_comfort_and_walking_shoes(client):
    outfit = recommend(client, occasion="travel")["outfits"][0]
    assert slot(outfit, "footwear")["title"] in {"Sneakers", "Flats"}
    assert outfit["breakdown"][3]["key"] == "comfort" and outfit["breakdown"][3]["points"] >= 8


def test_festival_is_traditional_and_coordinated(client):
    data = recommend(client, occasion="festival", budget="1500-3000")
    top = data["outfits"][0]
    assert top["resolvedOccasion"] == "festival"
    assert slot(top, "jewellery") is not None


def test_same_wardrobe_gives_different_looks_per_occasion(client):
    seen = {}
    for occasion in ("college", "office", "wedding", "party", "travel"):
        top = recommend(client, occasion=occasion, maxOutfits=1)["outfits"][0]
        seen[occasion] = (top["title"], slot(top, "footwear")["title"], slot(top, "bag")["title"])
    assert len(set(seen.values())) >= 3, seen
    assert seen["college"] != seen["wedding"] and seen["office"] != seen["party"]
    assert seen["wedding"][1] != seen["college"][1]


# -------------------------------------------------------------- distinctness
def test_multiple_distinct_outfits(client):
    data = recommend(client, occasion="college", maxOutfits=5)
    assert len(data["outfits"]) >= 3
    outfits = [garment_names(o) for o in data["outfits"]]
    assert len({frozenset(n) for n in outfits}) == len(outfits)
    assert len(set(titles(data))) == len(data["outfits"])
    assert len({o["id"] for o in data["outfits"]}) == len(data["outfits"])


def test_max_outfits_limits_results(client):
    assert len(recommend(client, occasion="casual", maxOutfits=1)["outfits"]) == 1


# --------------------------------------------------- preferences & colours
def test_favourite_colour_changes_ranking(client):
    purple = recommend(client, occasion="college", colors=["Purple"])["outfits"][0]
    pink = recommend(client, occasion="college", colors=["Pink"])["outfits"][0]
    assert "Lavender Kurti" in garment_names(purple) or "Purple" in str(slot(purple, "outfit")["detail"])
    assert garment_names(purple) != garment_names(pink)
    assert purple["breakdown"][1]["key"] == "color" and purple["breakdown"][1]["points"] > pink["breakdown"][1]["points"] - 5


def test_colour_preference_improves_colour_score_for_matching_outfit(client):
    base = recommend(client, occasion="college", maxOutfits=5)
    lavender = next(o for o in base["outfits"] if "Lavender Kurti" in garment_names(o))
    boosted = recommend(client, occasion="college", maxOutfits=5, colors=["Purple"])
    lavender_boosted = next(o for o in boosted["outfits"] if "Lavender Kurti" in garment_names(o))
    assert lavender_boosted["score"] >= lavender["score"]
    assert lavender_boosted["rank"] == 1


def test_style_preference_influences_choice(client):
    western = recommend(client, occasion="casual", style="western", maxOutfits=4)["outfits"]
    traditional = recommend(client, occasion="casual", style="traditional", maxOutfits=4)["outfits"]
    assert {frozenset(garment_names(o)) for o in western} != {frozenset(garment_names(o)) for o in traditional}
    assert not any("Kurti" in n for o in western[:1] for n in garment_names(o))
    assert any("Kurti" in n for o in traditional for n in garment_names(o))
    assert "Western" in western[0]["title"] and "Traditional" in traditional[0]["title"]


def test_notes_can_exclude_items(client):
    base = recommend(client, occasion="office", maxOutfits=1)["outfits"][0]
    assert slot(base, "footwear")["title"] == "Heels"
    data = recommend(client, occasion="office", notes="no heels please", maxOutfits=1)
    footwear = slot(data["outfits"][0], "footwear")
    assert "Heels" not in footwear["title"]
    assert any("avoid" in text for text in data["limitations"])


def test_comfort_priority_prefers_comfortable_items(client):
    wardrobe = [
        item("a-top", "Stiff Blazer Top", "tops", comfort=1, occasions=["casual"], fabric="Polyester"),
        item("b-top", "Soft Tee", "tops", comfort=5, occasions=["casual"], fabric="Cotton"),
        item("a-bot", "Jeans", "bottoms", subcategory="jeans", colors=["Blue"], comfort=4, occasions=["casual"]),
    ]
    high = recommend(client, occasion="casual", wardrobe=wardrobe, comfort="high", maxOutfits=1)["outfits"][0]
    assert "Soft Tee" in garment_names(high)


# ------------------------------------------------------------------- budget
@pytest.mark.parametrize("budget", ["under-500", "500-1500", "1500-3000"])
def test_suggested_spending_never_exceeds_budget(client, budget):
    for occasion in ("college", "office", "wedding", "party"):
        for wardrobe in ([], [item("only", "Plain Top")], None):
            body = {"wardrobe": wardrobe} if wardrobe is not None else {}
            data = recommend(client, occasion=occasion, budget=budget, **body)
            for outfit in data["outfits"]:
                assert outfit["suggestedTotal"] <= BUDGET_CAP[budget], (occasion, budget, outfit["title"])
                assert outfit["budgetMax"] == BUDGET_CAP[budget]


def test_higher_budget_unlocks_more_suggestions(client):
    low = recommend(client, occasion="wedding", budget="under-500")
    high = recommend(client, occasion="wedding", budget="3000-plus")
    assert max(o["suggestedTotal"] for o in low["outfits"]) <= 500
    assert max(o["suggestedTotal"] for o in high["outfits"]) > 2000
    assert high["outfits"][0]["score"] > low["outfits"][0]["score"]
    assert any("above your budget" in text for text in low["limitations"])


def test_budget_unlimited_has_no_cap(client):
    assert recommend(client, occasion="wedding", budget="3000-plus")["outfits"][0]["budgetMax"] is None


# ------------------------------------------------- missing items & ownership
def test_empty_wardrobe_marks_every_piece_as_shopping_or_tip(client):
    data = recommend(client, occasion="office", wardrobe=[], budget="1500-3000")
    assert data["wardrobeSize"] == 0 and any("no usable items" in text for text in data["limitations"])
    for outfit in data["outfits"]:
        for entry in outfit["items"]:
            assert entry["source"] in {"shopping", "tip"}, entry
            for piece in entry["pieces"]:
                assert piece["source"] == "shopping" and piece["wardrobeItemId"] is None
        assert outfit["missingItems"], "an empty wardrobe must list missing items"


def test_limited_wardrobe_lists_missing_items_with_alternatives(client):
    wardrobe = [item("t1", "White Top", "tops", occasions=["college"], colors=["White"]),
                item("b1", "Blue Jeans", "bottoms", subcategory="jeans", occasions=["college"], colors=["Blue"])]
    data = recommend(client, occasion="college", wardrobe=wardrobe, budget="500-1500", maxOutfits=1)
    top = data["outfits"][0]
    assert slot(top, "outfit")["source"] == "wardrobe"
    missing = {m["slot"]: m for m in top["missingItems"]}
    assert "footwear" in missing and missing["footwear"]["suggestion"]["priceIsDemo"] is True
    assert missing["footwear"]["withinBudget"] and missing["footwear"]["suggestion"]["price"] <= 1500
    assert missing["footwear"]["alternatives"]
    assert all(a["price"] <= missing["footwear"]["suggestion"]["price"] for a in missing["footwear"]["alternatives"])
    assert slot(top, "footwear")["source"] == "shopping"  # a purchase is never shown as owned
    assert top["suggestedTotal"] == sum(
        (m["suggestion"] or {}).get("price", 0) for m in top["missingItems"] if m["withinBudget"] and m["suggestion"]
    )


def test_owned_items_are_never_presented_as_purchases(client):
    top = recommend(client, occasion="college", maxOutfits=1)["outfits"][0]
    for entry in top["items"]:
        if entry["source"] == "wardrobe":
            assert entry["wardrobeItemIds"] and entry["shopItemId"] is None
    assert top["missingItems"] == [] and top["suggestedTotal"] == 0


def test_unsuitable_wardrobe_item_is_not_forced_into_the_look(client):
    wardrobe = [item("t1", "Party Sequin Top", "tops", occasions=["party"], styles=["trendy"], colors=["Black"],
                     fabric="Sequin", comfort=2),
                item("f1", "Stilettos", "footwear", subcategory="stilettos", occasions=["party"], colors=["Black"])]
    top = recommend(client, occasion="college", wardrobe=wardrobe, maxOutfits=1)["outfits"][0]
    assert slot(top, "footwear")["source"] == "shopping"


def test_limitations_explain_a_thin_wardrobe(client):
    data = recommend(client, occasion="college", wardrobe=[item("only", "Sparkly Top", occasions=["party"])])
    assert data["limitations"]


# ---------------------------------------------------- inventory variations
def test_different_wardrobes_give_different_looks(client):
    a = recommend(client, occasion="college", wardrobe=[
        item("a1", "Green Tee", "tops", colors=["Green"], occasions=["college"]),
        item("a2", "Black Jeans", "bottoms", subcategory="jeans", colors=["Black"], occasions=["college"])], maxOutfits=1)
    b = recommend(client, occasion="college", wardrobe=[
        item("b1", "Maroon Kurti", "kurtis", subcategory="kurti", colors=["Maroon"], occasions=["college"]),
        item("b2", "Cream Leggings", "bottoms", subcategory="leggings", colors=["Cream"], occasions=["college"])], maxOutfits=1)
    assert garment_names(a["outfits"][0]) == {"Green Tee", "Black Jeans"}
    assert garment_names(b["outfits"][0]) == {"Maroon Kurti", "Cream Leggings"}


def test_wardrobe_in_request_overrides_database(client):
    data = recommend(client, occasion="casual", wardrobe=[item("solo", "Solo Dress", "dresses", subcategory="dress", occasions=["casual"])])
    assert data["wardrobeSource"] == "request" and data["wardrobeSize"] == 1
    assert "Solo Dress" in garment_names(data["outfits"][0])


def test_recommend_works_after_deleting_everything_in_the_database(client):
    client.put("/api/wardrobe/sync", json={"items": []})
    data = recommend(client, occasion="casual")
    assert data["wardrobeSize"] == 0 and data["outfits"]


# ----------------------------------------------------------------- custom
def test_custom_occasion_is_interpreted(client):
    data = recommend(client, occasion="custom", customOccasion="Cousin's sangeet", budget="3000-plus")
    assert data["resolvedOccasion"] == "wedding" and data["occasionLabel"] == "Cousin's sangeet"
    assert any("styled like our Wedding occasion" in t for t in data["limitations"])
    brunch = recommend(client, occasion="custom", customOccasion="Sunday brunch with friends")
    assert brunch["resolvedOccasion"] == "casual"


def test_unknown_custom_occasion_falls_back_with_a_clear_message(client):
    data = recommend(client, occasion="custom", customOccasion="Zorb gala")
    assert data["resolvedOccasion"] == "casual"
    assert any("did not recognise" in t for t in data["limitations"])


def test_custom_occasion_without_text_is_accepted(client):
    data = recommend(client, occasion="custom")
    assert data["outfits"] and data["occasionLabel"]


# -------------------------------------------------------------- persistence
def test_recommended_outfits_are_stored_and_retrievable(client):
    data = recommend(client, occasion="office", maxOutfits=2)
    for outfit in data["outfits"]:
        stored = client.get(f"/api/outfits/{outfit['id']}")
        assert stored.status_code == 200 and stored.json()["title"] == outfit["title"]
    assert client.get("/api/outfits/does-not-exist").status_code == 404


def test_recommendation_is_deterministic_for_same_input(client):
    a = recommend(client, occasion="office", maxOutfits=3)
    b = recommend(client, occasion="office", maxOutfits=3)
    assert [o["title"] for o in a["outfits"]] == [o["title"] for o in b["outfits"]]
    assert [o["score"] for o in a["outfits"]] == [o["score"] for o in b["outfits"]]
    assert {o["id"] for o in a["outfits"]}.isdisjoint({o["id"] for o in b["outfits"]})


# --------------------------------------------------------------- invalid input
@pytest.mark.parametrize(
    "overrides",
    [
        {"occasion": "moon-party"},
        {"budget": "free"},
        {"comfort": "extreme"},
        {"style": "gothic"},
        {"maxOutfits": 0},
        {"maxOutfits": 9},
        {"traits": ["sparkly"]},
        {"notes": "x" * 401},
        {"wardrobe": [{"id": "x"}]},
        {"wardrobe": [item("dup-bad", category="hats")]},
    ],
)
def test_invalid_recommendation_requests_return_422(client, overrides):
    res = client.post("/api/recommendations", json=recommendation_request(**overrides))
    assert res.status_code == 422
    assert isinstance(res.json()["detail"], list)


def test_missing_occasion_returns_422(client):
    assert client.post("/api/recommendations", json={}).status_code == 422
    assert client.post("/api/recommendations", content="oops", headers={"Content-Type": "application/json"}).status_code == 422


def test_large_wardrobe_is_handled(client):
    wardrobe = [item(f"bulk-{i}", f"Top {i}", "tops", colors=["Blue" if i % 2 else "Red"], occasions=["casual"]) for i in range(150)]
    wardrobe += [item(f"bot-{i}", f"Jeans {i}", "bottoms", subcategory="jeans", occasions=["casual"]) for i in range(150)]
    data = recommend(client, occasion="casual", wardrobe=wardrobe)
    assert data["wardrobeSize"] == 300 and len(data["outfits"]) == 3
