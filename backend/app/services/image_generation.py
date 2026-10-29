"""Image-generation seam for SIERRAH's next development phase.

The app currently shows curated editorial photographs for every look. To switch
to AI-generated model previews:

1. Implement a provider class below (see ``ExampleProvider`` for the shape).
2. Register it in ``PROVIDERS``.
3. Set ``IMAGE_PROVIDER``, ``IMAGE_API_KEY`` and ``IMAGE_MODEL`` in ``backend/.env``.

The frontend already calls ``POST /api/look-image`` when a look is generated and
will use ``imageUrl`` automatically when ``status == "ready"``.
"""

from __future__ import annotations

from typing import Any, Protocol

from ..config import Settings
from ..schemas import LookImageResponse


class ImageProvider(Protocol):
    name: str

    def generate(self, look: dict[str, Any]) -> LookImageResponse: ...


def build_prompt(look: dict[str, Any]) -> str:
    """Turn a look into a text prompt for any text-to-image model."""
    items = look.get("items", [])
    pieces = ", ".join(
        f"{i.get('slot')}: {i.get('title')}" for i in items if isinstance(i, dict)
    )
    prefs = look.get("preferences", {}) or {}
    return (
        "Full-length editorial fashion photograph of an elegant adult Indian woman "
        f"styled for {look.get('occasionLabel', 'an occasion')}. "
        f"Wearing {pieces}. Style: {prefs.get('style') or 'effortless'}. "
        "Soft natural light, cream and blush backdrop, realistic, no text or logos."
    )


class ExampleProvider:
    """Template only. Replace the body with a real API call."""

    name = "example"

    def __init__(self, settings: Settings) -> None:
        self.settings = settings

    def generate(self, look: dict[str, Any]) -> LookImageResponse:
        _prompt = build_prompt(look)  # send this to your provider
        return LookImageResponse(
            status="error",
            provider=self.name,
            message="ExampleProvider is a template and does not generate images.",
        )


PROVIDERS: dict[str, type] = {
    # "openai": OpenAIProvider,
    # "replicate": ReplicateProvider,
    "example": ExampleProvider,
}


def generate_look_image(look: dict[str, Any], settings: Settings) -> LookImageResponse:
    provider_name = settings.image_provider
    if provider_name in {"", "none"}:
        return LookImageResponse(
            status="not_configured",
            provider="none",
            message="No image provider configured. Using curated look photography.",
        )
    provider_cls = PROVIDERS.get(provider_name)
    if provider_cls is None:
        return LookImageResponse(
            status="error",
            provider=provider_name,
            message=f"Unknown IMAGE_PROVIDER '{provider_name}'.",
        )
    return provider_cls(settings).generate(look)
