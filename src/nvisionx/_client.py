from __future__ import annotations

import asyncio
import copy
import time
from collections.abc import Mapping
from types import TracebackType
from typing import TypeVar

import httpx

from nvisionx._base_client import (
    DEFAULT_MAX_RETRIES,
    BaseClient,
    ModelT,
    RequestOptions,
    parse,
)
from nvisionx._errors import APIConnectionError, APITimeoutError, error_from_response
from nvisionx.resources.agents import Agents, AsyncAgents
from nvisionx.resources.billing import AsyncBilling, Billing
from nvisionx.resources.budgets import AsyncBudgets, Budgets
from nvisionx.resources.chat import AsyncChat, Chat
from nvisionx.resources.documents import AsyncDocuments, Documents
from nvisionx.resources.jobs import AsyncJobs, Jobs
from nvisionx.resources.mcp import AsyncMcp, Mcp
from nvisionx.resources.search import AsyncSearch, Search
from nvisionx.resources.sources import AsyncSources, Sources

SelfT = TypeVar("SelfT", bound=BaseClient)


def _with_options(
    client: SelfT,
    api_key: str | None,
    base_url: str | httpx.URL | None,
    timeout: float | httpx.Timeout | None,
    max_retries: int | None,
    default_headers: Mapping[str, str] | None,
) -> SelfT:
    clone = copy.copy(client)
    if api_key is not None:
        clone.api_key = api_key
    if base_url is not None:
        clone.base_url = httpx.URL(str(base_url).rstrip("/") + "/")
    if timeout is not None:
        clone.timeout = timeout if isinstance(timeout, httpx.Timeout) else httpx.Timeout(timeout)
    if max_retries is not None:
        clone.max_retries = max_retries
    if default_headers is not None:
        clone._default_headers = {**client._default_headers, **default_headers}
    clone._owns_http = False
    clone._bind_resources()
    return clone


class Nx(BaseClient):
    documents: Documents
    jobs: Jobs
    search: Search
    sources: Sources
    mcp: Mcp
    agents: Agents
    chat: Chat
    billing: Billing
    budgets: Budgets

    def __init__(
        self,
        *,
        api_key: str | None = None,
        base_url: str | httpx.URL | None = None,
        timeout: float | httpx.Timeout | None = None,
        max_retries: int = DEFAULT_MAX_RETRIES,
        default_headers: Mapping[str, str] | None = None,
        http_client: httpx.Client | None = None,
    ) -> None:
        super().__init__(
            api_key=api_key,
            base_url=base_url,
            timeout=timeout,
            max_retries=max_retries,
            default_headers=default_headers,
        )
        self._http = http_client or httpx.Client(follow_redirects=True)
        self._owns_http = http_client is None
        self._bind_resources()

    def _bind_resources(self) -> None:
        self.documents = Documents(self)
        self.jobs = Jobs(self)
        self.search = Search(self)
        self.sources = Sources(self)
        self.mcp = Mcp(self)
        self.agents = Agents(self)
        self.chat = Chat(self)
        self.billing = Billing(self)
        self.budgets = Budgets(self)

    def with_options(
        self,
        *,
        api_key: str | None = None,
        base_url: str | httpx.URL | None = None,
        timeout: float | httpx.Timeout | None = None,
        max_retries: int | None = None,
        default_headers: Mapping[str, str] | None = None,
    ) -> Nx:
        return _with_options(self, api_key, base_url, timeout, max_retries, default_headers)

    def send(self, options: RequestOptions, *, stream: bool = False) -> httpx.Response:
        options = self._prepare(options)
        rewindable = self._rewindable(options)
        attempt = 0
        while True:
            request = self._build_request(self._http, options)
            retry = attempt < self.max_retries and rewindable
            response: httpx.Response | None = None
            try:
                response = self._http.send(request, stream=stream)
            except httpx.TimeoutException as exc:
                if not retry:
                    raise APITimeoutError(request=request) from exc
            except httpx.TransportError as exc:
                if not retry:
                    raise APIConnectionError(str(exc) or "Connection error.", request=request) from exc
            if response is not None:
                if response.is_success:
                    return response
                if not (retry and self._should_retry(response)):
                    if stream:
                        response.read()
                        response.close()
                    raise error_from_response(response)
                response.close()

            time.sleep(self._retry_delay(attempt, response))
            self._rewind(options)
            attempt += 1

    def request(self, options: RequestOptions, cast_to: type[ModelT]) -> ModelT:
        return parse(cast_to, self.send(options))

    def close(self) -> None:
        if self._owns_http:
            self._http.close()

    def __enter__(self) -> Nx:
        return self

    def __exit__(
        self, exc_type: type[BaseException] | None, exc: BaseException | None, tb: TracebackType | None
    ) -> None:
        self.close()


