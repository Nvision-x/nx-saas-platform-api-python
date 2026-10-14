from __future__ import annotations

import json

import httpx
import pytest
import respx
from pydantic import ValidationError

from nvisionx import (
    DEFAULT_BASE_URL,
    APIConnectionError,
    APIStatusError,
    APITimeoutError,
    AuthenticationError,
    BadRequestError,
    InternalServerError,
    NotFoundError,
    Nx,
    NxError,
    PaymentRequiredError,
    PermissionDeniedError,
    RateLimitError,
    __version__,
)
from nvisionx._base_client import MAX_RETRY_DELAY

from .conftest import API_KEY, BASE_URL, error, job


def test_requires_api_key() -> None:
    with pytest.raises(NxError, match="NX_API_KEY"):
        Nx()


def test_reads_environment(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("NX_API_KEY", "nx_live_env")
    monkeypatch.setenv("NX_BASE_URL", "https://nx.internal.example/")
    nx = Nx()
    assert nx.api_key == "nx_live_env"
    assert str(nx.base_url) == "https://nx.internal.example/"


def test_default_base_url() -> None:
    assert str(Nx(api_key="k").base_url) == DEFAULT_BASE_URL + "/"


def test_sends_auth_and_user_agent(client: Nx, api: respx.MockRouter) -> None:
    route = api.get("/v1/jobs/job_1").respond(json=job())
    client.jobs.get("job_1")
    request = route.calls.last.request
    assert request.headers["Authorization"] == f"Bearer {API_KEY}"
    assert request.headers["User-Agent"] == f"nvisionx-python/{__version__}"
    assert "Idempotency-Key" not in request.headers


def test_base_url_with_path_prefix(api: respx.MockRouter) -> None:
    route = api.get("/prefix/v1/jobs/job_1").respond(json=job())
    with Nx(api_key="k", base_url=BASE_URL + "/prefix") as nx:
        nx.jobs.get("job_1")
    assert route.called


def test_path_params_are_escaped(client: Nx, api: respx.MockRouter) -> None:
    route = api.get(url__regex=r".*/v1/jobs/a%2Fb%3Fc$").respond(json=job(id="a/b?c"))
    assert client.jobs.get("a/b?c").id == "a/b?c"
    assert route.called


def test_default_headers_and_with_options(client: Nx, api: respx.MockRouter) -> None:
    route = api.get("/v1/jobs/job_1").respond(json=job())
    scoped = client.with_options(default_headers={"X-Trace": "t1"}, max_retries=0, timeout=5.0)
    scoped.jobs.get("job_1")
    assert route.calls.last.request.headers["X-Trace"] == "t1"
    assert scoped.max_retries == 0
    assert client.max_retries == 2
    assert scoped._http is client._http
    scoped.close()
    assert not client._http.is_closed


def test_mutations_send_idempotency_key(client: Nx, api: respx.MockRouter) -> None:
    route = api.post("/v1/documents").respond(202, json=job())
    client.documents.ingest(url="https://example.com/a.pdf")
    assert route.calls.last.request.headers["Idempotency-Key"].startswith("nx-py-")


@pytest.mark.usefixtures("no_retry_delay")
def test_retries_keep_the_idempotency_key(client: Nx, api: respx.MockRouter) -> None:
    route = api.post("/v1/documents").mock(
        side_effect=[httpx.Response(503), httpx.Response(502), httpx.Response(202, json=job())]
    )
    client.documents.ingest(url="https://example.com/a.pdf", idempotency_key="ingest-42")
    keys = {call.request.headers["Idempotency-Key"] for call in route.calls}
    assert route.call_count == 3
    assert keys == {"ingest-42"}


@pytest.mark.usefixtures("no_retry_delay")
def test_gives_up_after_max_retries(client: Nx, api: respx.MockRouter) -> None:
    route = api.get("/v1/jobs/job_1").respond(503, json=error("internal_error", "Try again."))
    with pytest.raises(InternalServerError) as excinfo:
        client.jobs.get("job_1")
    assert route.call_count == 3
    assert excinfo.value.status_code == 503
    assert excinfo.value.type == "internal_error"


@pytest.mark.usefixtures("no_retry_delay")
def test_rate_limit_is_retried(client: Nx, api: respx.MockRouter) -> None:
    route = api.get("/v1/jobs/job_1").mock(
        side_effect=[
            httpx.Response(429, headers={"Retry-After": "1"}, json=error("rate_limited", "Slow down.")),
            httpx.Response(200, json=job()),
        ]
    )
    assert client.jobs.get("job_1").id == "job_1"
    assert route.call_count == 2


def test_client_errors_are_not_retried(client: Nx, api: respx.MockRouter) -> None:
    route = api.post("/v1/search").respond(400, json=error("invalid_request", "query is empty", param="query"))
    with pytest.raises(BadRequestError) as excinfo:
        client.search("x")
    assert route.call_count == 1
    assert excinfo.value.detail is not None
    assert excinfo.value.detail.param == "query"
    assert str(excinfo.value) == "400 invalid_request: query is empty"


@pytest.mark.parametrize(
    ("status", "error_type", "exc"),
    [
        (401, "unauthenticated", AuthenticationError),
        (402, "budget_exceeded", PaymentRequiredError),
        (402, "insufficient_balance", PaymentRequiredError),
        (403, "insufficient_scope", PermissionDeniedError),
        (404, "not_found", NotFoundError),
    ],
)
def test_error_mapping(
    client: Nx, api: respx.MockRouter, status: int, error_type: str, exc: type[APIStatusError]
) -> None:
    api.post("/v1/search").respond(status, json=error(error_type, "Refused."))
    with pytest.raises(exc) as excinfo:
        client.search("contracts")
    assert excinfo.value.type == error_type
    assert excinfo.value.message == "Refused."


def test_insufficient_scope_exposes_required_scope(client: Nx, api: respx.MockRouter) -> None:
    api.post("/v1/search").respond(403, json=error("insufficient_scope", "Missing.", required_scope="search:read"))
    with pytest.raises(PermissionDeniedError) as excinfo:
        client.search("contracts")
    assert excinfo.value.required_scope == "search:read"


def test_rate_limit_error_exposes_retry_after(client: Nx, api: respx.MockRouter) -> None:
    api.post("/v1/search").respond(429, headers={"Retry-After": "7"}, json=error("rate_limited", "Slow down."))
    with pytest.raises(RateLimitError) as excinfo:
        client.with_options(max_retries=0).search("contracts")
    assert excinfo.value.retry_after == 7.0


def test_non_json_error_body(client: Nx, api: respx.MockRouter) -> None:
    api.get("/v1/jobs/job_1").respond(502, text="<html>Bad gateway</html>")
    with pytest.raises(InternalServerError) as excinfo:
        client.with_options(max_retries=0).jobs.get("job_1")
    assert excinfo.value.detail is None
    assert excinfo.value.type is None
    assert "Bad gateway" in excinfo.value.message


@pytest.mark.usefixtures("no_retry_delay")
def test_connection_errors(client: Nx, api: respx.MockRouter) -> None:
    route = api.get("/v1/jobs/job_1").mock(side_effect=httpx.ConnectError("refused"))
    with pytest.raises(APIConnectionError):
        client.jobs.get("job_1")
    assert route.call_count == 3


@pytest.mark.usefixtures("no_retry_delay")
def test_timeouts(client: Nx, api: respx.MockRouter) -> None:
    api.get("/v1/jobs/job_1").mock(side_effect=httpx.ReadTimeout("slow"))
    with pytest.raises(APITimeoutError):
        client.jobs.get("job_1")


@pytest.mark.usefixtures("no_retry_delay")
def test_recovers_from_a_connection_error(client: Nx, api: respx.MockRouter) -> None:
    api.get("/v1/jobs/job_1").mock(side_effect=[httpx.ConnectError("reset"), httpx.Response(200, json=job())])
    assert client.jobs.get("job_1").status == "queued"


def test_retry_delay_honours_retry_after() -> None:
    nx = Nx(api_key="k")
    response = httpx.Response(429, headers={"Retry-After": "3"})
    assert nx._retry_delay(0, response) == 3.0


def test_retry_delay_ignores_excessive_retry_after() -> None:
    nx = Nx(api_key="k")
    response = httpx.Response(429, headers={"Retry-After": "3600"})
    assert nx._retry_delay(0, response) <= MAX_RETRY_DELAY


def test_retry_delay_backs_off() -> None:
    nx = Nx(api_key="k")
    delays = [nx._retry_delay(attempt, None) for attempt in range(8)]
    assert all(0 < d <= MAX_RETRY_DELAY for d in delays)
    assert delays[3] > delays[0]


def test_unknown_response_fields_are_kept(client: Nx, api: respx.MockRouter) -> None:
    api.get("/v1/jobs/job_1").respond(json=job(new_field={"a": 1}))
    result = client.jobs.get("job_1")
    assert result.model_extra == {"new_field": {"a": 1}}


def test_unknown_enum_values_are_accepted(client: Nx, api: respx.MockRouter) -> None:
    api.get("/v1/jobs/job_1").respond(json=job(status="archived", source="onedrive"))
    result = client.jobs.get("job_1")
    assert result.status == "archived"
    assert result.source == "onedrive"


def test_invalid_values_are_still_rejected(client: Nx, api: respx.MockRouter) -> None:
    api.get("/v1/jobs/job_1").respond(json=job(progress="half", status=["queued"]))
    with pytest.raises(ValidationError) as excinfo:
        client.jobs.get("job_1")
    assert {e["loc"][0] for e in excinfo.value.errors()} == {"progress", "status"}


def test_request_body_is_json(client: Nx, api: respx.MockRouter) -> None:
    route = api.post("/v1/search").respond(json={"took_ms": 3, "total": 0, "results": []})
    client.search("cap", sources=["src_1"], limit=5)
    assert json.loads(route.calls.last.request.content) == {"query": "cap", "sources": ["src_1"], "limit": 5}
