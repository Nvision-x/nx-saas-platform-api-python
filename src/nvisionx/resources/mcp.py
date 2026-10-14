from __future__ import annotations

from nvisionx._base_client import RequestOptions, path
from nvisionx._models import McpServer, McpTool, McpToolName
from nvisionx.resources._resource import AsyncResource, SyncResource


def _tool(tool_name: McpToolName, enabled: bool) -> RequestOptions:
    return RequestOptions("PATCH", path("v1/mcp/tools/{name}", name=tool_name), json={"enabled": enabled})


class Mcp(SyncResource):
    def get(self) -> McpServer:
        return self._client.request(RequestOptions("GET", "v1/mcp"), McpServer)

    def update_tool(self, tool_name: McpToolName, *, enabled: bool) -> McpTool:
        return self._client.request(_tool(tool_name, enabled), McpTool)


class AsyncMcp(AsyncResource):
    async def get(self) -> McpServer:
        return await self._client.request(RequestOptions("GET", "v1/mcp"), McpServer)

    async def update_tool(self, tool_name: McpToolName, *, enabled: bool) -> McpTool:
        return await self._client.request(_tool(tool_name, enabled), McpTool)