class AsyncNx(BaseClient):
    documents: AsyncDocuments
    jobs: AsyncJobs
    search: AsyncSearch
    sources: AsyncSources
    mcp: AsyncMcp
    agents: AsyncAgents
    chat: AsyncChat
    billing: AsyncBilling
    budgets: AsyncBudgets

    def __init__(
        self,
        *,
        api_key: str | None = None,
        base_url: str | httpx.URL | None = None,
        timeout: float | httpx.Timeout | None = None,
        max_retries: int = DEFAULT_MAX_RETRIES,
        default_headers: Mapping[str, str] | None = None,
        http_client: httpx.AsyncClient | None = None,
    ) -> None:
        super().__init__(
            api_key=api_key,
            base_url=base_url,
            timeout=timeout,
            max_retries=max_retries,
            default_headers=default_headers,
        )
        self._http = http_client or httpx.AsyncClient(follow_redirects=True)
        self._owns_http = http_client is None
        self._bind_resources()

    def _bind_resources(self) -> None:
        self.documents = AsyncDocuments(self)
        self.jobs = AsyncJobs(self)
        self.search = AsyncSearch(self)
        self.sources = AsyncSources(self)
        self.mcp = AsyncMcp(self)
        self.agents = AsyncAgents(self)
        self.chat = AsyncChat(self)
        self.billing = AsyncBilling(self)
        self.budgets = AsyncBudgets(self)

    def with_options(
        self,
        *,
        api_key: str | None = None,
        base_url: str | httpx.URL | None = None,
        timeout: float | httpx.Timeout | None = None,
        max_retries: int | None = None,
        default_headers: Mapping[str, str] | None = None,
    ) -> AsyncNx:
        return _with_options(self, api_key, base_url, timeout, max_retries, default_headers)

    async def send(self, options: RequestOptions, *, stream: bool = False) -> httpx.Response:
        options = self._prepare(options)
        rewindable = self._rewindable(options)
        attempt = 0
        while True:
            request = self._build_request(self._http, options)
            retry = attempt < self.max_retries and rewindable
            response: httpx.Response | None = None
            try:
                response = await self._http.send(request, stream=stream)
            except httpx.TimeoutException as exc:
                if not retry:
                    raise APITimeoutError(request=request) from exc
            except httpx.TransportError as exc:
                if not retry:
                    raise APIConnectionError(str(exc) or "Connection error.", request=request) from exc
            if response is not None:
                if response.is_success:
                    return response
                if not (retry and self._should_retry(response)):
                    if stream:
                        await response.aread()
                        await response.aclose()
                    raise error_from_response(response)
                await response.aclose()

            await asyncio.sleep(self._retry_delay(attempt, response))
            self._rewind(options)
            attempt += 1

    async def request(self, options: RequestOptions, cast_to: type[ModelT]) -> ModelT:
        return parse(cast_to, await self.send(options))

    async def close(self) -> None:
        if self._owns_http:
            await self._http.aclose()

    async def __aenter__(self) -> AsyncNx:
        return self

    async def __aexit__(
        self, exc_type: type[BaseException] | None, exc: BaseException | None, tb: TracebackType | None
    ) -> None:
        await self.close()
