from __future__ import annotations

from collections.abc import Sequence
from typing import Any, Literal

from nvisionx._base_client import RequestOptions, drop_none, path
from nvisionx._models import Budget, BudgetList, BudgetScope, Deleted
from nvisionx.resources._resource import AsyncResource, SyncResource

AlertThreshold = Literal[50, 80, 100]


def _budget(budget_id: str) -> str:
    return path("v1/budgets/{id}", id=budget_id)


def _create_body(
    scope: BudgetScope | dict[str, Any],
    type: Literal["soft", "hard"],
    limit_usd: float,
    name: str | None,
    alert_thresholds: Sequence[AlertThreshold] | None,
    notify: Sequence[str] | None,
) -> dict[str, Any]:
    if isinstance(scope, BudgetScope):
        scope = scope.model_dump(mode="json", exclude_none=True)
    return drop_none(
        {
            "scope": scope,
            "type": type,
            "limit_usd": limit_usd,
            "name": name,
            "alert_thresholds": list(alert_thresholds) if alert_thresholds is not None else None,
            "notify": list(notify) if notify is not None else None,
        }
    )


def _update_body(
    name: str | None,
    limit_usd: float | None,
    alert_thresholds: Sequence[AlertThreshold] | None,
    notify: Sequence[str] | None,
) -> dict[str, Any]:
    return drop_none(
        {
            "name": name,
            "limit_usd": limit_usd,
            "alert_thresholds": list(alert_thresholds) if alert_thresholds is not None else None,
            "notify": list(notify) if notify is not None else None,
        }
    )


class Budgets(SyncResource):
    def list(self) -> BudgetList:
        return self._client.request(RequestOptions("GET", "v1/budgets"), BudgetList)

    def create(
        self,
        *,
        scope: BudgetScope | dict[str, Any],
        type: Literal["soft", "hard"],
        limit_usd: float,
        name: str | None = None,
        alert_thresholds: Sequence[AlertThreshold] | None = None,
        notify: Sequence[str] | None = None,
    ) -> Budget:
        body = _create_body(scope, type, limit_usd, name, alert_thresholds, notify)
        return self._client.request(RequestOptions("POST", "v1/budgets", json=body), Budget)

    def update(
        self,
        budget_id: str,
        *,
        name: str | None = None,
        limit_usd: float | None = None,
        alert_thresholds: Sequence[AlertThreshold] | None = None,
        notify: Sequence[str] | None = None,
    ) -> Budget:
        body = _update_body(name, limit_usd, alert_thresholds, notify)
        return self._client.request(RequestOptions("PATCH", _budget(budget_id), json=body), Budget)

    def delete(self, budget_id: str) -> Deleted:
        return self._client.request(RequestOptions("DELETE", _budget(budget_id)), Deleted)


class AsyncBudgets(AsyncResource):
    async def list(self) -> BudgetList:
        return await self._client.request(RequestOptions("GET", "v1/budgets"), BudgetList)

    async def create(
        self,
        *,
        scope: BudgetScope | dict[str, Any],
        type: Literal["soft", "hard"],
        limit_usd: float,
        name: str | None = None,
        alert_thresholds: Sequence[AlertThreshold] | None = None,
        notify: Sequence[str] | None = None,
    ) -> Budget:
        body = _create_body(scope, type, limit_usd, name, alert_thresholds, notify)
        return await self._client.request(RequestOptions("POST", "v1/budgets", json=body), Budget)

    async def update(
        self,
        budget_id: str,
        *,
        name: str | None = None,
        limit_usd: float | None = None,
        alert_thresholds: Sequence[AlertThreshold] | None = None,
        notify: Sequence[str] | None = None,
    ) -> Budget:
        body = _update_body(name, limit_usd, alert_thresholds, notify)
        return await self._client.request(RequestOptions("PATCH", _budget(budget_id), json=body), Budget)

    async def delete(self, budget_id: str) -> Deleted:
        return await self._client.request(RequestOptions("DELETE", _budget(budget_id)), Deleted)
