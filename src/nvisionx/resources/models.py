from __future__ import annotations

from nvisionx._base_client import RequestOptions
from nvisionx._models import ModelList
from nvisionx.resources._resource import AsyncResource, SyncResource


class Models(SyncResource):
    def list(self) -> ModelList:
        return self._client.request(RequestOptions("GET", "v1/models"), ModelList)


class AsyncModels(AsyncResource):
    async def list(self) -> ModelList:
        return await self._client.request(RequestOptions("GET", "v1/models"), ModelList)
