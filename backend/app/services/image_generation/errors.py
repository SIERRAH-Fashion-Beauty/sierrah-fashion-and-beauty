from __future__ import annotations


class ImageError(Exception):
    """A failure the API reports to the client as ``{"detail": {code, message, retryable}}``."""

    status_code = 502
    code = "image_error"
    retryable = False

    def __init__(self, message: str, *, code: str | None = None, retryable: bool | None = None) -> None:
        super().__init__(message)
        self.message = message
        if code is not None:
            self.code = code
        if retryable is not None:
            self.retryable = retryable


class OutfitNotFound(ImageError):
    status_code = 404
    code = "outfit_not_found"


class ProviderAuthError(ImageError):
    status_code = 502
    code = "provider_auth_failed"


class ProviderQuotaError(ImageError):
    status_code = 502
    code = "provider_quota_exceeded"


class ProviderRateLimited(ImageError):
    status_code = 429
    code = "provider_rate_limited"
    retryable = True


class ProviderRejected(ImageError):
    """The provider refused the request (content policy or invalid parameters)."""

    status_code = 422
    code = "provider_rejected"


class ProviderTimeout(ImageError):
    status_code = 504
    code = "provider_timeout"
    retryable = True


class ProviderUnavailable(ImageError):
    status_code = 502
    code = "provider_unavailable"
    retryable = True


class InvalidProviderResponse(ImageError):
    status_code = 502
    code = "invalid_provider_response"
    retryable = True


class LocalRateLimited(ImageError):
    status_code = 429
    code = "rate_limited"
    retryable = True
