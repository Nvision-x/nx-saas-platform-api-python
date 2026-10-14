from __future__ import annotations

import json
from collections.abc import AsyncIterator, Iterable, Iterator
from types import TracebackType

import httpx

from nvisionx._errors import StreamError
from nvisionx._models import ChatMessage, ChatStreamEvent


class SSEDecoder:
    def __init__(self) -> None:
        self._data: list[str] = []

    def feed(self, line: str) -> str | None:
        line = line.rstrip("\r")
        if not line:
            if not self._data:
                return None
            data = "\n".join(self._data)
            self._data = []
            return data
        if line.startswith(":"):
            return None
        name, _, value = line.partition(":")
        if name == "data":
            self._data.append(value[1:] if value.startswith(" ") else value)
        return None

    def flush(self) -> str | None:
        return self.feed("")


def decode_sse(lines: Iterable[str]) -> Iterator[str]:
    decoder = SSEDecoder()
    for line in lines:
        data = decoder.feed(line)
        if data is not None:
            yield data
    data = decoder.flush()
    if data is not None:
        yield data


async def adecode_sse(lines: AsyncIterator[str]) -> AsyncIterator[str]:
    decoder = SSEDecoder()
    async for line in lines:
        data = decoder.feed(line)
        if data is not None:
            yield data
    data = decoder.flush()
    if data is not None:
        yield data


def _event(data: str) -> ChatStreamEvent:
    event = ChatStreamEvent.model_validate(json.loads(data))
    if event.type == "error":
        raise StreamError(event.error or "The answer failed.")
    return event


class ChatStream:
    def __init__(self, response: httpx.Response) -> None:
        self.response = response
        self.message: ChatMessage | None = None
        self._iterator = self._events()

    def _events(self) -> Iterator[ChatStreamEvent]:
        try:
            for data in decode_sse(self.response.iter_lines()):
                event = _event(data)
                if event.type == "complete":
                    self.message = event.message
                yield event
        finally:
            self.response.close()

    def __iter__(self) -> Iterator[ChatStreamEvent]:
        return self._iterator

    def __next__(self) -> ChatStreamEvent:
        return next(self._iterator)

    @property
    def text_stream(self) -> Iterator[str]:
        for event in self:
            if event.type == "delta" and event.text:
                yield event.text

    def until_done(self) -> ChatMessage:
        for _ in self:
            pass
        if self.message is None:
            raise StreamError("The stream ended without a complete event.")
        return self.message

    def close(self) -> None:
        self.response.close()

    def __enter__(self) -> ChatStream:
        return self

    def __exit__(
        self, exc_type: type[BaseException] | None, exc: BaseException | None, tb: TracebackType | None
    ) -> None:
        self.close()


class AsyncChatStream:
    def __init__(self, response: httpx.Response) -> None:
        self.response = response
        self.message: ChatMessage | None = None
        self._iterator = self._events()

    async def _events(self) -> AsyncIterator[ChatStreamEvent]:
        try:
            async for data in adecode_sse(self.response.aiter_lines()):
                event = _event(data)
                if event.type == "complete":
                    self.message = event.message
                yield event
        finally:
            await self.response.aclose()

    def __aiter__(self) -> AsyncIterator[ChatStreamEvent]:
        return self._iterator

    async def __anext__(self) -> ChatStreamEvent:
        return await self._iterator.__anext__()

    @property
    async def text_stream(self) -> AsyncIterator[str]:
        async for event in self:
            if event.type == "delta" and event.text:
                yield event.text

    async def until_done(self) -> ChatMessage:
        async for _ in self:
            pass
        if self.message is None:
            raise StreamError("The stream ended without a complete event.")
        return self.message

    async def close(self) -> None:
        await self.response.aclose()

    async def __aenter__(self) -> AsyncChatStream:
        return self

    async def __aexit__(
        self, exc_type: type[BaseException] | None, exc: BaseException | None, tb: TracebackType | None
    ) -> None:
        await self.close()
