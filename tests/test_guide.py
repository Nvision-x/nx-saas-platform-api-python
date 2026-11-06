from __future__ import annotations

from pathlib import Path
from typing import Any

import pytest
import respx

from .conftest import API_KEY, BASE_URL, chat_message, conversation, error, job


def source() -> dict[str, Any]:
    return {
        "id": "src_1",
        "provider": "sharepoint",
        "mode": "tenant",
        "name": "contoso.sharepoint.com",
        "detail": "3 sites",
        "schedule": "daily",
        "status": "healthy",
        "phase": "idle",
        "progress": 100,
        "documents": 10,
        "size_gb": 0.1,
        "selection_summary": None,
        "estate_summary": None,
        "created_at": "2026-10-01T12:00:00Z",
    }


@pytest.fixture
def platform(api: respx.MockRouter) -> respx.MockRouter:
    api.post("/v1/search").respond(json={"took_ms": 1, "total": 0, "total_is_lower_bound": False, "results": []})
    api.post("/v1/documents").respond(202, json=job())
    api.get("/v1/jobs/job_1").respond(json=job(status="completed"))
    api.get("/v1/sources").respond(json={"data": [source()]})
    api.post("/v1/chat/conversations").respond(201, json=conversation())
    api.post("/v1/chat/conversations/conv_1/messages").respond(json=chat_message())
    return api


def test_quickstart(platform: respx.MockRouter, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.chdir(tmp_path)
    (tmp_path / "msa.pdf").write_bytes(b"%PDF-1.7")

    from nvisionx import Nx

    nx = Nx(api_key=API_KEY, base_url=BASE_URL)

    results = nx.search("indemnification cap in vendor contracts", limit=5)
    for r in results.results:
        print(r.title, r.record_type, r.score)

    job = nx.documents.ingest(file="msa.pdf", metadata={"department": "legal"})
    job = nx.jobs.wait(job.id)

    for source in nx.sources.list().data:
        print(source.name, source.status)

    answer = nx.chat.messages.create(
        nx.chat.conversations.create(title="Vendor risk").id, content="Which contracts cap indemnity below $2M?"
    )
    print(answer.content)

    assert job.status == "completed"
    assert platform.calls.last.request.headers["Authorization"] == f"Bearer {API_KEY}"


def test_environment_and_workspace(platform: respx.MockRouter, monkeypatch: pytest.MonkeyPatch) -> None:
    from nvisionx import Nx

    monkeypatch.setenv("NX_API_KEY", API_KEY)
    monkeypatch.setenv("NX_BASE_URL", BASE_URL)
    nx = Nx()
    nx = nx.with_options(default_headers={"Nx-Workspace": "ws_legal"})
    nx.search("retention schedule")
    assert platform.calls.last.request.headers["Nx-Workspace"] == "ws_legal"

    finance = Nx(workspace="ws_finance")
    finance.search("retention schedule")
    assert platform.calls.last.request.headers["Nx-Workspace"] == "ws_finance"

    monkeypatch.setenv("NX_WORKSPACE", "ws_hr")
    Nx().search("retention schedule")
    assert platform.calls.last.request.headers["Nx-Workspace"] == "ws_hr"

    Nx().with_options(workspace="ws_ops").search("retention schedule")
    assert platform.calls.last.request.headers["Nx-Workspace"] == "ws_ops"


def test_find_text_in_documents(api: respx.MockRouter) -> None:
    from .test_resources import chunk, match, search_result

    api.post("/v1/search").respond(
        json={
            "took_ms": 1,
            "total": 1,
            "total_is_lower_bound": False,
            "results": [search_result(document_match_count=3, document_pattern_counts=[2, 1])],
        }
    )
    api.post("/v1/documents/doc_1/matches").respond(
        json={"document_id": "doc_1", "took_ms": 1, "matches": [match(0, 0, "SUBJ-0042")], "next_cursor": None}
    )
    api.get("/v1/documents/doc_1/chunks").respond(
        json={"document_id": "doc_1", "total": 1, "chunks": [chunk(0)], "next_cursor": None}
    )

    from nvisionx import Nx
    from nvisionx.types import RegexOptions

    nx = Nx(api_key=API_KEY, base_url=BASE_URL)

    hits = nx.search(
        mode="regex",
        regex=RegexOptions(patterns=[r"SUBJ-\d{4}", r"CASE-\d{6}"], require="all", passages_per_document=3),
    )
    for r in hits.results:
        print(r.id, r.document_match_count, r.document_pattern_counts)

    for m in nx.documents.matches(hits.results[0].id, patterns=[r"SUBJ-\d{4}", r"CASE-\d{6}"]):
        print(m.pattern, m.text, m.before, m.after)

    for c in nx.documents.chunks(hits.results[0].id):
        print(c.ordinal, c.section, c.text[:80])

    assert hits.results[0].document_pattern_counts == [2, 1]


async def test_async(platform: respx.MockRouter) -> None:
    from nvisionx import AsyncNx

    async with AsyncNx(api_key=API_KEY, base_url=BASE_URL) as nx:
        assert (await nx.search("data processing agreement")).total == 0
        assert [s.name for s in (await nx.sources.list()).data] == ["contoso.sharepoint.com"]


@pytest.mark.parametrize(
    ("status", "type", "name"),
    [
        (401, "unauthenticated", "AuthenticationError"),
        (403, "insufficient_scope", "PermissionDeniedError"),
        (402, "budget_exceeded", "PaymentRequiredError"),
        (429, "rate_limited", "RateLimitError"),
        (404, "not_found", "NotFoundError"),
        (409, "conflict", "ConflictError"),
    ],
)
def test_error_classes(api: respx.MockRouter, status: int, type: str, name: str) -> None:
    import nvisionx

    api.post("/v1/search").respond(status, json=error(type, "No."))
    nx = nvisionx.Nx(api_key=API_KEY, base_url=BASE_URL, max_retries=0)
    with pytest.raises(getattr(nvisionx, name)):
        nx.search("board minutes")
