"""Image providers.

``OpenAIImageProvider`` implements the OpenAI Image API as documented at
https://platform.openai.com/docs/guides/image-generation :

* text-to-image: ``POST /v1/images/generations`` (JSON) with ``model``, ``prompt``,
  ``size``, ``quality``, ``output_format`` and ``output_compression``; the image comes
  back as base64 in ``data[0].b64_json``.
* with reference photos: ``POST /v1/images/edits`` (multipart) with one or more
  ``image[]`` files plus the same parameters.

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


class OpenAIImageProvider:
    name = "openai"
    supports_references = True
    DEFAULT_MODEL = "gpt-image-2.5-flare"
    DEFAULT_BASE_URL = "https://api.openai.com/v1"

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

    # ------------------------------------------------------------------ API
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


PROVIDERS: dict[str, type[OpenAIImageProvider]] = {"openai": OpenAIImageProvider}


def supported_providers() -> list[str]:
    return sorted(PROVIDERS)
