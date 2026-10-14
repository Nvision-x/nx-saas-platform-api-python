from __future__ import annotations

from typing import TYPE_CHECKING

import httpx
from pydantic import ValidationError

if TYPE_CHECKING:
    from nvisionx._models import ErrorDetail


class NxError(Exception):
    pass


class APIConnectionError(NxError):
    def __init__(self, message: str = "Connection error.", *, request: httpx.Request) -> None:
        super().__init__(message)
        self.request = request


class APITimeoutError(APIConnectionError):
    def __init__(self, *, request: httpx.Request) -> None:
        super().__init__("Request timed out.", request=request)


class JobTimeoutError(NxError):
    def __init__(self, job_id: str, timeout: float) -> None:
        super().__init__(f"Job {job_id} did not finish within {timeout:g}s.")
        self.job_id = job_id
        self.timeout = timeout


class StreamError(NxError):
    pass


class APIStatusError(NxError):
    status_code: int

    def __init__(self, message: str, *, response: httpx.Response, detail: ErrorDetail | None) -> None:
        super().__init__(message)
        self.message = message
        self.response = response
        self.status_code = response.status_code
        self.detail = detail

    @property
    def type(self) -> str | None:
        return self.detail.type if self.detail else None

    def __str__(self) -> str:
        kind = f" {self.type}" if self.type else ""
        return f"{self.status_code}{kind}: {self.message}"


class BadRequestError(APIStatusError):
    pass


class AuthenticationError(APIStatusError):
    pass


class PaymentRequiredError(APIStatusError):
    pass


class PermissionDeniedError(APIStatusError):
    @property
    def required_scope(self) -> str | None:
        return self.detail.required_scope if self.detail else None


class NotFoundError(APIStatusError):
    pass


class ConflictError(APIStatusError):
    pass


class UnprocessableEntityError(APIStatusError):
    pass


class RateLimitError(APIStatusError):
    @property
    def retry_after(self) -> float | None:
        return parse_retry_after(self.response)


class InternalServerError(APIStatusError):
    pass


_BY_STATUS: dict[int, type[APIStatusError]] = {
    400: BadRequestError,
    401: AuthenticationError,
    402: PaymentRequiredError,
    403: PermissionDeniedError,
    404: NotFoundError,
    409: ConflictError,
    413: BadRequestError,
    422: UnprocessableEntityError,
    429: RateLimitError,
}


def parse_retry_after(response: httpx.Response) -> float | None:
    value = response.headers.get("retry-after")
    if value is None:
        return None
    try:
        return max(float(value), 0.0)
    except ValueError:
        return None


def error_from_response(response: httpx.Response) -> APIStatusError:
    from nvisionx._models import Error

    detail: ErrorDetail | None = None
    message = response.reason_phrase or f"HTTP {response.status_code}"
    try:
        detail = Error.model_validate(response.json()).error
        message = detail.message
    except (ValueError, ValidationError):
        text = response.text.strip()
        if text:
            message = text[:500]

    cls = _BY_STATUS.get(response.status_code)
    if cls is None:
        cls = InternalServerError if response.status_code >= 500 else APIStatusError
    return cls(message, response=response, detail=detail)
