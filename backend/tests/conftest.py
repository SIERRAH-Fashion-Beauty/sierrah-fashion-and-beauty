"""Shared test setup.

Environment variables are set *before* the app is imported so tests use a throwaway
database and media folder and never touch real credentials, even if a developer has a
backend/.env with an image API key.
"""

import os
import shutil
import tempfile
from pathlib import Path

_TMP = Path(tempfile.mkdtemp(prefix="sierrah-tests-"))
os.environ["DATABASE_PATH"] = str(_TMP / "test.db")
os.environ["MEDIA_DIR"] = str(_TMP / "media")
os.environ["SEED_DEMO_DATA"] = "true"
os.environ["IMAGE_PROVIDER"] = "none"
os.environ["IMAGE_API_KEY"] = ""
os.environ["IMAGE_MODEL"] = ""
os.environ["IMAGE_API_BASE_URL"] = ""

import pytest  # noqa: E402
from fastapi.testclient import TestClient  # noqa: E402

from app.database import db, init_db, load_demo_wardrobe  # noqa: E402
from app.dependencies import get_engine  # noqa: E402
from app.main import app  # noqa: E402
from app.seed import seed_sample_looks  # noqa: E402


@pytest.fixture(scope="session")
def client():
    with TestClient(app) as c:
        yield c


@pytest.fixture(autouse=True)
def clean_state(client):
    """Every test starts from a freshly seeded database and an empty media folder."""
    app.dependency_overrides.clear()
    with db() as conn:
        for table in ("wardrobe_items", "saved_looks", "outfits", "generated_images", "meta"):
            conn.execute(f"DELETE FROM {table}")
    init_db()
    seed_sample_looks(get_engine())
    generated = _TMP / "media" / "generated"
    shutil.rmtree(generated, ignore_errors=True)
    generated.mkdir(parents=True, exist_ok=True)
    yield
    app.dependency_overrides.clear()


@pytest.fixture()
def demo_wardrobe() -> list[dict]:
    return load_demo_wardrobe()


@pytest.fixture()
def media_dir() -> Path:
    return _TMP / "media"
