"""Image providers.

``OpenAIImageProvider`` implements the OpenAI Image API as documented at
https://platform.openai.com/docs/guides/image-generation :

* text-to-image: ``POST /v1/images/generations`` (JSON) with ``model``, ``prompt``,
  ``size``, ``quality``, ``output_format`` and ``output_compression``; the image comes
  back as base64 in ``data[0].b64_json``.
* with reference photos: ``POST /v1/images/edits`` (multipart) with one or more
  ``image[]`` files plus the same parameters.

``GeminiImageProvider`` (Google Gemini / "Nano Banana") is defined further down.

Add another provider by implementing :class:`ImageProvider` and registering it in
:data:`PROVIDERS`.
"""

from __future__ import annotations

import base64
import binascii
import time
from collections.abc import Callable
from dataclasses import dataclass
from typing import Protocol

import httpx

from ...config import Settings
from .errors import (
    ImageError,
    InvalidProviderResponse,
    ProviderAuthError,
    ProviderQuotaError,
    ProviderRateLimited,
    ProviderRejected,
    ProviderTimeout,
    ProviderUnavailable,
)
from .references import ReferenceImage, sniff_mime


@dataclass(frozen=True)
class ProviderImage:
    data: bytes
    mime: str
    model: str


class ImageProvider(Protocol):
    name: str
    model: str
    supports_references: bool

    def generate(self, prompt: str, references: list[ReferenceImage]) -> ProviderImage: ...


class _HttpProvider:
    """Shared construction and retry policy (429, 5xx and timeouts are retried)."""

    name = ""
    supports_references = True
    DEFAULT_MODEL = ""
    DEFAULT_BASE_URL = ""

    def __init__(
        self,
        settings: Settings,
        *,
        transport: httpx.BaseTransport | None = None,
        sleep: Callable[[float], None] = time.sleep,
    ) -> None:
        self.settings = settings
        self.model = settings.image_model or self.DEFAULT_MODEL
        self.base_url = settings.image_api_base_url or self.DEFAULT_BASE_URL
        self._transport = transport
        self._sleep = sleep

    def generate(self, prompt: str, references: list[ReferenceImage]) -> ProviderImage:
        attempts = 1 + max(0, self.settings.image_max_retries)
        last: ImageError | None = None
        for attempt in range(attempts):
            try:
                return self._request_once(prompt, references)
            except (ProviderRateLimited, ProviderUnavailable, ProviderTimeout) as err:
                last = err
                if attempt + 1 < attempts:
                    self._sleep(min(2.0 * (attempt + 1), 8.0))
        assert last is not None
        raise last

    def _request_once(self, prompt: str, references: list[ReferenceImage]) -> ProviderImage:
        raise NotImplementedError


