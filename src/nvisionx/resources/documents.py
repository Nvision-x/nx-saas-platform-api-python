from __future__ import annotations

import json
from collections.abc import Mapping, Sequence
from datetime import datetime
from typing import IO, Any

from nvisionx._base_client import UPLOAD_TIMEOUT, RequestOptions, drop_none, path
from nvisionx._files import FilesInput, to_httpx_files
from nvisionx._models import (
    Deleted,
    Document,
    DocumentDeleteResult,
    DocumentDetail,
    DocumentFilter,
    DocumentList,
    DocumentParsed,
    DocumentStatusFilter,
    DocumentSummary,
    Job,
)
from nvisionx._pagination import AsyncPaginator, SyncPage
from nvisionx.resources._resource import AsyncResource, SyncResource


def _ingest_options(
    url: str | None,
    file: FilesInput | None,
    metadata: Mapping[str, str] | None,
    classify: bool | None,
    idempotency_key: str | None,
    opened: list[IO[bytes]],
) -> RequestOptions:
    if url is not None and file is None:
        body: dict[str, Any] = drop_none({"url": url, "metadata": metadata, "classify": classify})
        return RequestOptions("POST", "v1/documents", json=body, idempotency_key=idempotency_key)
    if file is None or url is not None:
        raise TypeError("Pass exactly one of url= or file=.")
    form = drop_none(
        {
            "metadata": json.dumps(dict(metadata)) if metadata is not None else None,
            "classify": None if classify is None else str(classify).lower(),
        }
    )
    return RequestOptions(
        "POST",
        "v1/documents",
        data=form,
        files=to_httpx_files(file, opened),
        idempotency_key=idempotency_key,
        timeout=UPLOAD_TIMEOUT,
    )


def _close(opened: list[IO[bytes]]) -> None:
    for handle in opened:
        handle.close()


def _document(document_id: str, suffix: str = "") -> str:
    return path("v1/documents/{id}", id=document_id) + suffix


def _iso(value: datetime | str | None) -> str | None:
    return value.isoformat() if isinstance(value, datetime) else value


def _list_params(
    status: DocumentStatusFilter | None,
    source_id: str | None,
    q: str | None,
    modified_after: datetime | str | None,
    modified_before: datetime | str | None,
    limit: int | None,
    cursor: str | None,
) -> dict[str, Any]:
    return {
        "status": status,
        "source_id": source_id,
        "q": q,
        "modified_after": _iso(modified_after),
        "modified_before": _iso(modified_before),
        "limit": limit,
        "cursor": cursor,
    }


def _delete_many_options(
    ids: Sequence[str] | None,
    filter: DocumentFilter | Mapping[str, Any] | None,
    expected_count: int | None,
    dry_run: bool | None,
) -> RequestOptions:
    if (ids is None) == (filter is None):
        raise TypeError("Pass exactly one of ids= or filter=.")
    if isinstance(filter, DocumentFilter):
        filter = filter.model_dump(mode="json", exclude_none=True)
    elif filter is not None:
        filter = {k: _iso(v) if isinstance(v, datetime) else v for k, v in filter.items()}
    body = drop_none(
        {
            "ids": list(ids) if ids is not None else None,
            "filter": filter,
            "expected_count": expected_count,
            "dry_run": dry_run,
        }
    )
    return RequestOptions("POST", "v1/documents/delete", json=body)


class Documents(SyncResource):
    def ingest(
        self,
        *,
        url: str | None = None,
        file: FilesInput | None = None,
        metadata: Mapping[str, str] | None = None,
        classify: bool | None = None,
        idempotency_key: str | None = None,
    ) -> Job:
        opened: list[IO[bytes]] = []
        try:
            options = _ingest_options(url, file, metadata, classify, idempotency_key, opened)
            return self._client.request(options, Job)
        finally:
            _close(opened)

    def list(
        self,
        *,
        status: DocumentStatusFilter | None = None,
        source_id: str | None = None,
        q: str | None = None,
        modified_after: datetime | str | None = None,
        modified_before: datetime | str | None = None,
        limit: int | None = None,
        cursor: str | None = None,
    ) -> SyncPage[Document]:
        params = _list_params(status, source_id, q, modified_after, modified_before, limit, cursor)
        return self._paginate("v1/documents", params, DocumentList)

    def get(self, document_id: str) -> DocumentDetail:
        return self._client.request(RequestOptions("GET", _document(document_id)), DocumentDetail)

    def parsed(self, document_id: str) -> DocumentParsed:
        return self._client.request(RequestOptions("GET", _document(document_id, "/parsed")), DocumentParsed)

    def summary(self) -> DocumentSummary:
        return self._client.request(RequestOptions("GET", "v1/documents/summary"), DocumentSummary)

    def delete(self, document_id: str) -> Deleted:
        return self._client.request(RequestOptions("DELETE", _document(document_id)), Deleted)

    def delete_many(
        self,
        *,
        ids: Sequence[str] | None = None,
        filter: DocumentFilter | Mapping[str, Any] | None = None,
        expected_count: int | None = None,
        dry_run: bool | None = None,
    ) -> DocumentDeleteResult:
        options = _delete_many_options(ids, filter, expected_count, dry_run)
        return self._client.request(options, DocumentDeleteResult)


class AsyncDocuments(AsyncResource):
    async def ingest(
        self,
        *,
        url: str | None = None,
        file: FilesInput | None = None,
        metadata: Mapping[str, str] | None = None,
        classify: bool | None = None,
        idempotency_key: str | None = None,
    ) -> Job:
        opened: list[IO[bytes]] = []
        try:
            options = _ingest_options(url, file, metadata, classify, idempotency_key, opened)
            return await self._client.request(options, Job)
        finally:
            _close(opened)

    def list(
        self,
        *,
        status: DocumentStatusFilter | None = None,
        source_id: str | None = None,
        q: str | None = None,
        modified_after: datetime | str | None = None,
        modified_before: datetime | str | None = None,
        limit: int | None = None,
        cursor: str | None = None,
    ) -> AsyncPaginator[Document]:
        params = _list_params(status, source_id, q, modified_after, modified_before, limit, cursor)
        return self._paginate("v1/documents", params, DocumentList)

    async def get(self, document_id: str) -> DocumentDetail:
        return await self._client.request(RequestOptions("GET", _document(document_id)), DocumentDetail)

    async def parsed(self, document_id: str) -> DocumentParsed:
        return await self._client.request(RequestOptions("GET", _document(document_id, "/parsed")), DocumentParsed)

    async def summary(self) -> DocumentSummary:
        return await self._client.request(RequestOptions("GET", "v1/documents/summary"), DocumentSummary)

    async def delete(self, document_id: str) -> Deleted:
        return await self._client.request(RequestOptions("DELETE", _document(document_id)), Deleted)

    async def delete_many(
        self,
        *,
        ids: Sequence[str] | None = None,
        filter: DocumentFilter | Mapping[str, Any] | None = None,
        expected_count: int | None = None,
        dry_run: bool | None = None,
    ) -> DocumentDeleteResult:
        options = _delete_many_options(ids, filter, expected_count, dry_run)
        return await self._client.request(options, DocumentDeleteResult)
