"""Opt-in smoke test against the REAL image provider.

Skipped by default because it spends money. Run it deliberately with your own key:

    $env:SIERRAH_LIVE_IMAGE_TEST = "1"
    $env:LIVE_IMAGE_API_KEY = "sk-..."
    python -m pytest tests/test_live_provider.py -s
"""

import dataclasses
import os

import pytest

from app.config import get_settings
from app.services.image_generation.prompt import build_prompt
from app.services.image_generation.providers import OpenAIImageProvider

pytestmark = pytest.mark.skipif(
    os.environ.get("SIERRAH_LIVE_IMAGE_TEST") != "1" or not os.environ.get("LIVE_IMAGE_API_KEY"),
    reason="live provider test is opt-in (SIERRAH_LIVE_IMAGE_TEST=1 and LIVE_IMAGE_API_KEY)",
)


def test_real_provider_returns_a_valid_image(client):
    from app.schemas import Outfit

    outfit = Outfit.model_validate(client.get("/api/saved-looks").json()[0])
    settings = dataclasses.replace(
        get_settings(),
        image_provider="openai",
        image_api_key=os.environ["LIVE_IMAGE_API_KEY"],
        image_model=os.environ.get("LIVE_IMAGE_MODEL", ""),
        image_quality="low",
    )
    result = OpenAIImageProvider(settings).generate(build_prompt(outfit), [])
    assert result.mime in {"image/jpeg", "image/png", "image/webp"} and len(result.data) > 10_000
