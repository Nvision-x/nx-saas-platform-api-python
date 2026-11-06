from __future__ import annotations

from collections.abc import Sequence
from typing import Any, Literal

from nvisionx._base_client import RequestOptions, drop_none
from nvisionx._models import Filters, RegexOptions, SearchResponse
from nvisionx.resources._resource import AsyncResource, SyncResource

SearchMode = Literal["hybrid", "semantic", "keyword", "regex"]
DenseMode = Literal["auto", "full", "fast"]


def _search_options(
    query: str | None,
    sources: Sequence[str] | None,
    mode: SearchMode | None,
    regex: RegexOptions | dict[str, Any] | None,
    dense_mode: DenseMode | None,
    filters: Filters | dict[str, Any] | None,
    limit: int | None,
    cursor: str | None,
) -> RequestOptions:
    if isinstance(filters, Filters):
        filters = filters.model_dump(mode="json", exclude_none=True)
    if isinstance(regex, RegexOptions):
        regex = regex.model_dump(mode="json", exclude_unset=True)
    body = drop_none(
        {
            "query": query,
            "sources": list(sources) if sources is not None else None,
            "mode": mode,
            "regex": regex,
            "dense_mode": dense_mode,
            "filters": filters,
            "limit": limit,
            "cursor": cursor,
        }
    )
    return RequestOptions("POST", "v1/search", json=body)


class Search(SyncResource):
    def __call__(
        self,
        query: str | None = None,
        *,
        sources: Sequence[str] | None = None,
        mode: SearchMode | None = None,
        regex: RegexOptions | dict[str, Any] | None = None,
        dense_mode: DenseMode | None = None,
        filters: Filters | dict[str, Any] | None = None,
        limit: int | None = None,
        cursor: str | None = None,
    ) -> SearchResponse:
        options = _search_options(query, sources, mode, regex, dense_mode, filters, limit, cursor)
        return self._client.request(options, SearchResponse)


class AsyncSearch(AsyncResource):
    async def __call__(
        self,
        query: str | None = None,
        *,
        sources: Sequence[str] | None = None,
        mode: SearchMode | None = None,
        regex: RegexOptions | dict[str, Any] | None = None,
        dense_mode: DenseMode | None = None,
        filters: Filters | dict[str, Any] | None = None,
        limit: int | None = None,
        cursor: str | None = None,
    ) -> SearchResponse:
        options = _search_options(query, sources, mode, regex, dense_mode, filters, limit, cursor)
        return await self._client.request(options, SearchResponse)