class OpenAIImageProvider(_HttpProvider):
    name = "openai"
    DEFAULT_MODEL = "gpt-image-2.5-flare"
    DEFAULT_BASE_URL = "https://api.openai.com/v1"

    # ------------------------------------------------------------------ API
    def _request_once(self, prompt: str, references: list[ReferenceImage]) -> ProviderImage:
        s = self.settings
        fields: dict[str, str] = {
            "model": self.model,
            "prompt": prompt,
            "size": s.image_size,
            "quality": s.image_quality,
            "output_format": "jpeg",
            "output_compression": "88",
            "n": "1",
        }
        headers = {"Authorization": f"Bearer {s.image_api_key}"}
        timeout = httpx.Timeout(s.image_timeout_seconds, connect=10.0)
        try:
            with httpx.Client(timeout=timeout, transport=self._transport) as client:
                if references:
                    files = [("image[]", (r.filename, r.data, r.mime)) for r in references]
                    response = client.post(f"{self.base_url}/images/edits", headers=headers, data=fields, files=files)
                else:
                    response = client.post(
                        f"{self.base_url}/images/generations",
                        headers=headers,
                        json={**fields, "n": 1, "output_compression": 88},
                    )
        except httpx.TimeoutException as err:
            raise ProviderTimeout(
                "The image provider took too long to respond. Please try again."
            ) from err
        except httpx.HTTPError as err:
            raise ProviderUnavailable("Could not reach the image provider. Check the connection and try again.") from err
        return self._parse(response)

    # ------------------------------------------------------------- parsing
    def _parse(self, response: httpx.Response) -> ProviderImage:
        if response.status_code == 200:
            try:
                b64 = response.json()["data"][0]["b64_json"]
                data = base64.b64decode(b64, validate=True)
            except (KeyError, IndexError, TypeError, ValueError, binascii.Error) as err:
                raise InvalidProviderResponse("The image provider returned an unexpected response.") from err
            mime = sniff_mime(data)
            if mime is None:
                raise InvalidProviderResponse("The image provider returned data that is not a valid image.")
            return ProviderImage(data=data, mime=mime, model=self.model)
        raise self._error_for(response)

    def _error_for(self, response: httpx.Response) -> ImageError:
        status = response.status_code
        code = message = kind = ""
        try:
            body = response.json().get("error") or {}
            code = str(body.get("code") or "")
            kind = str(body.get("type") or "")
            message = str(body.get("message") or "")
        except (ValueError, AttributeError):
            pass
        if status in (401, 403):
            return ProviderAuthError(
                "The image provider rejected the API key. Check IMAGE_API_KEY (and organisation verification) in backend/.env."
            )
        if status == 429:
            if code == "insufficient_quota" or "quota" in message.lower() or "billing" in message.lower():
                return ProviderQuotaError("The image provider account has no remaining quota. Check billing and limits.")
            return ProviderRateLimited("The image provider is busy right now. Please retry in a moment.")
        if status == 404:
            return ProviderRejected(
                f"The image model \"{self.model}\" was not found for this account. Check IMAGE_MODEL.",
                code="model_not_found",
            )
        if status == 400 or status == 422:
            if code == "moderation_blocked" or kind == "image_generation_user_error":
                return ProviderRejected(
                    "The image provider declined this request under its content policy. Try a different look.",
                    code="moderation_blocked",
                )
            return ProviderRejected(
                f"The image provider could not process the request{': ' + message if message else '.'}",
                code="invalid_request",
            )
        if status >= 500:
            return ProviderUnavailable("The image provider is having problems. Please try again shortly.")
        return ImageError(f"Unexpected response from the image provider ({status}).")


