from __future__ import annotations

import asyncio
import time

from nvisionx._base_client import RequestOptions, path
from nvisionx._errors import JobTimeoutError
from nvisionx._models import Job, JobList, JobStatus
from nvisionx._pagination import AsyncPaginator, SyncPage
from nvisionx.resources._resource import AsyncResource, SyncResource

TERMINAL_STATUSES = frozenset({"completed", "failed"})


class Jobs(SyncResource):
    def list(
        self,
        *,
        status: JobStatus | None = None,
        source_id: str | None = None,
        limit: int | None = None,
        cursor: str | None = None,
    ) -> SyncPage[Job]:
        params = {"status": status, "source_id": source_id, "limit": limit, "cursor": cursor}
        return self._paginate("v1/jobs", params, JobList)

    def get(self, job_id: str) -> Job:
        return self._client.request(RequestOptions("GET", path("v1/jobs/{id}", id=job_id)), Job)

    def wait(self, job_id: str, *, poll_interval: float = 2.0, timeout: float | None = 600.0) -> Job:
        deadline = None if timeout is None else time.monotonic() + timeout
        while True:
            job = self.get(job_id)
            if job.status in TERMINAL_STATUSES:
                return job
            if deadline is not None and time.monotonic() + poll_interval > deadline:
                raise JobTimeoutError(job_id, timeout or 0.0)
            time.sleep(poll_interval)


class AsyncJobs(AsyncResource):
    def list(
        self,
        *,
        status: JobStatus | None = None,
        source_id: str | None = None,
        limit: int | None = None,
        cursor: str | None = None,
    ) -> AsyncPaginator[Job]:
        params = {"status": status, "source_id": source_id, "limit": limit, "cursor": cursor}
        return self._paginate("v1/jobs", params, JobList)

    async def get(self, job_id: str) -> Job:
        return await self._client.request(RequestOptions("GET", path("v1/jobs/{id}", id=job_id)), Job)

    async def wait(self, job_id: str, *, poll_interval: float = 2.0, timeout: float | None = 600.0) -> Job:
        deadline = None if timeout is None else time.monotonic() + timeout
        while True:
            job = await self.get(job_id)
            if job.status in TERMINAL_STATUSES:
                return job
            if deadline is not None and time.monotonic() + poll_interval > deadline:
                raise JobTimeoutError(job_id, timeout or 0.0)
            await asyncio.sleep(poll_interval)
