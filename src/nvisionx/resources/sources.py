from __future__ import annotations

from collections.abc import Sequence
from typing import Any, Literal

from nvisionx._base_client import RequestOptions, drop_none, path
from nvisionx._models import (
    AppGrant,
    AppGrantList,
    Deleted,
    Provider,
    SelectionPreview,
    Source,
    SourceAuthorization,
    SourceEstate,
    SourceList,
    SourceMode,
    SourceNode,
    SourceNodeList,
    SourceRun,
    SourceRunList,
    SourceSelection,
    SyncSchedule,
)
from nvisionx._pagination import AsyncPaginator, SyncPage
from nvisionx.resources._resource import AsyncResource, SyncResource

SelectionMode = Literal["all", "custom"]


def _source(source_id: str, suffix: str = "") -> str:
    return path("v1/sources/{id}", id=source_id) + suffix


def _selection_body(
    mode: SelectionMode,
    include: Sequence[str] | None,
    exclude: Sequence[str] | None,
    include_new_sites: bool | None,
    include_onedrive: bool | None,
) -> dict[str, Any]:
    return drop_none(
        {
            "mode": mode,
            "include": list(include) if include is not None else None,
            "exclude": list(exclude) if exclude is not None else None,
            "include_new_sites": include_new_sites,
            "include_onedrive": include_onedrive,
        }
    )


def _nodes_params(
    parent: str | None, q: str | None, files: bool | None, limit: int | None, cursor: str | None
) -> dict[str, Any]:
    return {
        "parent": parent,
        "q": q,
        "files": None if files is None else str(files).lower(),
        "limit": limit,
        "cursor": cursor,
    }


class Authorizations(SyncResource):
    def create(
        self, *, provider: Provider, mode: SourceMode | None = None, redirect_uri: str | None = None
    ) -> SourceAuthorization:
        body = drop_none({"provider": provider, "mode": mode, "redirect_uri": redirect_uri})
        return self._client.request(RequestOptions("POST", "v1/sources/authorizations", json=body), SourceAuthorization)

    def get(self, authorization_id: str) -> SourceAuthorization:
        options = RequestOptions("GET", path("v1/sources/authorizations/{id}", id=authorization_id))
        return self._client.request(options, SourceAuthorization)

    def verify(self, authorization_id: str, **fields: str) -> SourceAuthorization:
        options = RequestOptions(
            "POST", path("v1/sources/authorizations/{id}/verify", id=authorization_id), json=fields
        )
        return self._client.request(options, SourceAuthorization)


class AppGrants(SyncResource):
    def list(self, source_id: str) -> AppGrantList:
        return self._client.request(RequestOptions("GET", _source(source_id, "/app-grants")), AppGrantList)

    def create(self, source_id: str, *, redirect_uri: str) -> AppGrant:
        options = RequestOptions("POST", _source(source_id, "/app-grants"), json={"redirect_uri": redirect_uri})
        return self._client.request(options, AppGrant)

    def verify(self, source_id: str, grant_id: str, **fields: str) -> AppGrant:
        suffix = path("/app-grants/{id}/verify", id=grant_id)
        return self._client.request(RequestOptions("POST", _source(source_id, suffix), json=fields), AppGrant)


class Sources(SyncResource):
    @property
    def authorizations(self) -> Authorizations:
        return Authorizations(self._client)

    @property
    def app_grants(self) -> AppGrants:
        return AppGrants(self._client)

    def list(self) -> SourceList:
        return self._client.request(RequestOptions("GET", "v1/sources"), SourceList)

    def create(self, *, authorization_id: str, schedule: SyncSchedule, name: str | None = None) -> Source:
        body = drop_none({"authorization_id": authorization_id, "schedule": schedule, "name": name})
        return self._client.request(RequestOptions("POST", "v1/sources", json=body), Source)

    def get(self, source_id: str) -> Source:
        return self._client.request(RequestOptions("GET", _source(source_id)), Source)

    def update(self, source_id: str, *, name: str | None = None, schedule: SyncSchedule | None = None) -> Source:
        body = drop_none({"name": name, "schedule": schedule})
        return self._client.request(RequestOptions("PATCH", _source(source_id), json=body), Source)

    def delete(self, source_id: str) -> Deleted:
        return self._client.request(RequestOptions("DELETE", _source(source_id)), Deleted)

    def sync(self, source_id: str) -> Source:
        return self._client.request(RequestOptions("POST", _source(source_id, "/sync")), Source)

    def estate(self, source_id: str) -> SourceEstate:
        return self._client.request(RequestOptions("GET", _source(source_id, "/estate")), SourceEstate)

    def nodes(
        self,
        source_id: str,
        *,
        parent: str | None = None,
        q: str | None = None,
        files: bool | None = None,
        limit: int | None = None,
        cursor: str | None = None,
    ) -> SyncPage[SourceNode]:
        params = _nodes_params(parent, q, files, limit, cursor)
        return self._paginate(_source(source_id, "/nodes"), params, SourceNodeList)

    def runs(self, source_id: str, *, limit: int | None = None, cursor: str | None = None) -> SyncPage[SourceRun]:
        return self._paginate(_source(source_id, "/runs"), {"limit": limit, "cursor": cursor}, SourceRunList)

    def get_selection(self, source_id: str) -> SourceSelection:
        return self._client.request(RequestOptions("GET", _source(source_id, "/selection")), SourceSelection)

    def update_selection(
        self,
        source_id: str,
        *,
        mode: SelectionMode,
        include: Sequence[str] | None = None,
        exclude: Sequence[str] | None = None,
        include_new_sites: bool | None = None,
        include_onedrive: bool | None = None,
    ) -> SourceSelection:
        body = _selection_body(mode, include, exclude, include_new_sites, include_onedrive)
        return self._client.request(RequestOptions("PUT", _source(source_id, "/selection"), json=body), SourceSelection)

    def preview_selection(
        self,
        source_id: str,
        *,
        mode: SelectionMode,
        include: Sequence[str] | None = None,
        exclude: Sequence[str] | None = None,
        include_new_sites: bool | None = None,
        include_onedrive: bool | None = None,
    ) -> SelectionPreview:
        body = _selection_body(mode, include, exclude, include_new_sites, include_onedrive)
        return self._client.request(
            RequestOptions("POST", _source(source_id, "/selection/preview"), json=body), SelectionPreview
        )


