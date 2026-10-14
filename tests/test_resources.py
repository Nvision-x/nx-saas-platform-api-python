from __future__ import annotations

import io
import json
from pathlib import Path
from typing import Any

import httpx
import pytest
import respx

from nvisionx import AsyncNx, JobTimeoutError, NotFoundError, Nx, StreamError
from nvisionx._base_client import AGENT_TIMEOUT
from nvisionx.resources import jobs as jobs_module
from nvisionx.types import BudgetScope, SearchFilters

from .conftest import chat_message, conversation, error, job


def body(route: respx.Route) -> Any:
    return json.loads(route.calls.last.request.content)


def sse(*events: dict[str, Any]) -> bytes:
    return "".join(f"data: {json.dumps(e)}\n\n" for e in events).encode()


def test_ingest_url(client: Nx, api: respx.MockRouter) -> None:
    route = api.post("/v1/documents").respond(202, json=job())
    result = client.documents.ingest(url="https://example.com/msa.pdf", metadata={"department": "legal"})
    assert result.id == "job_1"
    assert body(route) == {"url": "https://example.com/msa.pdf", "metadata": {"department": "legal"}}


def test_ingest_files(client: Nx, api: respx.MockRouter, tmp_path: Path) -> None:
    pdf = tmp_path / "msa.pdf"
    pdf.write_bytes(b"%PDF-1.7")
    route = api.post("/v1/documents").respond(202, json=job(documents=3))

    client.documents.ingest(
        file=[pdf, ("notes.txt", b"renewal due"), io.BytesIO(b"raw")],
        metadata={"department": "legal"},
        classify=False,
    )

    request = route.calls.last.request
    assert request.headers["Content-Type"].startswith("multipart/form-data")
    content = request.content
    assert content.count(b'name="file"') == 3
    assert b'filename="msa.pdf"' in content
    assert b"Content-Type: application/pdf" in content
    assert b'filename="notes.txt"' in content
    assert b"%PDF-1.7" in content
    assert b'{"department": "legal"}' in content
    assert b'name="classify"\r\n\r\nfalse' in content


def test_ingest_closes_files_it_opened(client: Nx, api: respx.MockRouter, tmp_path: Path) -> None:
    pdf = tmp_path / "a.pdf"
    pdf.write_bytes(b"x")
    api.post("/v1/documents").respond(400, json=error("invalid_request", "Unsupported."))
    opened: list[Any] = []
    real_open = Path.open

    def spy(self: Path, *args: Any, **kwargs: Any) -> Any:
        handle = real_open(self, *args, **kwargs)
        opened.append(handle)
        return handle

    with pytest.MonkeyPatch.context() as mp:
        mp.setattr(Path, "open", spy)
        with pytest.raises(Exception, match="Unsupported"):
            client.documents.ingest(file=str(pdf))
    assert opened
    assert all(h.closed for h in opened)


@pytest.mark.usefixtures("no_retry_delay")
def test_ingest_upload_retry_resends_the_file(client: Nx, api: respx.MockRouter) -> None:
    route = api.post("/v1/documents").mock(side_effect=[httpx.Response(503), httpx.Response(202, json=job())])
    client.documents.ingest(file=io.BytesIO(b"payload-bytes"))
    assert route.call_count == 2
    assert all(b"payload-bytes" in call.request.content for call in route.calls)


def test_ingest_requires_exactly_one_input(client: Nx) -> None:
    with pytest.raises(TypeError):
        client.documents.ingest()
    with pytest.raises(TypeError):
        client.documents.ingest(url="https://example.com/a.pdf", file=b"x")


def test_jobs_wait_polls_until_done(client: Nx, api: respx.MockRouter, monkeypatch: pytest.MonkeyPatch) -> None:
    sleeps: list[float] = []
    monkeypatch.setattr(jobs_module.time, "sleep", sleeps.append)
    api.get("/v1/jobs/job_1").mock(
        side_effect=[
            httpx.Response(200, json=job(status="queued")),
            httpx.Response(200, json=job(status="running", progress=50)),
            httpx.Response(200, json=job(status="completed", progress=100, record_types=["contract"])),
        ]
    )
    result = client.jobs.wait("job_1", poll_interval=0.5)
    assert result.status == "completed"
    assert result.record_types == ["contract"]
    assert sleeps == [0.5, 0.5]


