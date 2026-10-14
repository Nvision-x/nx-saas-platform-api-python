from __future__ import annotations

from collections.abc import AsyncIterator, Awaitable, Callable, Generator, Iterator
from typing import Any, Generic, TypeVar

T = TypeVar("T")


class SyncPage(Generic[T]):
    def __init__(self, data: list[T], next_cursor: str | None, fetch: Callable[[str], SyncPage[T]]) -> None:
        self.data = data
        self.next_cursor = next_cursor
        self._fetch = fetch

    def has_next_page(self) -> bool:
        return bool(self.next_cursor)

    def next_page(self) -> SyncPage[T] | None:
        return self._fetch(self.next_cursor) if self.next_cursor else None

    def iter_pages(self) -> Iterator[SyncPage[T]]:
        page: SyncPage[T] | None = self
        while page is not None:
            yield page
            page = page.next_page()

    def __iter__(self) -> Iterator[T]:
        for page in self.iter_pages():
            yield from page.data

    def __repr__(self) -> str:
        return f"SyncPage(data={self.data!r}, next_cursor={self.next_cursor!r})"


class AsyncPage(Generic[T]):
    def __init__(self, data: list[T], next_cursor: str | None, fetch: Callable[[str], Awaitable[AsyncPage[T]]]) -> None:
        self.data = data
        self.next_cursor = next_cursor
        self._fetch = fetch

    def has_next_page(self) -> bool:
        return bool(self.next_cursor)

    async def next_page(self) -> AsyncPage[T] | None:
        return await self._fetch(self.next_cursor) if self.next_cursor else None

    async def iter_pages(self) -> AsyncIterator[AsyncPage[T]]:
        page: AsyncPage[T] | None = self
        while page is not None:
            yield page
            page = await page.next_page()

    async def __aiter__(self) -> AsyncIterator[T]:
        async for page in self.iter_pages():
            for item in page.data:
                yield item

    def __repr__(self) -> str:
        return f"AsyncPage(data={self.data!r}, next_cursor={self.next_cursor!r})"


class AsyncPaginator(Generic[T]):
    def __init__(self, first: Callable[[], Awaitable[AsyncPage[T]]]) -> None:
        self._first = first

    def __await__(self) -> Generator[Any, None, AsyncPage[T]]:
        return self._first().__await__()

    async def __aiter__(self) -> AsyncIterator[T]:
        page = await self._first()
        async for item in page:
            yield item
