from __future__ import annotations

import os
import random
import uuid
from collections.abc import Mapping
from dataclasses import dataclass, field, replace
from typing import IO, Any, TypeVar
from urllib.parse import quote

import httpx
from pydantic import BaseModel

from nvisionx._errors import NxError, parse_retry_after
from nvisionx._version import __version__

DEFAULT_BASE_URL = "https://platform.us.nvisionx.ai"
DEFAULT_TIMEOUT = httpx.Timeout(60.0, connect=10.0)
DEFAULT_MAX_RETRIES = 2
AGENT_TIMEOUT = httpx.Timeout(300.0, connect=10.0)
UPLOAD_TIMEOUT = httpx.Timeout(60.0, connect=10.0, write=None)

RETRYABLE_STATUSES = frozenset({408, 429, 500, 502, 503, 504})
INITIAL_RETRY_DELAY = 0.5
MAX_RETRY_DELAY = 8.0
MAX_RETRY_AFTER = 60.0

ModelT = TypeVar("ModelT", bound=BaseModel)


@dataclass(frozen=True)
class RequestOptions:
    method: str
    path: str
    params: Mapping[str, Any] | None = None
    json: Any = None
    data: Mapping[str, Any] | None = None
    files: list[Any] | None = None
    headers: Mapping[str, str] = field(default_factory=dict)
    idempotency_key: str | None = None
    timeout: httpx.Timeout | None = None


def path(template: str, **params: str) -> str:
    return template.format(**{k: quote(v, safe="") for k, v in params.items()})


def drop_none(values: Mapping[str, Any]) -> dict[str, Any]:
    return {k: v for k, v in values.items() if v is not None}


class BaseClient:
    api_key: str
    base_url: httpx.URL
    timeout: httpx.Timeout
    max_retries: int
    _owns_http: bool

    def __init__(
        self,
        *,
        api_key: str | None,
        base_url: str | httpx.URL | None,
        timeout: float | httpx.Timeout | None,
        max_retries: int,
        default_headers: Mapping[str, str] | None,
    ) -> None:
        api_key = api_key or os.environ.get("NX_API_KEY")
        if not api_key:
            raise NxError("No API key: pass api_key= or set NX_API_KEY.")
        self.api_key = api_key
        self.base_url = httpx.URL(str(base_url or os.environ.get("NX_BASE_URL") or DEFAULT_BASE_URL).rstrip("/") + "/")
        if timeout is None:
            self.timeout = DEFAULT_TIMEOUT
        elif isinstance(timeout, httpx.Timeout):
            self.timeout = timeout
        else:
            self.timeout = httpx.Timeout(timeout)
        self.max_retries = max_retries
        self._default_headers = dict(default_headers or {})

    def _bind_resources(self) -> None:
        raise NotImplementedError

    @property
    def default_headers(self) -> dict[str, str]:
        return {
            "Authorization": f"Bearer {self.api_key}",
            "Accept": "application/json",
            "User-Agent": f"nvisionx-python/{__version__}",
            **self._default_headers,
        }

    def _prepare(self, options: RequestOptions) -> RequestOptions:
        if options.method == "GET" or options.idempotency_key:
            return options
        return replace(options, idempotency_key=f"nx-py-{uuid.uuid4()}")

    def _build_request(self, http: httpx.Client | httpx.AsyncClient, options: RequestOptions) -> httpx.Request:
        headers = {**self.default_headers, **options.headers}
        if options.idempotency_key:
            headers["Idempotency-Key"] = options.idempotency_key
        return http.build_request(
            options.method,
            self.base_url.join(options.path.lstrip("/")),
            params=drop_none(options.params) if options.params else None,
            json=options.json,
            data=options.data,
            files=options.files,
            headers=headers,
            timeout=options.timeout if options.timeout and self.timeout is DEFAULT_TIMEOUT else self.timeout,
        )

    def _should_retry(self, response: httpx.Response) -> bool:
        return response.status_code in RETRYABLE_STATUSES

    def _retry_delay(self, attempt: int, response: httpx.Response | None) -> float:
        if response is not None:
            retry_after = parse_retry_after(response)
            if retry_after is not None and retry_after <= MAX_RETRY_AFTER:
                return retry_after
        delay = min(INITIAL_RETRY_DELAY * 2.0**attempt, MAX_RETRY_DELAY)
        return delay * (1 - 0.25 * random.random())

    @staticmethod
    def _rewindable(options: RequestOptions) -> bool:
        if not options.files:
            return True
        for _, (_, content, _) in options.files:
            if not isinstance(content, bytes) and not (hasattr(content, "seek") and _seekable(content)):
                return False
        return True

    @staticmethod
    def _rewind(options: RequestOptions) -> None:
        for _, (_, content, _) in options.files or []:
            if not isinstance(content, bytes):
                content.seek(0)


def _seekable(content: IO[bytes]) -> bool:
    try:
        return bool(content.seekable())
    except (AttributeError, OSError, ValueError):
        return False


def parse(cast_to: type[ModelT], response: httpx.Response) -> ModelT:
    return cast_to.model_validate(response.json())
