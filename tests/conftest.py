from __future__ import annotations

from collections.abc import AsyncIterator, Iterator
from typing import Any

import pytest
import respx

from nvisionx import AsyncNx, Nx
from nvisionx._base_client import BaseClient

BASE_URL = "https://api.test.example"
API_KEY = "nx_test_abc123_secret"


def job(**overrides: Any) -> dict[str, Any]:
    return {
        "id": "job_1",
        "source": "api",
        "documents": 1,
        "status": "queued",
        "progress": 0,
        "record_types": [],
        "created_at": "2026-10-01T12:00:00Z",
        **overrides,
    }


def conversation(**overrides: Any) -> dict[str, Any]:
    return {
        "id": "conv_1",
        "title": "Vendor indemnity",
        "sources": [],
        "message_count": 0,
        "last_message_preview": None,
        "created_at": "2026-10-01T12:00:00Z",
        "updated_at": "2026-10-01T12:00:00Z",
        **overrides,
    }


def chat_message(**overrides: Any) -> dict[str, Any]:
    return {
        "id": "msg_1",
        "role": "assistant",
        "content": "Two contracts cap indemnity below $2M [1].",
        "created_at": "2026-10-01T12:00:00Z",
        **overrides,
    }


def error(type: str, message: str, **extra: Any) -> dict[str, Any]:
    return {"error": {"type": type, "message": message, **extra}}


@pytest.fixture(autouse=True)
def _no_env(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("NX_API_KEY", raising=False)
    monkeypatch.delenv("NX_BASE_URL", raising=False)


@pytest.fixture
def no_retry_delay(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(BaseClient, "_retry_delay", lambda self, attempt, response: 0.0)


@pytest.fixture
def api() -> Iterator[respx.MockRouter]:
    with respx.mock(base_url=BASE_URL, assert_all_called=False) as router:
        yield router


@pytest.fixture
def client(api: respx.MockRouter) -> Iterator[Nx]:
    with Nx(api_key=API_KEY, base_url=BASE_URL) as nx:
        yield nx


@pytest.fixture
async def async_client(api: respx.MockRouter) -> AsyncIterator[AsyncNx]:
    async with AsyncNx(api_key=API_KEY, base_url=BASE_URL) as nx:
        yield nx
