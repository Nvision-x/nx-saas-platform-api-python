from __future__ import annotations

from collections.abc import Sequence
from typing import Any, Literal

from nvisionx._base_client import RequestOptions, drop_none
from nvisionx._models import Filters, SearchResponse
from nvisionx.resources._resource import AsyncResource, SyncResource

SearchMode = Literal["hybrid", "semantic", "keyword"]


def _search_options(
    query: str,
    sources: Sequence[str] | None,
    mode: SearchMode | None,
    filters: Filters | dict[str, Any] | None,
    limit: int | None,
) -> RequestOptions:
    if isinstance(filters, Filters):
        filters = filters.model_dump(mode="json", exclude_none=True)
    body = drop_none(
        {
            "query": query,
            "sources": list(sources) if sources is not None else None,
            "mode": mode,
            "filters": filters,
            "limit": limit,
        }
    )
    return RequestOptions("POST", "v1/search", json=body)


class Search(SyncResource):
    def __call__(
        self,
        query: str,
        *,
        sources: Sequence[str] | None = None,
        mode: SearchMode | None = None,
        filters: Filters | dict[str, Any] | None = None,
        limit: int | None = None,
    ) -> SearchResponse:
        return self._client.request(_search_options(query, sources, mode, filters, limit), SearchResponse)


class AsyncSearch(AsyncResource):
    async def __call__(
        self,
        query: str,
        *,
        sources: Sequence[str] | None = None,
        mode: SearchMode | None = None,
        filters: Filters | dict[str, Any] | None = None,
        limit: int | None = None,
    ) -> SearchResponse:
        return await self._client.request(_search_options(query, sources, mode, filters, limit), SearchResponse)
