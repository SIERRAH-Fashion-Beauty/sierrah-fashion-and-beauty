"""Gemini image provider tests.

No real Google endpoint is contacted. The provider runs against an ``httpx.MockTransport``
that checks the request against the documented Interactions API
(https://ai.google.dev/gemini-api/docs/image-generation) and replies with Gemini-shaped
responses and errors.
"""

from __future__ import annotations

import base64
import dataclasses
import json
import threading

import httpx
import pytest

from app.config import get_settings
from app.dependencies import get_image_service
from app.main import app
from app.repositories import ImageRepository, OutfitRepository, SavedLookRepository, WardrobeRepository
from app.services.image_generation import ImageGenerationService
from app.services.image_generation.errors import (
    InvalidProviderResponse,
    ProviderAuthError,
    ProviderQuotaError,
    ProviderRateLimited,
    ProviderRejected,
    ProviderTimeout,
    ProviderUnavailable,
)
from app.services.image_generation.providers import GeminiImageProvider, supported_providers
from app.services.image_generation.references import ReferenceImage
from app.services.image_generation.storage import MediaStore
from factories import recommendation_request

JPEG = b"\xff\xd8\xff\xe0" + b"fake-jpeg-bytes" * 20
KEY = "AIza-test-key-123"


def ok(data: bytes = JPEG, *, status: str = "completed", extra_blocks: list | None = None) -> httpx.Response:
    content = list(extra_blocks or []) + [
        {"type": "image", "mime_type": "image/jpeg", "data": base64.b64encode(data).decode()}
    ]
    return httpx.Response(
        200,
        json={
            "id": "v1_x", "object": "interaction", "status": status, "model": "gemini-nano-banana-2.1",
            "steps": [{"type": "model_output", "content": content}],
        },
    )


def gerror(status: int, message: str = "boom", google_status: str = "") -> httpx.Response:
    return httpx.Response(status, json={"error": {"code": status, "message": message, "status": google_status}})


class FakeGemini:
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

    def body(self, index: int = 0) -> dict:
        return json.loads(self.requests[index].content)


def provider_for(fake: FakeGemini, **overrides) -> GeminiImageProvider:
    values = {"image_provider": "gemini", "image_api_key": KEY, "image_max_retries": 1, **overrides}
    settings = dataclasses.replace(get_settings(), **values)
    return GeminiImageProvider(settings, transport=httpx.MockTransport(fake), sleep=lambda _s: None)


# ------------------------------------------------------------ request shape
def test_request_matches_documented_interactions_api():
    fake = FakeGemini()
    result = provider_for(fake).generate("A model in a kurti", [])
    assert result.mime == "image/jpeg" and result.data == JPEG and result.model == "gemini-nano-banana-2.1"
    req = fake.requests[0]
    assert req.method == "POST"
    assert str(req.url) == "https://generativelanguage.googleapis.com/v1beta/interactions"
    assert req.headers["x-goog-api-key"] == KEY
    assert "authorization" not in req.headers and KEY not in str(req.url)
    body = fake.body()
    assert body["model"] == "gemini-nano-banana-2.1"
    assert body["input"] == [{"type": "text", "text": "A model in a kurti"}]
    assert body["response_format"] == {
        "type": "image", "mime_type": "image/jpeg", "aspect_ratio": "2:3", "image_size": "1K",
    }
    assert body["store"] is False


def test_model_aspect_ratio_resolution_and_base_url_are_configurable():
    fake = FakeGemini()
    provider_for(
        fake, image_model="gemini-3-pro-image", image_aspect_ratio="3:4", image_resolution="2K",
        image_api_base_url="http://localhost:9999/v1beta",
    ).generate("p", [])
    assert str(fake.requests[0].url) == "http://localhost:9999/v1beta/interactions"
    body = fake.body()
    assert body["model"] == "gemini-3-pro-image"
    assert body["response_format"]["aspect_ratio"] == "3:4" and body["response_format"]["image_size"] == "2K"


