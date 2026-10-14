from __future__ import annotations

from collections.abc import Mapping
from typing import TYPE_CHECKING, Any

from nvisionx._base_client import RequestOptions
from nvisionx._pagination import AsyncPage, AsyncPaginator, SyncPage

if TYPE_CHECKING:
    from nvisionx._client import AsyncNx, Nx


class SyncResource:
    def __init__(self, client: Nx) -> None:
        self._client = client

    def _paginate(self, path: str, params: Mapping[str, Any], cast_to: type[Any]) -> SyncPage[Any]:
        def fetch(cursor: str | None) -> SyncPage[Any]:
            body = self._client.request(RequestOptions("GET", path, params={**params, "cursor": cursor}), cast_to)
            return SyncPage(list(body.data), body.next_cursor, fetch)

        return fetch(params.get("cursor"))


class AsyncResource:
    def __init__(self, client: AsyncNx) -> None:
        self._client = client

    def _paginate(self, path: str, params: Mapping[str, Any], cast_to: type[Any]) -> AsyncPaginator[Any]:
        async def fetch(cursor: str | None) -> AsyncPage[Any]:
            body = await self._client.request(RequestOptions("GET", path, params={**params, "cursor": cursor}), cast_to)
            return AsyncPage(list(body.data), body.next_cursor, fetch)

        return AsyncPaginator(lambda: fetch(params.get("cursor")))