def test_jobs_wait_returns_failed_jobs(client: Nx, api: respx.MockRouter) -> None:
    api.get("/v1/jobs/job_1").respond(json=job(status="failed", error="Unreadable PDF"))
    assert client.jobs.wait("job_1").error == "Unreadable PDF"


def test_jobs_wait_times_out(client: Nx, api: respx.MockRouter, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(jobs_module.time, "sleep", lambda _: None)
    api.get("/v1/jobs/job_1").respond(json=job(status="running"))
    with pytest.raises(JobTimeoutError):
        client.jobs.wait("job_1", poll_interval=1.0, timeout=0.5)


def test_list_paginates(client: Nx, api: respx.MockRouter) -> None:
    route = api.get("/v1/jobs").mock(
        side_effect=[
            httpx.Response(200, json={"data": [job(id="job_1"), job(id="job_2")], "next_cursor": "c2"}),
            httpx.Response(200, json={"data": [job(id="job_3")], "next_cursor": None}),
        ]
    )
    page = client.jobs.list(status="completed", limit=2)
    assert [j.id for j in page.data] == ["job_1", "job_2"]
    assert page.has_next_page()
    assert [j.id for j in page] == ["job_1", "job_2", "job_3"]
    first, second = route.calls
    assert first.request.url.params == httpx.QueryParams({"status": "completed", "limit": "2"})
    assert second.request.url.params == httpx.QueryParams({"status": "completed", "limit": "2", "cursor": "c2"})


def test_search_with_filters_model(client: Nx, api: respx.MockRouter) -> None:
    route = api.post("/v1/search").respond(json={"took_ms": 4, "total": 0, "results": []})
    client.search("termination", mode="keyword", filters=SearchFilters(record_type=["contract"]))
    assert body(route) == {"query": "termination", "mode": "keyword", "filters": {"record_type": ["contract"]}}


def test_agents_run_uses_long_timeout(client: Nx, api: respx.MockRouter) -> None:
    route = api.post("/v1/agents/runs").respond(
        json={"run_id": "run_1", "status": "completed", "tool_calls": 2, "cost_usd": 0.01, "answer": "Two."}
    )
    run = client.agents.run("Which contracts?", tools=["search_records"], max_tool_calls=5)
    assert run.answer == "Two."
    assert body(route) == {"instructions": "Which contracts?", "tools": ["search_records"], "max_tool_calls": 5}
    assert route.calls.last.request.extensions["timeout"]["read"] == AGENT_TIMEOUT.read


def test_explicit_client_timeout_wins(api: respx.MockRouter) -> None:
    route = api.post("/v1/agents/runs").respond(
        json={"run_id": "run_1", "status": "completed", "tool_calls": 0, "cost_usd": 0}
    )
    with Nx(api_key="k", base_url="https://api.test.example", timeout=12.0) as nx:
        nx.agents.run("x")
    assert route.calls.last.request.extensions["timeout"]["read"] == 12.0


def test_chat_conversation_lifecycle(client: Nx, api: respx.MockRouter) -> None:
    create = api.post("/v1/chat/conversations").respond(201, json=conversation())
    update = api.patch("/v1/chat/conversations/conv_1").respond(json=conversation(title="Renamed"))
    delete = api.delete("/v1/chat/conversations/conv_1").respond(json={"id": "conv_1", "deleted": True})

    assert client.chat.conversations.create(sources=["src_1"]).id == "conv_1"
    assert body(create) == {"sources": ["src_1"]}
    assert client.chat.conversations.update("conv_1", title="Renamed").title == "Renamed"
    assert body(update) == {"title": "Renamed"}
    assert client.chat.conversations.delete("conv_1").deleted is True
    assert delete.called


def test_chat_message(client: Nx, api: respx.MockRouter) -> None:
    route = api.post("/v1/chat/conversations/conv_1/messages").respond(json=chat_message())
    message = client.chat.messages.create("conv_1", content="Which contracts?")
    assert message.role == "assistant"
    assert route.calls.last.request.headers["Accept"] == "application/json"


def test_chat_stream(client: Nx, api: respx.MockRouter) -> None:
    route = api.post("/v1/chat/conversations/conv_1/messages").respond(
        headers={"Content-Type": "text/event-stream"},
        content=sse(
            {"type": "status", "status": "Searching records"},
            {"type": "delta", "text": "Two contracts "},
            {"type": "delta", "text": "cap indemnity."},
            {"type": "complete", "message": chat_message(content="Two contracts cap indemnity.")},
        ),
    )
    with client.chat.messages.stream("conv_1", content="Which?") as stream:
        text = "".join(stream.text_stream)
        message = stream.until_done()
    assert text == "Two contracts cap indemnity."
    assert message.content == "Two contracts cap indemnity."
    assert route.calls.last.request.headers["Accept"] == "text/event-stream"


def test_chat_stream_events(client: Nx, api: respx.MockRouter) -> None:
    api.post("/v1/chat/conversations/conv_1/messages").respond(
        content=b": keep-alive\n\n"
        + sse({"type": "status", "status": "Thinking"}, {"type": "complete", "message": chat_message()})
    )
    stream = client.chat.messages.stream("conv_1", content="Hi")
    assert [e.type for e in stream] == ["status", "complete"]
    assert stream.message is not None
    assert stream.response.is_closed


def test_chat_stream_error_event(client: Nx, api: respx.MockRouter) -> None:
    api.post("/v1/chat/conversations/conv_1/messages").respond(
        content=sse({"type": "delta", "text": "Par"}, {"type": "error", "error": "Agent failed."})
    )
    with pytest.raises(StreamError, match="Agent failed"), client.chat.messages.stream("conv_1", content="Hi") as s:
        s.until_done()


def test_chat_stream_http_error(client: Nx, api: respx.MockRouter) -> None:
    api.post("/v1/chat/conversations/conv_9/messages").respond(404, json=error("not_found", "No conversation."))
    with pytest.raises(NotFoundError, match="No conversation"):
        client.chat.messages.stream("conv_9", content="Hi")


def test_chat_stream_without_complete(client: Nx, api: respx.MockRouter) -> None:
    api.post("/v1/chat/conversations/conv_1/messages").respond(content=sse({"type": "delta", "text": "x"}))
    with pytest.raises(StreamError, match="without a complete"):
        client.chat.messages.stream("conv_1", content="Hi").until_done()


def test_sources(client: Nx, api: respx.MockRouter) -> None:
    selection = api.put("/v1/sources/src_1/selection").respond(
        json={"mode": "custom", "include": ["site:a"], "files": 10, "bytes": 2048, "updated_at": None}
    )
    nodes = api.get("/v1/sources/src_1/nodes").respond(json={"data": [], "next_cursor": None})
    verify = api.post("/v1/sources/authorizations/auth_1/verify").respond(
        json={"id": "auth_1", "provider": "sharepoint", "mode": "tenant", "status": "verified"}
    )

    client.sources.update_selection("src_1", mode="custom", include=["site:a"])
    assert body(selection) == {"mode": "custom", "include": ["site:a"]}
    assert list(client.sources.nodes("src_1", q="contracts", files=True)) == []
    assert nodes.calls.last.request.url.params == httpx.QueryParams({"q": "contracts", "files": "true"})
    client.sources.authorizations.verify("auth_1", code="abc", state="xyz")
    assert body(verify) == {"code": "abc", "state": "xyz"}


def test_mcp_update_tool(client: Nx, api: respx.MockRouter) -> None:
    route = api.patch("/v1/mcp/tools/ingest_document").respond(
        json={"name": "ingest_document", "description": "Ingest.", "scope": "ingest:write", "enabled": False}
    )
    assert client.mcp.update_tool("ingest_document", enabled=False).enabled is False
    assert body(route) == {"enabled": False}


def test_budgets_create(client: Nx, api: respx.MockRouter) -> None:
    route = api.post("/v1/budgets").respond(
        201,
        json={
            "id": "bud_1",
            "name": "Search cap",
            "scope": {"type": "meter", "meter": "search"},
            "type": "soft",
            "limit_usd": 100,
            "spent_usd": 0,
            "alert_thresholds": [80],
            "notify": [],
            "blocking": False,
            "created_at": "2026-10-01T12:00:00Z",
        },
    )
    client.budgets.create(scope=BudgetScope(type="meter", meter="search"), type="soft", limit_usd=100)
    assert body(route) == {"scope": {"type": "meter", "meter": "search"}, "type": "soft", "limit_usd": 100}


def test_billing_usage_period(client: Nx, api: respx.MockRouter) -> None:
    route = api.get("/v1/billing/usage").respond(404, json=error("not_found", "No such period."))
    with pytest.raises(NotFoundError):
        client.billing.usage(period="2026-09")
    assert route.calls.last.request.url.params["period"] == "2026-09"


async def test_async_search(async_client: AsyncNx, api: respx.MockRouter) -> None:
    api.post("/v1/search").respond(json={"took_ms": 2, "total": 0, "results": []})
    response = await async_client.search("cap")
    assert response.total == 0


async def test_async_pagination(async_client: AsyncNx, api: respx.MockRouter) -> None:
    api.get("/v1/chat/conversations").mock(
        side_effect=[
            httpx.Response(200, json={"data": [conversation(id="conv_1")], "next_cursor": "n"}),
            httpx.Response(200, json={"data": [conversation(id="conv_2")], "next_cursor": None}),
        ]
    )
    ids = [c.id async for c in async_client.chat.conversations.list()]
    assert ids == ["conv_1", "conv_2"]


async def test_async_page_await(async_client: AsyncNx, api: respx.MockRouter) -> None:
    api.get("/v1/jobs").respond(json={"data": [job()], "next_cursor": None})
    page = await async_client.jobs.list()
    assert [j.id for j in page.data] == ["job_1"]
    assert not page.has_next_page()
    assert await page.next_page() is None


@pytest.mark.usefixtures("no_retry_delay")
async def test_async_retries(async_client: AsyncNx, api: respx.MockRouter) -> None:
    route = api.get("/v1/jobs/job_1").mock(side_effect=[httpx.Response(500), httpx.Response(200, json=job())])
    assert (await async_client.jobs.get("job_1")).id == "job_1"
    assert route.call_count == 2


async def test_async_errors(async_client: AsyncNx, api: respx.MockRouter) -> None:
    api.get("/v1/jobs/job_x").respond(404, json=error("not_found", "No such job."))
    with pytest.raises(NotFoundError):
        await async_client.jobs.get("job_x")


async def test_async_ingest_file(async_client: AsyncNx, api: respx.MockRouter) -> None:
    route = api.post("/v1/documents").respond(202, json=job())
    await async_client.documents.ingest(file=("a.txt", b"hello"))
    assert b"hello" in route.calls.last.request.content


async def test_async_jobs_wait(async_client: AsyncNx, api: respx.MockRouter, monkeypatch: pytest.MonkeyPatch) -> None:
    async def no_sleep(_: float) -> None:
        return None

    monkeypatch.setattr(jobs_module.asyncio, "sleep", no_sleep)
    api.get("/v1/jobs/job_1").mock(
        side_effect=[httpx.Response(200, json=job(status="running")), httpx.Response(200, json=job(status="completed"))]
    )
    assert (await async_client.jobs.wait("job_1")).status == "completed"


async def test_async_chat_stream(async_client: AsyncNx, api: respx.MockRouter) -> None:
    api.post("/v1/chat/conversations/conv_1/messages").respond(
        content=sse(
            {"type": "delta", "text": "Hello "},
            {"type": "delta", "text": "there"},
            {"type": "complete", "message": chat_message(content="Hello there")},
        )
    )
    stream = await async_client.chat.messages.stream("conv_1", content="Hi")
    async with stream:
        text = "".join([t async for t in stream.text_stream])
    assert text == "Hello there"
    assert stream.message is not None
    assert stream.message.content == "Hello there"


async def test_async_chat_stream_until_done(async_client: AsyncNx, api: respx.MockRouter) -> None:
    api.post("/v1/chat/conversations/conv_1/messages").respond(
        content=sse(
            {"type": "step", "step": {"summary": "Searched 3 records"}},
            {"type": "complete", "message": chat_message()},
        )
    )
    stream = await async_client.chat.messages.stream("conv_1", content="Hi")
    message = await stream.until_done()
    assert message.id == "msg_1"
