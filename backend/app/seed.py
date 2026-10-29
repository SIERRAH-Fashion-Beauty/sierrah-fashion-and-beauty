"""First-run sample data: the demo wardrobe (see database.init_db) and a few saved looks.

The sample looks are produced by the real recommendation engine from the demo wardrobe,
and flagged ``isSample`` so the UI can label them as examples.
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone

from .config import get_settings
from .database import db
from .repositories import OutfitRepository, SavedLookRepository, WardrobeRepository
from .schemas import RecommendationRequest, SavedLook
from .services.recommendation import RecommendationEngine

SEEDS: list[tuple[str, dict, bool]] = [
    ("college", {"occasion": "college", "style": "casual", "colors": ["Purple"], "traits": ["comfortable", "simple"]}, False),
    ("office", {"occasion": "office", "style": "elegant", "colors": ["Black", "White"], "traits": ["minimal"]}, True),
    ("wedding", {"occasion": "wedding", "style": "traditional", "colors": ["Red"], "budget": "1500-3000"}, False),
    ("party", {"occasion": "party", "style": "elegant", "colors": ["Black"], "budget": "1500-3000", "traits": ["trendy"]}, True),
]


def seed_sample_looks(engine: RecommendationEngine) -> None:
    if not get_settings().seed_demo_data:
        return
    with db() as conn:
        done = conn.execute("SELECT 1 FROM meta WHERE key = 'seeded_looks'").fetchone()
    if done:
        return
    wardrobe = WardrobeRepository().list()
    saved_repo, outfit_repo = SavedLookRepository(), OutfitRepository()
    base = datetime(2026, 10, 28, 9, 0, tzinfo=timezone.utc)
    for index, (key, prefs, favorite) in enumerate(SEEDS):
        request = RecommendationRequest.model_validate({**prefs, "max_outfits": 1})
        outfit = engine.recommend(request, wardrobe, "database").outfits[0]
        stamp = (base - timedelta(days=index)).isoformat(timespec="milliseconds").replace("+00:00", "Z")
        outfit.id = f"seed-{key}"
        outfit.generated_at = stamp
        look = SavedLook.model_validate(
            {**outfit.model_dump(by_alias=True), "favorite": favorite, "savedAt": stamp, "isSample": True}
        )
        saved_repo.upsert(look)
        outfit_repo.save_many([outfit])
    with db() as conn:
        conn.execute("INSERT OR REPLACE INTO meta (key, value) VALUES ('seeded_looks', '1')")
