from __future__ import annotations

from nvisionx._base_client import RequestOptions
from nvisionx._models import Usage
from nvisionx.resources._resource import AsyncResource, SyncResource


class Billing(SyncResource):
    def usage(self, *, period: str | None = None) -> Usage:
        return self._client.request(RequestOptions("GET", "v1/billing/usage", params={"period": period}), Usage)


class AsyncBilling(AsyncResource):
    async def usage(self, *, period: str | None = None) -> Usage:
        options = RequestOptions("GET", "v1/billing/usage", params={"period": period})
        return await self._client.request(options, Usage)
