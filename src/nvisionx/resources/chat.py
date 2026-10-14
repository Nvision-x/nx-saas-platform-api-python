from __future__ import annotations

from collections.abc import Sequence

from nvisionx._base_client import AGENT_TIMEOUT, RequestOptions, drop_none, path
from nvisionx._models import (
    ChatConversation,
    ChatConversationDetail,
    ChatConversationList,
    ChatMessage,
    Deleted,
)
from nvisionx._pagination import AsyncPaginator, SyncPage
from nvisionx._streaming import AsyncChatStream, ChatStream
from nvisionx.resources._resource import AsyncResource, SyncResource


def _conversation(conversation_id: str, suffix: str = "") -> str:
    return path("v1/chat/conversations/{id}", id=conversation_id) + suffix


def _conversation_body(title: str | None, sources: Sequence[str] | None) -> dict[str, object]:
    return drop_none({"title": title, "sources": list(sources) if sources is not None else None})


def _message_options(conversation_id: str, content: str, *, stream: bool) -> RequestOptions:
    return RequestOptions(
        "POST",
        _conversation(conversation_id, "/messages"),
        json={"content": content},
        headers={"Accept": "text/event-stream"} if stream else {},
        timeout=AGENT_TIMEOUT,
    )


class Conversations(SyncResource):
    def list(self, *, limit: int | None = None, cursor: str | None = None) -> SyncPage[ChatConversation]:
        return self._paginate("v1/chat/conversations", {"limit": limit, "cursor": cursor}, ChatConversationList)

    def create(self, *, title: str | None = None, sources: Sequence[str] | None = None) -> ChatConversation:
        options = RequestOptions("POST", "v1/chat/conversations", json=_conversation_body(title, sources))
        return self._client.request(options, ChatConversation)

    def get(self, conversation_id: str) -> ChatConversationDetail:
        return self._client.request(RequestOptions("GET", _conversation(conversation_id)), ChatConversationDetail)

    def update(
        self, conversation_id: str, *, title: str | None = None, sources: Sequence[str] | None = None
    ) -> ChatConversation:
        options = RequestOptions("PATCH", _conversation(conversation_id), json=_conversation_body(title, sources))
        return self._client.request(options, ChatConversation)

    def delete(self, conversation_id: str) -> Deleted:
        return self._client.request(RequestOptions("DELETE", _conversation(conversation_id)), Deleted)


class Messages(SyncResource):
    def create(self, conversation_id: str, *, content: str) -> ChatMessage:
        return self._client.request(_message_options(conversation_id, content, stream=False), ChatMessage)

    def stream(self, conversation_id: str, *, content: str) -> ChatStream:
        response = self._client.send(_message_options(conversation_id, content, stream=True), stream=True)
        return ChatStream(response)


class Chat(SyncResource):
    @property
    def conversations(self) -> Conversations:
        return Conversations(self._client)

    @property
    def messages(self) -> Messages:
        return Messages(self._client)


class AsyncConversations(AsyncResource):
    def list(self, *, limit: int | None = None, cursor: str | None = None) -> AsyncPaginator[ChatConversation]:
        return self._paginate("v1/chat/conversations", {"limit": limit, "cursor": cursor}, ChatConversationList)

    async def create(self, *, title: str | None = None, sources: Sequence[str] | None = None) -> ChatConversation:
        options = RequestOptions("POST", "v1/chat/conversations", json=_conversation_body(title, sources))
        return await self._client.request(options, ChatConversation)

    async def get(self, conversation_id: str) -> ChatConversationDetail:
        options = RequestOptions("GET", _conversation(conversation_id))
        return await self._client.request(options, ChatConversationDetail)

    async def update(
        self, conversation_id: str, *, title: str | None = None, sources: Sequence[str] | None = None
    ) -> ChatConversation:
        options = RequestOptions("PATCH", _conversation(conversation_id), json=_conversation_body(title, sources))
        return await self._client.request(options, ChatConversation)

    async def delete(self, conversation_id: str) -> Deleted:
        return await self._client.request(RequestOptions("DELETE", _conversation(conversation_id)), Deleted)


class AsyncMessages(AsyncResource):
    async def create(self, conversation_id: str, *, content: str) -> ChatMessage:
        return await self._client.request(_message_options(conversation_id, content, stream=False), ChatMessage)

    async def stream(self, conversation_id: str, *, content: str) -> AsyncChatStream:
        response = await self._client.send(_message_options(conversation_id, content, stream=True), stream=True)
        return AsyncChatStream(response)


class AsyncChat(AsyncResource):
    @property
    def conversations(self) -> AsyncConversations:
        return AsyncConversations(self._client)

    @property
    def messages(self) -> AsyncMessages:
        return AsyncMessages(self._client)