def test_reference_photos_are_sent_as_inline_image_blocks():
    fake = FakeGemini()
    refs = [ReferenceImage(data=JPEG, mime="image/jpeg", filename="a.jpg")]
    provider_for(fake).generate("p", refs)
    blocks = fake.body()["input"]
    assert blocks[0]["type"] == "text"
    assert blocks[1] == {"type": "image", "data": base64.b64encode(JPEG).decode(), "mime_type": "image/jpeg"}


def test_image_is_found_even_when_text_precedes_it():
    fake = FakeGemini(ok(extra_blocks=[{"type": "text", "text": "Here you go"}]))
    assert provider_for(fake).generate("p", []).data == JPEG


# ------------------------------------------------------------------- errors
@pytest.mark.parametrize(
    ("reply", "error", "code"),
    [
        (gerror(400, "API key not valid. Please pass a valid API key.", "INVALID_ARGUMENT"), ProviderAuthError, "provider_auth_failed"),
        (gerror(403, "denied", "PERMISSION_DENIED"), ProviderAuthError, "provider_auth_failed"),
        (gerror(401, "nope", "UNAUTHENTICATED"), ProviderAuthError, "provider_auth_failed"),
        (gerror(429, "Resource exhausted, try later", "RESOURCE_EXHAUSTED"), ProviderRateLimited, "provider_rate_limited"),
        (gerror(429, "You exceeded your current quota, check your plan and billing", "RESOURCE_EXHAUSTED"), ProviderQuotaError, "provider_quota_exceeded"),
        (gerror(404, "model not found", "NOT_FOUND"), ProviderRejected, "model_not_found"),
        (gerror(400, "Request blocked by safety settings", "INVALID_ARGUMENT"), ProviderRejected, "moderation_blocked"),
        (gerror(400, "Invalid aspect_ratio", "INVALID_ARGUMENT"), ProviderRejected, "invalid_request"),
        (gerror(503, "overloaded", "UNAVAILABLE"), ProviderUnavailable, "provider_unavailable"),
        (httpx.Response(200, text="<html>not json</html>"), InvalidProviderResponse, "invalid_provider_response"),
        (httpx.Response(200, json={"steps": [{"type": "model_output", "content": [{"type": "image", "data": "!!notb64"}]}]}), InvalidProviderResponse, "invalid_provider_response"),
        (httpx.Response(200, json={"steps": [{"type": "model_output", "content": [{"type": "image", "data": base64.b64encode(b"just text").decode()}]}]}), InvalidProviderResponse, "invalid_provider_response"),
    ],
)
def test_error_mapping(reply, error, code):
    fake = FakeGemini(reply)
    with pytest.raises(error) as caught:
        provider_for(fake, image_max_retries=0).generate("p", [])
    assert caught.value.code == code
    assert KEY not in caught.value.message


def test_text_only_answer_is_reported_as_no_image():
    reply = httpx.Response(
        200, json={"status": "completed", "steps": [{"type": "model_output", "content": [{"type": "text", "text": "I can't draw that."}]}]}
    )
    with pytest.raises(ProviderRejected) as caught:
        provider_for(FakeGemini(reply)).generate("p", [])
    assert caught.value.code == "no_image_returned" and "I can't draw that." in caught.value.message


def test_unfinished_interaction_is_reported():
    reply = httpx.Response(200, json={"status": "failed", "steps": []})
    with pytest.raises(ProviderRejected) as caught:
        provider_for(FakeGemini(reply)).generate("p", [])
    assert caught.value.code == "generation_failed" and caught.value.retryable


def test_transient_failures_are_retried_then_succeed():
    fake = FakeGemini(gerror(503), gerror(429, "slow down", "RESOURCE_EXHAUSTED"), ok())
    assert provider_for(fake, image_max_retries=2).generate("p", []).data == JPEG
    assert fake.calls == 3


def test_retries_are_bounded():
    fake = FakeGemini(gerror(503))
    with pytest.raises(ProviderUnavailable):
        provider_for(fake, image_max_retries=1).generate("p", [])
    assert fake.calls == 2


def test_auth_errors_are_not_retried():
    fake = FakeGemini(gerror(403, "denied", "PERMISSION_DENIED"))
    with pytest.raises(ProviderAuthError):
        provider_for(fake, image_max_retries=3).generate("p", [])
    assert fake.calls == 1


