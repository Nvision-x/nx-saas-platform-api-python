from __future__ import annotations

from collections.abc import Sequence

from nvisionx._base_client import AGENT_TIMEOUT, RequestOptions, drop_none
from nvisionx._models import AgentRun, AgentSession, AgentSessionList, McpToolName
from nvisionx._pagination import AsyncPaginator, SyncPage
from nvisionx.resources._resource import AsyncResource, SyncResource


def _run_options(
    instructions: str,
    tools: Sequence[McpToolName] | None,
    sources: Sequence[str] | None,
    max_tool_calls: int | None,
) -> RequestOptions:
    body = drop_none(
        {
            "instructions": instructions,
            "tools": list(tools) if tools is not None else None,
            "sources": list(sources) if sources is not None else None,
            "max_tool_calls": max_tool_calls,
        }
    )
    return RequestOptions("POST", "v1/agents/runs", json=body, timeout=AGENT_TIMEOUT)


class Agents(SyncResource):
    def run(
        self,
        instructions: str,
        *,
        tools: Sequence[McpToolName] | None = None,
        sources: Sequence[str] | None = None,
        max_tool_calls: int | None = None,
    ) -> AgentRun:
        return self._client.request(_run_options(instructions, tools, sources, max_tool_calls), AgentRun)

    def sessions(self, *, limit: int | None = None, cursor: str | None = None) -> SyncPage[AgentSession]:
        return self._paginate("v1/agents/sessions", {"limit": limit, "cursor": cursor}, AgentSessionList)


class AsyncAgents(AsyncResource):
    async def run(
        self,
        instructions: str,
        *,
        tools: Sequence[McpToolName] | None = None,
        sources: Sequence[str] | None = None,
        max_tool_calls: int | None = None,
    ) -> AgentRun:
        return await self._client.request(_run_options(instructions, tools, sources, max_tool_calls), AgentRun)

    def sessions(self, *, limit: int | None = None, cursor: str | None = None) -> AsyncPaginator[AgentSession]:
        return self._paginate("v1/agents/sessions", {"limit": limit, "cursor": cursor}, AgentSessionList)