class AsyncAuthorizations(AsyncResource):
    async def create(
        self, *, provider: Provider, mode: SourceMode | None = None, redirect_uri: str | None = None
    ) -> SourceAuthorization:
        body = drop_none({"provider": provider, "mode": mode, "redirect_uri": redirect_uri})
        return await self._client.request(
            RequestOptions("POST", "v1/sources/authorizations", json=body), SourceAuthorization
        )

    async def get(self, authorization_id: str) -> SourceAuthorization:
        options = RequestOptions("GET", path("v1/sources/authorizations/{id}", id=authorization_id))
        return await self._client.request(options, SourceAuthorization)

    async def verify(self, authorization_id: str, **fields: str) -> SourceAuthorization:
        options = RequestOptions(
            "POST", path("v1/sources/authorizations/{id}/verify", id=authorization_id), json=fields
        )
        return await self._client.request(options, SourceAuthorization)


class AsyncAppGrants(AsyncResource):
    async def list(self, source_id: str) -> AppGrantList:
        return await self._client.request(RequestOptions("GET", _source(source_id, "/app-grants")), AppGrantList)

    async def create(self, source_id: str, *, redirect_uri: str) -> AppGrant:
        options = RequestOptions("POST", _source(source_id, "/app-grants"), json={"redirect_uri": redirect_uri})
        return await self._client.request(options, AppGrant)

    async def verify(self, source_id: str, grant_id: str, **fields: str) -> AppGrant:
        suffix = path("/app-grants/{id}/verify", id=grant_id)
        return await self._client.request(RequestOptions("POST", _source(source_id, suffix), json=fields), AppGrant)


class AsyncSources(AsyncResource):
    @property
    def authorizations(self) -> AsyncAuthorizations:
        return AsyncAuthorizations(self._client)

    @property
    def app_grants(self) -> AsyncAppGrants:
        return AsyncAppGrants(self._client)

    async def list(self) -> SourceList:
        return await self._client.request(RequestOptions("GET", "v1/sources"), SourceList)

    async def create(self, *, authorization_id: str, schedule: SyncSchedule, name: str | None = None) -> Source:
        body = drop_none({"authorization_id": authorization_id, "schedule": schedule, "name": name})
        return await self._client.request(RequestOptions("POST", "v1/sources", json=body), Source)

    async def get(self, source_id: str) -> Source:
        return await self._client.request(RequestOptions("GET", _source(source_id)), Source)

    async def update(self, source_id: str, *, name: str | None = None, schedule: SyncSchedule | None = None) -> Source:
        body = drop_none({"name": name, "schedule": schedule})
        return await self._client.request(RequestOptions("PATCH", _source(source_id), json=body), Source)

    async def delete(self, source_id: str) -> Deleted:
        return await self._client.request(RequestOptions("DELETE", _source(source_id)), Deleted)

    async def sync(self, source_id: str) -> Source:
        return await self._client.request(RequestOptions("POST", _source(source_id, "/sync")), Source)

    async def estate(self, source_id: str) -> SourceEstate:
        return await self._client.request(RequestOptions("GET", _source(source_id, "/estate")), SourceEstate)

    def nodes(
        self,
        source_id: str,
        *,
        parent: str | None = None,
        q: str | None = None,
        files: bool | None = None,
        limit: int | None = None,
        cursor: str | None = None,
    ) -> AsyncPaginator[SourceNode]:
        params = _nodes_params(parent, q, files, limit, cursor)
        return self._paginate(_source(source_id, "/nodes"), params, SourceNodeList)

    def runs(self, source_id: str, *, limit: int | None = None, cursor: str | None = None) -> AsyncPaginator[SourceRun]:
        return self._paginate(_source(source_id, "/runs"), {"limit": limit, "cursor": cursor}, SourceRunList)

    async def get_selection(self, source_id: str) -> SourceSelection:
        return await self._client.request(RequestOptions("GET", _source(source_id, "/selection")), SourceSelection)

    async def update_selection(
        self,
        source_id: str,
        *,
        mode: SelectionMode,
        include: Sequence[str] | None = None,
        exclude: Sequence[str] | None = None,
        include_new_sites: bool | None = None,
        include_onedrive: bool | None = None,
    ) -> SourceSelection:
        body = _selection_body(mode, include, exclude, include_new_sites, include_onedrive)
        return await self._client.request(
            RequestOptions("PUT", _source(source_id, "/selection"), json=body), SourceSelection
        )

    async def preview_selection(
        self,
        source_id: str,
        *,
        mode: SelectionMode,
        include: Sequence[str] | None = None,
        exclude: Sequence[str] | None = None,
        include_new_sites: bool | None = None,
        include_onedrive: bool | None = None,
    ) -> SelectionPreview:
        body = _selection_body(mode, include, exclude, include_new_sites, include_onedrive)
        return await self._client.request(
            RequestOptions("POST", _source(source_id, "/selection/preview"), json=body), SelectionPreview
        )