def test_timeout_and_connection_errors():
    with pytest.raises(ProviderTimeout):
        provider_for(FakeGemini(httpx.ReadTimeout("slow")), image_max_retries=0).generate("p", [])
    with pytest.raises(ProviderUnavailable):
        provider_for(FakeGemini(httpx.ConnectError("down")), image_max_retries=0).generate("p", [])


# ----------------------------------------------------- configuration + wiring
def test_gemini_is_a_supported_provider():
    assert "gemini" in supported_providers() and "openai" in supported_providers()


def test_gemini_key_env_fallbacks(monkeypatch):
    monkeypatch.setenv("IMAGE_PROVIDER", "gemini")
    monkeypatch.setenv("IMAGE_API_KEY", "")
    monkeypatch.setenv("GEMINI_API_KEY", "gem-key")
    assert get_settings().image_api_key == "gem-key"
    monkeypatch.setenv("GEMINI_API_KEY", "")
    monkeypatch.setenv("GOOGLE_API_KEY", "goog-key")
    assert get_settings().image_api_key == "goog-key"
    monkeypatch.setenv("IMAGE_API_KEY", "explicit")
    assert get_settings().image_api_key == "explicit"


def test_gemini_env_key_is_not_used_for_other_providers(monkeypatch):
    monkeypatch.setenv("IMAGE_PROVIDER", "openai")
    monkeypatch.setenv("IMAGE_API_KEY", "")
    monkeypatch.setenv("GEMINI_API_KEY", "gem-key")
    assert get_settings().image_api_key == ""


@pytest.fixture()
def gemini_service(media_dir):
    def _install(fake: FakeGemini | None = None):
        fake = fake or FakeGemini()
        settings = dataclasses.replace(
            get_settings(), image_provider="gemini", image_api_key=KEY, media_dir=media_dir, image_max_retries=1
        )
        provider = GeminiImageProvider(settings, transport=httpx.MockTransport(fake), sleep=lambda _s: None)
        service = ImageGenerationService(
            settings, outfits=OutfitRepository(), images=ImageRepository(), saved=SavedLookRepository(),
            wardrobe=WardrobeRepository(), store=MediaStore(media_dir), provider=provider,
        )
        app.dependency_overrides[get_image_service] = lambda: service
        return fake

    return _install


def test_full_pipeline_with_gemini_stores_and_caches_the_image(client, gemini_service):
    fake = gemini_service()
    health = client.get("/health").json()["imageGeneration"]
    assert health["configured"] is True and health["provider"] == "gemini" and health["model"] == "gemini-nano-banana-2.1"
    assert KEY not in client.get("/health").text

    outfit = client.post("/api/recommendations", json=recommendation_request()).json()["outfits"][0]
    first = client.post(f"/api/outfits/{outfit['id']}/generate-image", json={}).json()
    assert first["status"] == "ready" and first["cached"] is False
    assert first["image"]["provider"] == "gemini" and first["image"]["url"].startswith("/media/")
    assert client.get(first["image"]["url"]).content == JPEG
    assert KEY not in json.dumps(first)

    second = client.post(f"/api/outfits/{outfit['id']}/generate-image", json={}).json()
    assert second["cached"] is True and fake.calls == 1

    again = client.post(f"/api/outfits/{outfit['id']}/generate-image", json={"regenerate": True}).json()
    assert again["cached"] is False and fake.calls == 2


def test_pipeline_surfaces_gemini_errors_as_structured_json(client, gemini_service):
    gemini_service(FakeGemini(gerror(400, "API key not valid. Please pass a valid API key.", "INVALID_ARGUMENT")))
    outfit = client.post("/api/recommendations", json=recommendation_request()).json()["outfits"][0]
    res = client.post(f"/api/outfits/{outfit['id']}/generate-image", json={})
    assert res.status_code == 502
    detail = res.json()["detail"]
    assert detail["code"] == "provider_auth_failed" and "IMAGE_API_KEY" in detail["message"] and detail["retryable"] is False
    assert KEY not in res.text
