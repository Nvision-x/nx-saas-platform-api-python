# NVISIONx Nx Platform Python library

[![CI](https://github.com/Nvision-x/nx-saas-platform-api-python/actions/workflows/ci.yml/badge.svg)](https://github.com/Nvision-x/nx-saas-platform-api-python/actions/workflows/ci.yml)

The official Python client for the [NVISIONx Nx Platform](https://platform.us.nvisionx.ai) API. Nx turns the documents in your data
estate into **business records** (record type, owner, sensitivity, retention), makes them searchable, and exposes them
to agents.

This library covers the data plane, which is everything an API token can call: ingest, jobs, search, hosted agents,
chat, data sources, MCP settings, usage and budgets. It ships typed models, sync and async clients, automatic retries,
cursor pagination and streaming chat.

## Install

```sh
pip install nvisionx
```

Python 3.10 or newer.

## Quickstart

Create an API token in the Nx console under **API tokens**. A token belongs to one workspace, and every call made with
it acts on that workspace.

```sh
export NX_API_KEY="nx_live_…"
```

```python
from nvisionx import Nx

nx = Nx()

job = nx.documents.ingest(file="Northwind_MSA_2024.pdf", metadata={"department": "legal"})
job = nx.jobs.wait(job.id)
print(job.status, job.record_types)

results = nx.search("indemnification cap in vendor contracts", limit=5)
for result in results.results:
    print(result.title, result.record_type, result.score)
```

## Configuration

```python
from nvisionx import Nx

nx = Nx(
    api_key="nx_live_…",
    timeout=30.0,
    max_retries=3,
)
```

| Option | Environment variable | Default |
| --- | --- | --- |
| `api_key` | `NX_API_KEY` | required |
| `base_url` | `NX_BASE_URL` | `https://platform.us.nvisionx.ai` |
| `timeout` | | 60 s; 300 s for agent runs and chat answers; no write timeout for uploads |
| `max_retries` | | 2 |
| `default_headers` | | |
| `http_client` | | your own `httpx.Client` / `httpx.AsyncClient` (proxies, transports, limits) |

`with_options` returns a copy that shares the connection pool:

```python
nx.with_options(timeout=120.0, max_retries=0).search("retention schedule")
```

## Ingest

Pass `url=` for a document Nx should fetch, or `file=` to upload. `file=` accepts a path, bytes, an open binary file,
a `(filename, content)` or `(filename, content, content_type)` tuple, or a list of any of these.

```python
job = nx.documents.ingest(url="https://files.example.com/signed/msa.pdf")

job = nx.documents.ingest(
    file=["contracts/msa.pdf", ("notes.txt", b"Renewal due Q3", "text/plain")],
    metadata={"department": "legal"},
    classify=True,
)

job = nx.jobs.wait(job.id, poll_interval=2.0, timeout=600.0)
if job.status == "completed":
    for doc in job.classified or []:
        print(doc)
```

`jobs.wait` returns the job once it is `completed` or `failed`, and raises `JobTimeoutError` if it is neither by the
timeout.

## Search

```python
from nvisionx.types import SearchFilters

response = nx.search(
    "termination for convenience",
    mode="hybrid",
    filters=SearchFilters(record_type=["contract"], sensitivity=["confidential"]),
    limit=10,
)
```

`filters` also accepts a plain `dict`.

## Chat

Conversations keep context across questions. Answers cite records with `[n]` markers that match
`citations[].marker`.

```python
conversation = nx.chat.conversations.create(title="Vendor risk")

answer = nx.chat.messages.create(conversation.id, content="Which vendor contracts cap indemnity below $2M?")
print(answer.content)
for citation in answer.citations or []:
    print(citation.marker, citation.title)
```

Stream the answer as the agent works:

```python
with nx.chat.messages.stream(conversation.id, content="Summarize the Northwind MSA") as stream:
    for text in stream.text_stream:
        print(text, end="", flush=True)
    message = stream.until_done()
```

Iterate the stream itself to see every `ChatStreamEvent`: `status`, `step`, `delta` and `complete`. A failed answer
raises `StreamError`.

## Agents

```python
run = nx.agents.run(
    "Which vendor contracts cap indemnity below $2M?",
    tools=["search_records", "get_record"],
    max_tool_calls=10,
)
print(run.answer, run.citations, run.cost_usd)
```

## MCP

To connect an agent framework to Nx over the [Model Context Protocol](https://modelcontextprotocol.io), use the
official `mcp` package with the hosted endpoint and your token:

```python
from mcp import ClientSession
from mcp.client.streamable_http import streamablehttp_client

async with streamablehttp_client(
    "https://platform.us.nvisionx.ai/mcp", headers={"Authorization": f"Bearer {api_key}"}
) as (read, write, _):
    async with ClientSession(read, write) as session:
        await session.initialize()
        tools = await session.list_tools()
```

This library manages the workspace's MCP server:

```python
server = nx.mcp.get()
nx.mcp.update_tool("ingest_document", enabled=False)
```

## Data sources

```python
for source in nx.sources.list().data:
    print(source.name, source.provider, source.status)

nx.sources.sync("src_123")
estate = nx.sources.estate("src_123")
for node in nx.sources.nodes("src_123", q="contracts"):
    print(node)
```

Connecting a new source is an OAuth consent flow: `sources.authorizations.create`, send the person to the returned
URL, then `sources.authorizations.verify` with the callback parameters and `sources.create`.

## Usage and budgets

```python
usage = nx.billing.usage(period="2026-10")
print(usage.total_usd, usage.forecast_usd)

nx.budgets.create(scope={"type": "workspace"}, type="soft", limit_usd=500, alert_thresholds=[50, 80, 100])
```

## Pagination

List methods return a page. Iterating a page fetches the following pages as needed:

```python
for job in nx.jobs.list(status="completed"):
    print(job.id)

page = nx.jobs.list(limit=20)
print(page.data, page.next_cursor)
if page.has_next_page():
    page = page.next_page()
```

## Async

`AsyncNx` has the same surface:

```python
import asyncio
from nvisionx import AsyncNx


async def main() -> None:
    async with AsyncNx() as nx:
        results = await nx.search("data processing agreement")

        async for job in nx.jobs.list():
            print(job.id)

        page = await nx.jobs.list(limit=10)

        stream = await nx.chat.messages.stream("conv_123", content="What changed in the MSA?")
        async with stream:
            async for text in stream.text_stream:
                print(text, end="")


asyncio.run(main())
```

## Errors

Every non-2xx response raises a subclass of `APIStatusError`. Each one carries `status_code`, `type` (the API's error
type), `message`, `detail` (the full typed error body) and `response`.

| Status | Exception | Error types |
| --- | --- | --- |
| 400, 413 | `BadRequestError` | `invalid_request` |
| 401 | `AuthenticationError` | `unauthenticated` |
| 402 | `PaymentRequiredError` | `budget_exceeded`, `spend_limit_reached`, `insufficient_balance` |
| 403 | `PermissionDeniedError` | `insufficient_scope`, `permission_denied` |
| 404 | `NotFoundError` | `not_found` |
| 409 | `ConflictError` | `conflict` |
| 422 | `UnprocessableEntityError` | `unprocessable` |
| 429 | `RateLimitError` | `rate_limited` |
| 5xx | `InternalServerError` | `internal_error` |

Network failures raise `APIConnectionError` (or `APITimeoutError`). Everything derives from `NxError`.

```python
from nvisionx import PaymentRequiredError, PermissionDeniedError

try:
    nx.search("board minutes")
except PermissionDeniedError as e:
    print("token is missing scope", e.required_scope)
except PaymentRequiredError as e:
    print(e.type, e.detail.resolve if e.detail else e.message)
```

## Retries and idempotency

Connection errors, timeouts, 408, 429 and 5xx responses are retried up to `max_retries` times. Retries back off
exponentially, or wait as long as the `Retry-After` header says (up to 60 s). Every `POST`, `PUT`, `PATCH` and `DELETE`
sends an `Idempotency-Key`, and the key stays the same across retries, so a retried write is never applied twice. To
control the key yourself, for example to deduplicate across processes, pass it to `ingest`:

```python
nx.documents.ingest(url=url, idempotency_key=f"ingest-{document_id}")
```

## Models

Responses are [Pydantic](https://docs.pydantic.dev) models, and every model is importable from `nvisionx.types`. Fields
the API adds after a release are kept: read them with `model.model_extra` or `model.model_dump()`.

## Development

```sh
python -m venv .venv && source .venv/bin/activate
pip install -e . --group dev
make check
```

The models in `src/nvisionx/_models.py` and the exports in `src/nvisionx/types.py` are generated from
`openapi/openapi.yaml`, so don't edit them by hand. Run `make generate` after changing the spec.

## License

[MIT](LICENSE)
