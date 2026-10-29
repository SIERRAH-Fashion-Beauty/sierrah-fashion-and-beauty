"""Pollinations (free, keyless) provider tests, against a mocked transport.

The request shape follows https://github.com/pollinations/pollinations/blob/master/APIDOCS.md
"""

from __future__ import annotations

import dataclasses
import threading
from urllib.parse import parse_qs, unquote, urlparse

import httpx
import pytest

from app.config import get_settings
from app.dependencies import get_image_service
from app.main import app
from app.repositories import ImageRepository, OutfitRepository, SavedLookRepository, WardrobeRepository
from app.services.image_generation import ImageGenerationService
from app.services.image_generation.errors import (
    InvalidProviderResponse,
    ProviderRateLimited,
    ProviderRejected,
    ProviderTimeout,
    ProviderUnavailable,
)
from app.services.image_generation.providers import PollinationsImageProvider, supported_providers
from app.services.image_generation.references import ReferenceImage
from app.services.image_generation.storage import MediaStore
from factories import recommendation_request

JPEG = b"\xff\xd8\xff\xe0" + b"fake-jpeg-bytes" * 20


def ok(data: bytes = JPEG) -> httpx.Response:
    return httpx.Response(200, content=data, headers={"content-type": "image/jpeg"})


class FakePollinations:
    def __init__(self, *replies) -> None:
        self.replies = list(replies) or [ok()]
        self.requests: list[httpx.Request] = []
        self._lock = threading.Lock()

    def __call__(self, request: httpx.Request) -> httpx.Response:
        with self._lock:
            self.requests.append(request)
            reply = self.replies.pop(0) if len(self.replies) > 1 else self.replies[0]
        if isinstance(reply, Exception):
            raise reply
        return reply

    @property
    def calls(self) -> int:
        return len(self.requests)


def provider_for(fake: FakePollinations, **overrides) -> PollinationsImageProvider:
    values = {"image_provider": "pollinations", "image_api_key": "", "image_max_retries": 1, **overrides}
    settings = dataclasses.replace(get_settings(), **values)
    return PollinationsImageProvider(settings, transport=httpx.MockTransport(fake), sleep=lambda _s: None)


def test_request_matches_documented_api_and_sends_no_key():
    fake = FakePollinations()
    prompt = "Photorealistic fashion photo\nOutfit: Lavender Kurti & White Trousers (100% cotton)."
    result = provider_for(fake).generate(prompt, [])
    assert result.data == JPEG and result.mime == "image/jpeg"
    req = fake.requests[0]
    assert req.method == "GET" and req.url.host == "image.pollinations.ai"
    assert req.url.path.startswith("/prompt/")
    sent = unquote(req.url.raw_path.decode().split("?")[0][len("/prompt/"):])
    assert "\n" not in sent and "%0A" not in req.url.raw_path.decode().upper()  # a newline makes the service 404
    assert sent == " ".join(prompt.split())
    q = parse_qs(urlparse(str(req.url)).query)
    assert q["width"] == ["512"] and q["height"] == ["768"] and "safe" not in q and q["seed"][0].isdigit()
    assert "authorization" not in req.headers and "x-goog-api-key" not in req.headers


def test_each_call_uses_a_new_seed_so_regenerate_differs():
    fake = FakePollinations()
    p = provider_for(fake)
    for _ in range(6):
        p.generate("p", [])
    seeds = {parse_qs(urlparse(str(req.url)).query)["seed"][0] for req in fake.requests}
    assert len(seeds) > 1


def test_reference_photos_are_ignored():
    fake = FakePollinations()
    p = provider_for(fake)
    assert p.supports_references is False
    p.generate("p", [ReferenceImage(data=JPEG, mime="image/jpeg", filename="a.jpg")])
    assert fake.calls == 1


def test_rate_limit_402_reports_retry_after_and_is_not_retried():
    fake = FakePollinations(httpx.Response(402, headers={"retry-after": "37"}, json={"error": "Payment Required"}))
    with pytest.raises(ProviderRateLimited) as caught:
        provider_for(fake, image_max_retries=3).generate("p", [])
    assert "37 seconds" in caught.value.message and caught.value.retryable
    assert fake.calls == 1


def test_server_errors_are_retried_then_succeed():
    fake = FakePollinations(httpx.Response(502), ok())
    assert provider_for(fake).generate("p", []).data == JPEG
    assert fake.calls == 2


@pytest.mark.parametrize(
    ("reply", "error"),
    [
        (httpx.Response(200, text="<html>image card</html>"), InvalidProviderResponse),
        (httpx.Response(403, text="blocked"), ProviderRejected),
        (httpx.Response(400, text="bad"), ProviderRejected),
        (httpx.Response(503, text="down"), ProviderUnavailable),
        (httpx.ReadTimeout("slow"), ProviderTimeout),
        (httpx.ConnectError("down"), ProviderUnavailable),
    ],
)
def test_error_mapping(reply, error):
    with pytest.raises(error):
        provider_for(FakePollinations(reply), image_max_retries=0).generate("p", [])


def test_pollinations_is_supported_and_needs_no_key(client, media_dir):
    assert "pollinations" in supported_providers()
    settings = dataclasses.replace(get_settings(), image_provider="pollinations", image_api_key="", media_dir=media_dir)
    service = ImageGenerationService(
        settings, outfits=OutfitRepository(), images=ImageRepository(), saved=SavedLookRepository(),
        wardrobe=WardrobeRepository(), store=MediaStore(media_dir),
    )
    status = service.status()
    assert status.configured is True and status.provider == "pollinations" and status.model


def test_full_pipeline_stores_caches_and_explains_missing_reference_support(client, media_dir):
    fake = FakePollinations()
    settings = dataclasses.replace(
        get_settings(), image_provider="pollinations", image_api_key="", media_dir=media_dir, image_max_retries=0
    )
    provider = PollinationsImageProvider(settings, transport=httpx.MockTransport(fake), sleep=lambda _s: None)
    service = ImageGenerationService(
        settings, outfits=OutfitRepository(), images=ImageRepository(), saved=SavedLookRepository(),
        wardrobe=WardrobeRepository(), store=MediaStore(media_dir), provider=provider,
    )
    app.dependency_overrides[get_image_service] = lambda: service

    outfit = client.post("/api/recommendations", json=recommendation_request()).json()["outfits"][0]
    first = client.post(f"/api/outfits/{outfit['id']}/generate-image", json={"useReferenceImages": True}).json()
    assert first["status"] == "ready" and first["image"]["provider"] == "pollinations"
    assert "cannot use reference photos" in first["message"]
    assert client.get(first["image"]["url"]).content == JPEG
    sent = unquote(fake.requests[0].url.raw_path.decode().split("/prompt/", 1)[1])
    assert len(sent) < 600 and "fashion editorial photo" in sent  # compact prompt for the small free model
    assert outfit["items"][0]["pieces"][0]["name"].split()[0] in sent
    second = client.post(f"/api/outfits/{outfit['id']}/generate-image", json={}).json()
    assert second["cached"] is True and fake.calls == 1
