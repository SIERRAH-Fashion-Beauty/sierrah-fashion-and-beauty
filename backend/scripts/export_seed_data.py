"""Single source of truth for the demo wardrobe and the demo shopping catalog.

Run from the ``backend`` folder:

    python scripts/export_seed_data.py

It writes the JSON files the API seeds from and the JSON files the frontend uses
as its offline copy, so both sides always agree. It also runs the real Python
recommendation engine to produce the sample looks shown before the API is reachable.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "backend"))
CREATED = "2026-10-29T10:00:00.000Z"


def w(
    key, name, category, sub, colors, styles, occasions, fabric, comfort, tags, image, price=None
):
    return {
        "id": f"demo-{key}",
        "name": name,
        "category": category,
        "subcategory": sub,
        "colors": colors,
        "styles": styles,
        "occasions": occasions,
        "fabric": fabric,
        "comfort": comfort,
        "price": price,
        "tags": tags,
        "image": f"/images/items/{image}.jpg",
        "createdAt": CREATED,
    }


DEMO_WARDROBE = [
    w("floral-dress", "Floral Dress", "dresses", "casual dress", ["Blue"], ["casual", "western", "elegant"],
      ["casual", "party", "travel"], "Chiffon", 4, ["floral", "dress"], "floral-dress", 1799),
    w("blue-kurti", "Blue Kurti", "kurtis", "kurti", ["Blue"], ["traditional"],
      ["college", "office", "festival"], "Cotton", 5, ["kurti", "comfortable"], "blue-kurti", 899),
    w("white-top", "White Top", "tops", "top", ["White"], ["casual", "western"],
      ["college", "casual", "office", "travel"], "Cotton", 4, ["minimal", "simple"], "white-top", 499),
    w("jeans", "Jeans", "bottoms", "jeans", ["Blue"], ["casual", "western"],
      ["college", "casual", "travel"], "Denim", 4, ["denim", "comfortable"], "jeans", 1499),
    w("black-skirt", "Black Skirt", "bottoms", "skirt", ["Black"], ["western", "elegant", "trendy"],
      ["office", "party"], "Crepe", 3, ["minimal"], "black-skirt", 799),
    w("sneakers", "Sneakers", "footwear", "sneakers", ["White"], ["casual", "western"],
      ["college", "casual", "travel"], "Canvas", 5, ["sneakers", "comfortable", "simple"], "sneakers", 1299),
    w("heels", "Heels", "footwear", "heels", ["Beige"], ["elegant", "western"],
      ["office", "party", "wedding"], "Faux leather", 2, ["heels"], "heels", 1599),
    w("handbag", "Handbag", "bags", "handbag", ["Pink"], ["elegant"],
      ["office", "party", "wedding"], "Faux leather", 3, ["handbag", "structured"], "handbag", 1299),
    w("earrings", "Earrings", "jewellery", "earrings", ["Gold"], ["elegant", "traditional"],
      ["college", "office", "party", "wedding", "festival"], "Metal", 4, ["earrings", "minimal"], "earrings", 399),
    w("watch", "Watch", "jewellery", "watch", ["Rose Gold"], ["casual", "elegant"],
      ["college", "office", "casual", "travel"], "Metal", 4, ["watch", "minimal"], "watch", 1999),
    w("lipstick", "Lipstick", "makeup", "lipstick", ["Red"], ["elegant"],
      ["party", "wedding", "festival", "office"], "", 5, ["lipstick"], "lipstick", 599),
    w("foundation", "Foundation", "makeup", "foundation", ["Beige"], ["elegant"],
      ["party", "wedding", "office"], "", 5, ["foundation"], "foundation", 799),
    w("compact", "Compact", "makeup", "compact", ["Pink"], ["casual", "elegant"],
      ["college", "casual", "office", "travel"], "", 5, ["compact", "minimal"], "compact", 349),
    w("perfume", "Perfume", "skincare", "fragrance", ["Pink"], ["elegant"],
      ["party", "wedding", "festival"], "", 5, ["perfume"], "perfume", 999),
    w("hair-serum", "Hair Serum", "skincare", "hair care", ["Blue"], ["casual"],
      ["college", "casual", "travel"], "", 5, ["hair-serum"], "hair-serum", 449),
    w("lavender-kurti", "Lavender Kurti", "kurtis", "kurti", ["Purple"], ["traditional"],
      ["college", "casual", "office", "festival"], "Cotton", 5, ["kurti", "comfortable", "simple", "lavender-kurti"], "lavender-kurti", 999),
    w("white-trousers", "White Trousers", "bottoms", "trousers", ["White"], ["traditional", "elegant"],
      ["college", "casual", "office"], "Cotton blend", 4, ["minimal", "simple", "comfortable"], "white-trousers", 899),
    w("sling-bag", "Beige Sling Bag", "bags", "sling bag", ["Beige"], ["casual"],
      ["college", "casual", "travel"], "Canvas", 5, ["minimal", "simple", "sling-bag"], "sling-bag", 699),
]


def p(key, name, category, sub, colors, price, image, occasions, styles, fabric, comfort, desc):
    return {
        "id": f"shop-{key}",
        "name": name,
        "category": category,
        "subcategory": sub,
        "colors": colors,
        "price": price,
        "priceIsDemo": True,
        "image": f"/images/{image}.jpg",
        "occasions": occasions,
        "styles": styles,
        "fabric": fabric,
        "comfort": comfort,
        "description": desc,
    }


SHOP_CATALOG = [
    p("tee", "Light Blue Tee", "tops", "t-shirt", ["Blue"], 499, "shop/tee", ["casual", "college", "travel"],
      ["casual", "western"], "Cotton", 5, "A soft relaxed-fit tee for easy everyday outfits."),
    p("grey-top", "Grey Shirt Top", "tops", "top", ["Grey"], 899, "shop/grey-top", ["office", "college", "casual"],
      ["elegant", "western"], "Cotton blend", 4, "A twist-front top that dresses up jeans or skirts."),
    p("formal-shirt", "White Formal Shirt", "tops", "formal shirt", ["White"], 1199, "shop/formal-shirt", ["office"],
      ["elegant", "western"], "Cotton", 3, "A crisp button-up shirt that anchors an office look."),
    p("pink-kurti", "Pink Kurti", "kurtis", "kurti", ["Pink"], 1499, "shop/pink-kurti", ["college", "office", "festival"],
      ["traditional"], "Cotton", 5, "Embroidered cotton kurti in a dusty rose shade."),
    p("black-trousers", "Black Formal Trousers", "bottoms", "trousers", ["Black"], 1299, "shop/black-trousers",
      ["office", "party"], ["elegant", "western"], "Polyester blend", 4, "Tailored straight-leg trousers for polished looks."),
    p("party-dress", "Emerald Satin Dress", "dresses", "party dress", ["Green"], 2499, "shop/party-dress", ["party"],
      ["elegant", "trendy", "western"], "Satin", 3, "A draped satin midi dress made for evenings out."),
    p("silk-saree", "Maroon Silk Saree", "sarees", "saree", ["Maroon", "Gold"], 2999, "shop/silk-saree",
      ["wedding", "festival"], ["traditional", "elegant"], "Silk", 3, "A rich silk saree with a woven gold zari border."),
    p("lehenga", "Rose Embroidered Lehenga Set", "sarees", "lehenga", ["Pink"], 3999, "shop/lehenga",
      ["wedding", "festival"], ["traditional", "elegant"], "Net", 2, "A dusty rose lehenga set with a matching dupatta."),
    p("white-sneakers", "White Sneakers", "footwear", "sneakers", ["White"], 1299, "shop/chunky-sneakers",
      ["college", "casual", "travel"], ["casual", "western"], "Canvas", 5, "Clean everyday sneakers that go with almost everything."),
    p("flats", "Nude Ballet Flats", "footwear", "flats", ["Beige"], 899, "shop/flats",
      ["college", "office", "casual", "travel"], ["elegant", "casual"], "Faux leather", 4, "Soft flats that pair with kurtis, trousers and dresses."),
    p("block-heels", "Black Block Heels", "footwear", "heels", ["Black"], 1599, "shop/block-heels", ["office", "party"],
      ["elegant", "western"], "Faux leather", 3, "Stable block heels that stay comfortable through a long day."),
    p("juttis", "Embroidered Juttis", "footwear", "juttis", ["Yellow", "Gold"], 799, "shop/juttis", ["festival", "wedding"],
      ["traditional"], "Embroidered fabric", 4, "Traditional flats that feel as good as they look."),
    p("shoulder-bag", "Shoulder Bag", "bags", "shoulder bag", ["Brown"], 999, "shop/shoulder-bag",
      ["college", "casual", "office", "party"], ["casual", "elegant"], "Faux leather", 4, "A tan chain-strap bag that lifts simple outfits."),
    p("crossbody-bag", "Crossbody Bag", "bags", "crossbody", ["Pink"], 1199, "shop/crossbody-bag",
      ["college", "casual", "travel"], ["casual", "trendy"], "Faux leather", 5, "Hands-free pink crossbody for busy days."),
    p("sling-bag", "Beige Sling Bag", "bags", "sling bag", ["Beige"], 899, "look/bag", ["college", "casual", "travel"],
      ["casual"], "Canvas", 5, "Neutral sling that pairs with pastel kurtis."),
    p("backpack", "Canvas Backpack", "bags", "backpack", ["Brown", "Beige"], 1399, "shop/backpack", ["college", "travel"],
      ["casual"], "Canvas", 5, "Roomy backpack for books, laptops and long days."),
    p("tote", "Structured Work Tote", "bags", "tote", ["Black"], 1799, "shop/tote", ["office"],
      ["elegant", "western"], "Faux leather", 4, "A structured tote that fits a laptop sleeve and planner."),
    p("clutch", "Gold Evening Clutch", "bags", "clutch", ["Gold"], 899, "shop/clutch", ["party", "wedding", "festival"],
      ["elegant", "traditional"], "Embellished fabric", 3, "A small embellished clutch with a slim chain strap."),
    p("statement-earrings", "Statement Earrings", "jewellery", "jhumkas", ["Gold"], 799, "shop/statement-earrings",
      ["wedding", "festival", "party"], ["traditional", "elegant"], "Metal", 3, "Kundan-style chandbalis for festive outfits."),
    p("pearl-drops", "Pearl Drop Earrings", "jewellery", "earrings", ["White", "Gold"], 599, "look/jewellery",
      ["college", "office", "casual", "party"], ["elegant", "casual"], "Pearl", 4, "Light pearl drops for a soft, polished finish."),
    p("gold-set", "Gold Necklace & Jhumka Set", "jewellery", "necklace set", ["Gold"], 1999, "shop/gold-set",
      ["wedding", "festival"], ["traditional"], "Gold plated", 3, "A temple-style necklace with matching jhumkas."),
    p("nude-makeup", "Nude Makeup Set", "makeup", "makeup kit", ["Beige", "Pink"], 1299, "look/makeup",
      ["college", "casual", "office", "travel"], ["casual", "elegant"], "", 5, "Lip balm, blush duo and mascara for a fresh face."),
    p("red-lipstick", "Classic Red Lipstick", "makeup", "lipstick", ["Red"], 399, "items/lipstick",
      ["party", "wedding", "festival", "office"], ["elegant", "traditional"], "", 5, "A creamy red that lifts evening and festive looks."),
    p("hair-serum", "Hair Serum", "skincare", "hair care", ["Blue"], 499, "items/hair-serum",
      ["college", "casual", "travel", "wedding", "festival"], ["casual", "elegant"], "", 5, "Smooths frizz for soft, glossy waves."),
]


def dump(path: Path, data) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print("wrote", path.relative_to(ROOT))


def sample_looks() -> tuple[dict, list[dict]]:
    """Demo look (lavender kurti) and the 4 sample saved looks, produced by the real engine."""
    from datetime import datetime, timedelta, timezone

    from app.schemas import RecommendationRequest, ShopProduct, WardrobeItem
    from app.seed import SEEDS
    from app.services.catalog import CatalogService
    from app.services.recommendation import RecommendationEngine

    engine = RecommendationEngine(CatalogService([ShopProduct.model_validate(p) for p in SHOP_CATALOG]))
    wardrobe = [WardrobeItem.model_validate(i) for i in DEMO_WARDROBE]

    def run(prefs: dict):
        request = RecommendationRequest.model_validate({**prefs, "max_outfits": 1})
        return engine.recommend(request, wardrobe, "database").outfits[0]

    # The sample photo shows a lavender kurti with white trousers, so pick that real engine option.
    options = engine.recommend(
        RecommendationRequest.model_validate(
            {"occasion": "college", "style": "casual", "colors": ["Purple"], "traits": ["comfortable", "simple"],
             "max_outfits": 5}
        ),
        wardrobe,
        "database",
    ).outfits
    demo = next((o for o in options if o.items[0].title == "Lavender Kurti + White Trousers"), options[0])
    demo.id = "demo-look"
    demo.title = "College Casual Look"
    base = datetime(2026, 10, 28, 9, 0, tzinfo=timezone.utc)
    saved = []
    for index, (key, prefs, favorite) in enumerate(SEEDS):
        outfit = run(prefs)
        stamp = (base - timedelta(days=index)).isoformat(timespec="milliseconds").replace("+00:00", "Z")
        outfit.id, outfit.generated_at = f"seed-{key}", stamp
        saved.append({**outfit.model_dump(by_alias=True), "favorite": favorite, "savedAt": stamp, "isSample": True})
    return demo.model_dump(by_alias=True), saved


if __name__ == "__main__":
    dump(ROOT / "backend/app/data/demo_wardrobe.json", DEMO_WARDROBE)
    dump(ROOT / "backend/app/data/shop_catalog.json", SHOP_CATALOG)
    dump(ROOT / "frontend/src/data/seed/demoWardrobe.json", DEMO_WARDROBE)
    dump(ROOT / "frontend/src/data/seed/shopCatalog.json", SHOP_CATALOG)
    demo_look, sample_saved = sample_looks()
    dump(ROOT / "frontend/src/data/seed/demoLook.json", demo_look)
    dump(ROOT / "frontend/src/data/seed/sampleLooks.json", sample_saved)
