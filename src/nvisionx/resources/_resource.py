from __future__ import annotations

from collections.abc import Callable, Mapping
from typing import TYPE_CHECKING, Any

from nvisionx._base_client import RequestOptions
from nvisionx._pagination import AsyncPage, AsyncPaginator, SyncPage

if TYPE_CHECKING:
    from nvisionx._client import AsyncNx, Nx

OptionsFor = Callable[[str | None], RequestOptions]


def _get(path: str, params: Mapping[str, Any]) -> OptionsFor:
    return lambda cursor: RequestOptions("GET", path, params={**params, "cursor": cursor})


class SyncResource:
    def __init__(self, client: Nx) -> None:
        self._client = client

    def _paginate(self, path: str, params: Mapping[str, Any], cast_to: type[Any]) -> SyncPage[Any]:
        return self._pages(_get(path, params), cast_to, params.get("cursor"))

    def _pages(self, options: OptionsFor, cast_to: type[Any], cursor: str | None, items: str = "data") -> SyncPage[Any]:
        def fetch(cursor: str | None) -> SyncPage[Any]:
            body = self._client.request(options(cursor), cast_to)
            return SyncPage(list(getattr(body, items)), body.next_cursor, fetch, body)

        return fetch(cursor)


class AsyncResource:
    def __init__(self, client: AsyncNx) -> None:
        self._client = client

    def _paginate(self, path: str, params: Mapping[str, Any], cast_to: type[Any]) -> AsyncPaginator[Any]:
        return self._pages(_get(path, params), cast_to, params.get("cursor"))

    def _pages(
        self, options: OptionsFor, cast_to: type[Any], cursor: str | None, items: str = "data"
    ) -> AsyncPaginator[Any]:
        async def fetch(cursor: str | None) -> AsyncPage[Any]:
            body = await self._client.request(options(cursor), cast_to)
            return AsyncPage(list(getattr(body, items)), body.next_cursor, fetch, body)

        return AsyncPaginator(lambda: fetch(cursor))
