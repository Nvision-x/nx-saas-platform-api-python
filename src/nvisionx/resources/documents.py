from __future__ import annotations

import json
from collections.abc import Mapping
from typing import IO, Any

from nvisionx._base_client import UPLOAD_TIMEOUT, RequestOptions, drop_none
from nvisionx._files import FilesInput, to_httpx_files
from nvisionx._models import Job
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