class GeminiImageProvider(_HttpProvider):
    """Google Gemini ("Nano Banana") image generation through the Interactions API.

    Documented at https://ai.google.dev/gemini-api/docs/image-generation :

    * ``POST {base}/interactions`` with the key in the ``x-goog-api-key`` header;
    * ``input`` is a list of ``{"type": "text", ...}`` and optional
      ``{"type": "image", "data": <base64>, "mime_type": ...}`` blocks (the clothing references);
    * ``response_format`` = ``{"type": "image", "mime_type", "aspect_ratio", "image_size"}``;
    * the picture comes back as ``steps[].content[]`` blocks of ``type: "image"`` with base64 ``data``.

    ``store: false`` asks Google not to keep the interaction for later retrieval.
    """

    name = "gemini"
    DEFAULT_MODEL = "gemini-nano-banana-2.1"
    DEFAULT_BASE_URL = "https://generativelanguage.googleapis.com/v1beta"

    def _request_once(self, prompt: str, references: list[ReferenceImage]) -> ProviderImage:
        s = self.settings
        blocks: list[dict] = [{"type": "text", "text": prompt}]
        for ref in references:
            blocks.append(
                {"type": "image", "data": base64.b64encode(ref.data).decode("ascii"), "mime_type": ref.mime}
            )
        payload = {
            "model": self.model,
            "input": blocks,
            "response_format": {
                "type": "image",
                "mime_type": "image/jpeg",
                "aspect_ratio": s.image_aspect_ratio,
                "image_size": s.image_resolution,
            },
            "store": False,
        }
        headers = {"x-goog-api-key": s.image_api_key, "Content-Type": "application/json"}
        timeout = httpx.Timeout(s.image_timeout_seconds, connect=10.0)
        try:
            with httpx.Client(timeout=timeout, transport=self._transport) as client:
                response = client.post(f"{self.base_url}/interactions", headers=headers, json=payload)
        except httpx.TimeoutException as err:
            raise ProviderTimeout("The image provider took too long to respond. Please try again.") from err
        except httpx.HTTPError as err:
            raise ProviderUnavailable("Could not reach the image provider. Check the connection and try again.") from err
        return self._parse(response)

    # ------------------------------------------------------------- parsing
    def _parse(self, response: httpx.Response) -> ProviderImage:
        if response.status_code != 200:
            raise self._error_for(response)
        try:
            body = response.json()
            steps = body.get("steps") or []
            state = body.get("status")
        except (ValueError, AttributeError) as err:
            raise InvalidProviderResponse("The image provider returned an unexpected response.") from err

        if state in ("failed", "cancelled", "incomplete"):
            raise ProviderRejected(
                f"The image provider did not finish this request (status: {state}). Try again or try a different look.",
                code="generation_failed",
                retryable=True,
            )

        texts: list[str] = []
        for step in steps if isinstance(steps, list) else []:
            if not isinstance(step, dict) or step.get("type") != "model_output":
                continue
            for block in step.get("content") or []:
                if not isinstance(block, dict):
                    continue
                if block.get("type") == "image" and block.get("data"):
                    try:
                        data = base64.b64decode(block["data"], validate=True)
                    except (binascii.Error, ValueError, TypeError) as err:
                        raise InvalidProviderResponse("The image provider returned an unexpected response.") from err
                    mime = sniff_mime(data)
                    if mime is None:
                        raise InvalidProviderResponse("The image provider returned data that is not a valid image.")
                    return ProviderImage(data=data, mime=mime, model=self.model)
                if block.get("type") == "text" and block.get("text"):
                    texts.append(str(block["text"]))

        detail = f" It said: \"{' '.join(texts)[:200]}\"" if texts else ""
        raise ProviderRejected(
            "The image provider did not return a picture for this request, which usually means its safety "
            "filters declined it. Try again or try a different look." + detail,
            code="no_image_returned",
            retryable=True,
        )

    def _error_for(self, response: httpx.Response) -> ImageError:
        status = response.status_code
        message = google_status = ""
        try:
            body = response.json().get("error") or {}
            message = str(body.get("message") or "")
            google_status = str(body.get("status") or "")
        except (ValueError, AttributeError):
            pass
        low = message.lower()

        if status in (401, 403) or "api key not valid" in low or "api_key_invalid" in low:
            return ProviderAuthError(
                "The image provider rejected the API key. Check IMAGE_API_KEY (your Gemini API key) in backend/.env, "
                "and that the key is allowed to use the Gemini API in your region."
            )
        if status == 429 or google_status == "RESOURCE_EXHAUSTED":
            if "billing" in low or "plan" in low or "daily" in low or "per day" in low:
                return ProviderQuotaError(
                    "The Gemini quota for this key is used up. Check the plan, billing and limits for your API key."
                )
            return ProviderRateLimited("The image provider is busy right now. Please retry in a moment.")
        if status == 404:
            return ProviderRejected(
                f"The image model \"{self.model}\" was not found for this key. Check IMAGE_MODEL.",
                code="model_not_found",
            )
        if status == 400 or status == 422:
            if "safety" in low or "blocked" in low or "policy" in low:
                return ProviderRejected(
                    "The image provider declined this request under its safety policy. Try a different look.",
                    code="moderation_blocked",
                )
            return ProviderRejected(
                f"The image provider could not process the request{': ' + message[:300] if message else '.'}",
                code="invalid_request",
            )
        if status >= 500:
            return ProviderUnavailable("The image provider is having problems. Please try again shortly.")
        return ImageError(f"Unexpected response from the image provider ({status}).")


PROVIDERS: dict[str, type[_HttpProvider]] = {
    "gemini": GeminiImageProvider,
    "google": GeminiImageProvider,  # alias
    "openai": OpenAIImageProvider,
}


def supported_providers() -> list[str]:
    return ["gemini", "openai"]
