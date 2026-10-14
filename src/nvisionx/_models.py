from __future__ import annotations

from datetime import date
from typing import Annotated, Literal

from pydantic import AwareDatetime, ConfigDict, Field
from typing_extensions import TypeAliasType

from nvisionx._base import NxModel, Open


class AgentRun(NxModel):
    run_id: str
    status: Annotated[Literal["completed", "failed", "stopped"], Open]
    tool_calls: int
    cost_usd: float
    answer: str | None = None
    citations: list[str] | None = None
    """
    Record IDs.
    """


class AppGrant(NxModel):
    id: str
    app_id: str
    """
    The Nx application (Entra client ID).
    """
    status: Annotated[Literal["pending", "consented", "revoked"], Open]
    consent_url: str | None = None
    """
    Pending grants.
    """
    drives: int
    """
    Drives synced through this application.
    """
    throttled_until: AwareDatetime | None = None
    consented_at: AwareDatetime | None = None
    created_at: AwareDatetime


class AppGrantList(NxModel):
    data: list[AppGrant]
    recommended: Annotated[int, Field(ge=1)]


class BudgetUpdate(NxModel):
    name: str | None = None
    limit_usd: Annotated[float | None, Field(gt=0.0)] = None
    alert_thresholds: list[Annotated[Literal[50, 80, 100], Open]] | None = None
    notify: list[str] | None = None


class ChatCitation(NxModel):
    """
    A record the answer cites; `marker` is the number in its `[n]` markers.
    """

    marker: Annotated[int, Field(ge=1)]
    record_id: str
    title: str
    path: str | None = None
    """
    Source URI.
    """
    source_id: str
    record_type: str | None = None
    snippet: str
    """
    The passage the answer relies on.
    """


class ChatConversation(NxModel):
    id: Annotated[str, Field(examples=["conv_8Kd2"])]
    title: Annotated[str, Field(examples=["Indemnity caps in vendor contracts"])]
    sources: list[str]
    """
    Data source IDs the agent may search. Empty: every source the caller may read.
    """
    message_count: int
    last_message_preview: str | None
    created_at: AwareDatetime
    updated_at: AwareDatetime


class ChatConversationCreate(NxModel):
    title: Annotated[str | None, Field(max_length=120)] = None
    sources: list[str] | None = None


class ChatConversationUpdate(NxModel):
    title: Annotated[str | None, Field(max_length=120, min_length=1)] = None
    sources: list[str] | None = None


class ChatMessageCreate(NxModel):
    content: Annotated[str, Field(max_length=8000, min_length=1)]


class CredentialRef(NxModel):
    """
    What authenticated a call — an API token or an OAuth grant (connected app).
    """

    type: Annotated[Literal["token", "oauth"], Open]
    id: str
    """
    Token ID or grant ID.
    """
    name: Annotated[str, Field(examples=["support-copilot-mcp", "Claude · Lena Chen"])]


Cursor = TypeAliasType("Cursor", str | None)
"""
Pass as `cursor` to fetch the next page. `null` on the last page.
"""


class Deleted(NxModel):
    id: str
    deleted: Annotated[Literal[True], Open]


ErrorType = TypeAliasType(
    "ErrorType",
    Annotated[
        Literal[
            "invalid_request",
            "unauthenticated",
            "budget_exceeded",
            "spend_limit_reached",
            "insufficient_balance",
            "insufficient_scope",
            "permission_denied",
            "not_found",
            "conflict",
            "unprocessable",
            "rate_limited",
            "internal_error",
        ],
        Open,
    ],
)


class EstateBucket(NxModel):
    key: str
    files: int
    bytes: int


class EstateTotals(NxModel):
    sites: int
    libraries: int
    """
    Document libraries (drives) outside OneDrive.
    """
    onedrives: int
    folders: int
    files: int
    bytes: int
    shared_items: int | None = None
    """
    Items shared beyond their site or owner.
    """


class IngestUploadRequest(NxModel):
    file: list[bytes]
    metadata: str | None = None
    """
    JSON-encoded object.
    """
    classify: bool | None = True


class IngestUrlRequest(NxModel):
    url: str
    """
    A URL (typically signed) Nx fetches once.
    """
    metadata: dict[str, str] | None = None
    """
    Stored with the record.
    """
    classify: bool | None = True


JobStatus = TypeAliasType("JobStatus", Annotated[Literal["queued", "running", "paused", "completed", "failed"], Open])


class Oauth(NxModel):
    resource_metadata_url: Annotated[str, Field(examples=["https://mcp.nx.dev/.well-known/oauth-protected-resource"])]
    authorization_server: Annotated[str, Field(examples=["https://auth.nx.dev"])]


McpToolName = TypeAliasType(
    "McpToolName",
    Annotated[Literal["search_records", "get_record", "list_sources", "summarize_records", "ingest_document"], Open],
)


Meter = TypeAliasType("Meter", Annotated[Literal["docs", "gb", "search", "agent"], Open])
"""
`docs` documents ingested · `gb` GB processed · `search` search queries · `agent` agent / MCP tool calls.
"""


NodeSelection = TypeAliasType("NodeSelection", Annotated[Literal["included", "excluded", "partial"], Open])


Provider = TypeAliasType("Provider", Annotated[Literal["sharepoint", "s3", "gdrive", "box"], Open])


class Rate(NxModel):
    meter: Meter
    label: Annotated[str, Field(examples=["Documents ingested"])]
    unit: Annotated[str, Field(examples=["per 1K docs"])]
    unit_size: Annotated[int, Field(examples=[1000])]
    price_usd: Annotated[float, Field(examples=[1.2])]


RetentionStatus = TypeAliasType("RetentionStatus", Annotated[Literal["active", "hold", "expired", "unscheduled"], Open])


Scope = TypeAliasType(
    "Scope",
    Annotated[
        Literal[
            "ingest:read",
            "ingest:write",
            "search:read",
            "search:write",
            "agent:read",
            "agent:write",
            "sources:read",
            "sources:write",
            "billing:read",
            "billing:write",
        ],
        Open,
    ],
)


class SelectionPreview(NxModel):
    files: int
    bytes: int
    containers: int
    """
    Sites, libraries and drives touched.
    """
    complete: bool | None = None
    """
    False while the inventory is still running; counts will grow.
    """


Sensitivity = TypeAliasType(
    "Sensitivity", Annotated[Literal["public", "internal", "confidential", "pii", "phi", "pci"], Open]
)


class SelectionSummary(NxModel):
    """
    `null` until content is selected.
    """

    mode: Annotated[Literal["all", "custom"], Open]
    files: int
    bytes: int


class SourceAuthorizationVerify(NxModel):
    """
    Pass the provider's redirect parameters through unchanged.
    Microsoft 365 admin consent: `tenant`, `admin_consent`, `state` (or `error`, `error_description`).
    OAuth (`personal` mode, Google Drive, Box): `code`, `state`.
    IAM (Amazon S3): `bucket`, `region`, `role_arn`.

    """

    code: str | None = None
    """
    OAuth authorization code from the redirect.
    """
    state: str | None = None
    tenant: str | None = None
    """
    Microsoft 365 tenant ID from the admin-consent redirect.
    """
    admin_consent: Annotated[str | None, Field(examples=["True"])] = None
    error: str | None = None
    error_description: str | None = None
    bucket: Annotated[str | None, Field(examples=["acme-claims-archive"])] = None
    region: Annotated[str | None, Field(examples=["us-east-1"])] = None
    role_arn: Annotated[str | None, Field(examples=["arn:aws:iam::123456789012:role/nx-reader"])] = None


class Inventory(NxModel):
    status: Annotated[Literal["pending", "running", "complete"], Open]
    containers_total: int
    containers_done: int


SourceMode = TypeAliasType("SourceMode", Annotated[Literal["tenant", "personal"], Open])
"""
`tenant`: an administrator grants app-only read access to the whole organization (Microsoft 365). `personal`: delegated access to one user's own drive.
"""


class SourceNode(NxModel):
    ref: Annotated[str, Field(examples=["drive:b!x1"])]
    """
    Opaque, stable node reference, e.g. `site:…`, `drive:…`, `item:…`. Use as `parent` and in selections.
    """
    kind: Annotated[Literal["group", "site", "library", "onedrive", "folder", "file", "bucket", "prefix"], Open]
    name: Annotated[str, Field(examples=["Contracts"])]
    path: Annotated[str, Field(examples=["Legal / Contracts"])]
    web_url: str | None = None
    has_children: bool
    files: int | None = None
    """
    Recursive file count. `null` until inventoried.
    """
    bytes: int | None = None
    last_modified: AwareDatetime | None = None
    selection: NodeSelection


class SourceNodeList(NxModel):
    data: list[SourceNode]
    next_cursor: Cursor


SourcePhase = TypeAliasType(
    "SourcePhase", Annotated[Literal["discovering", "inventorying", "awaiting_selection", "syncing", "idle"], Open]
)
"""
Where the source is in its lifecycle. `awaiting_selection`: the estate is inventoried and nothing is selected yet.
"""


class Counters(NxModel):
    seen: int
    added: int
    updated: int
    deleted: int
    bytes: int


class SourceRun(NxModel):
    id: str
    kind: Annotated[Literal["discover", "inventory", "sync", "reconcile"], Open]
    trigger: Annotated[Literal["initial", "schedule", "webhook", "manual", "selection"], Open]
    status: Annotated[Literal["queued", "running", "completed", "failed", "cancelled"], Open]
    container: SourceNode | None = None
    counters: Counters
    error: str | None = None
    started_at: AwareDatetime
    finished_at: AwareDatetime | None = None


class SourceRunList(NxModel):
    data: list[SourceRun]
    next_cursor: Cursor


class SourceSelectionUpdate(NxModel):
    mode: Annotated[Literal["all", "custom"], Open]
    include: Annotated[list[str] | None, Field(max_length=1000)] = None
    """
    Node refs. `custom` only.
    """
    exclude: Annotated[list[str] | None, Field(max_length=1000)] = None
    """
    Node refs inside included nodes (or anywhere with `mode: all`).
    """
    include_new_sites: bool | None = False
    """
    Add sites and libraries created later. Implied by `mode: all`.
    """
    include_onedrive: bool | None = False
    """
    Include every user's OneDrive. Implied by `mode: all`.
    """


SyncSchedule = TypeAliasType("SyncSchedule", Annotated[Literal["continuous", "hourly", "daily"], Open])
"""
`continuous`: change notifications from the provider, plus a safety-net poll. `hourly` and `daily`: incremental syncs on that cadence. Use `syncSource` to sync now.
"""


class UsageCredit(NxModel):
    """
    Free credit against the period's usage. Credit belongs to the **organization**, so these figures cover every workspace of it, not only the workspace of the request. Provisional until the period closes.
    """

    organization_total_usd: float
    """
    The organization's usage cost for the period (every workspace).
    """
    applied_usd: float
    """
    Credit applied to the organization's usage in the period (at most `organization_total_usd`).
    """
    remaining_usd: float
    """
    Unexpired credit left after the period.
    """


class AgentRunRequest(NxModel):
    instructions: Annotated[str, Field(min_length=1)]
    tools: list[McpToolName] | None = None
    """
    Allowed tools. Default: all permitted.
    """
    sources: list[str] | None = None
    """
    Limit to these source IDs. Default: all permitted.
    """
    max_tool_calls: Annotated[int | None, Field(ge=1, le=100)] = 20


class AgentSession(NxModel):
    id: str
    client: Annotated[str, Field(examples=["Claude Desktop 1.4"])]
    credential: CredentialRef
    tool_calls: int
    cost_usd: float
    started_at: AwareDatetime


class AgentSessionList(NxModel):
    data: list[AgentSession]
    next_cursor: Cursor


class BudgetScope(NxModel):
    type: Annotated[Literal["workspace", "meter", "token"], Open]
    meter: Meter | None = None
    token_id: str | None = None


class ChatConversationList(NxModel):
    data: list[ChatConversation]
    next_cursor: Cursor


class ChatReasoningStep(NxModel):
    summary: Annotated[str, Field(examples=["Searched vendor contracts for indemnity caps"])]
    detail: str | None = None
    tool: McpToolName | None = None


class Classification(NxModel):
    record_id: str | None = None
    record_type: str
    owner: str
    sensitivity: Sensitivity
    retention: Annotated[str, Field(examples=["7y after termination"])]


class ErrorDetail(NxModel):
    model_config = ConfigDict(
        extra="allow",
    )
    type: ErrorType
    message: str
    param: str | None = None
    """
    The request field at fault (invalid_request).
    """
    required_scope: str | None = None
    """
    The missing scope (insufficient_scope).
    """
    budget: str | None = None
    """
    The exhausted budget (budget_exceeded).
    """
    limit_usd: float | None = None
    spent_usd: float | None = None
    resolve: str | None = None
    """
    How to recover.
    """
    balance_usd: float | None = None
    """
    The organization balance (insufficient_balance).
    """
    limit_per_minute: int | None = None
    """
    The organization's request rate (rate_limited).
    """


class Error(NxModel):
    error: ErrorDetail


class Job(NxModel):
    id: Annotated[str, Field(examples=["job_7Hq2xK"])]
    source: Annotated[Literal["api", "upload", "sharepoint", "s3", "gdrive", "box"], Open]
    source_id: str | None = None
    documents: int
    status: JobStatus
    progress: Annotated[int, Field(ge=0, le=100)]
    record_types: list[str]
    """
    Distinct record types assigned so far.
    """
    estimated_cost_usd: float | None = None
    classified: list[Classification] | None = None
    """
    Per-document classifications, on completed jobs with ≤ 100 documents.
    """
    error: str | None = None
    created_at: AwareDatetime
    completed_at: AwareDatetime | None = None


class JobList(NxModel):
    data: list[Job]
    next_cursor: Cursor


class McpTool(NxModel):
    name: McpToolName
    description: str
    scope: Scope
    enabled: bool


class MeterUsage(Rate):
    quantity: float
    cost_usd: float
    daily: list[float]
    """
    Cost per day so far this period.
    """


class RecordRetention(NxModel):
    status: RetentionStatus
    series: Annotated[str | None, Field(examples=["VC-01"])] = None
    until: date | None = None
    """
    `null` while an event trigger has not fired.
    """
    rule_summary: Annotated[str | None, Field(examples=["until superseded + 2y"])] = None
    hold_id: str | None = None
    schedule_version: str | None = None


class Filters(NxModel):
    record_type: list[str] | None = None
    owner: str | None = None
    sensitivity: list[Sensitivity] | None = None
    retention_status: RetentionStatus | None = None
    created_after: date | None = None
    created_before: date | None = None


class SearchRequest(NxModel):
    query: Annotated[str, Field(min_length=1)]
    """
    Natural-language or keyword query.
    """
    sources: list[str] | None = None
    """
    Limit to these source IDs. Default: every source the token can read.
    """
    mode: Annotated[Literal["hybrid", "semantic", "keyword"], Open] | None = "hybrid"
    filters: Filters | None = None
    limit: Annotated[int | None, Field(ge=1, le=100)] = 10


class SearchResult(NxModel):
    id: str
    title: str
    path: str
    """
    Source URI.
    """
    source_id: str
    record_type: str
    owner: str
    sensitivity: Sensitivity
    score: Annotated[float, Field(ge=0.0, le=1.0)]
    snippet: str
    retention: RecordRetention


class Source(NxModel):
    id: Annotated[str, Field(examples=["src_01J9Z…"])]
    provider: Provider
    mode: SourceMode
    name: Annotated[str, Field(examples=["acmehealth.sharepoint.com"])]
    account: str | None = None
    """
    The connected tenant, bucket or domain.
    """
    detail: Annotated[str, Field(examples=["3 sites · Legal, HR, Finance"])]
    schedule: SyncSchedule
    status: Annotated[Literal["healthy", "syncing", "paused", "error", "action_required"], Open]
    """
    `action_required`: consent was revoked or change notifications are failing; see `error`.
    """
    phase: SourcePhase
    progress: Annotated[int, Field(ge=0, le=100)]
    """
    Progress of the current phase.
    """
    documents: int
    """
    Documents ingested from this source.
    """
    size_gb: float
    """
    Size of the ingested documents.
    """
    selection_summary: SelectionSummary | None
    """
    `null` until content is selected.
    """
    estate_summary: EstateTotals | None
    """
    `null` until discovery finishes.
    """
    last_synced_at: AwareDatetime | None = None
    next_sync_at: AwareDatetime | None = None
    error: str | None = None
    created_at: AwareDatetime


class SourceAuthorization(NxModel):
    id: str
    provider: Provider
    mode: SourceMode
    status: Annotated[Literal["pending", "verified", "failed"], Open]
    authorize_url: str | None = None
    """
    OAuth and admin-consent providers.
    """
    external_id: str | None = None
    """
    IAM providers. Use as the role's sts:ExternalId condition.
    """
    account: str | None = None
    """
    The verified tenant, bucket or domain, e.g. acmehealth.sharepoint.com.
    """
    error: str | None = None
    expires_at: AwareDatetime | None = None
    """
    A pending authorization must be verified before this time.
    """


class SourceAuthorizationCreate(NxModel):
    provider: Provider
    mode: SourceMode | None = "tenant"
    """
    Microsoft 365 only. Ignored by other providers.
    """
    redirect_uri: str | None = None
    """
    OAuth providers only.
    """


class SourceCreate(NxModel):
    authorization_id: str
    """
    A verified authorization.
    """
    name: str | None = None
    """
    Default: the verified account.
    """
    schedule: SyncSchedule


class SourceEstate(NxModel):
    source_id: str
    as_of: AwareDatetime
    inventory: Inventory
    totals: EstateTotals
    by_type: list[EstateBucket]
    """
    Keys: documents, spreadsheets, presentations, pdf, email, images, media, archives, other.
    """
    by_age: list[EstateBucket]
    """
    By last modified. Keys: lt_1y, 1y_3y, 3y_7y, gt_7y.
    """
    top_containers: list[SourceNode]
    """
    Largest sites and drives.
    """


class SourceList(NxModel):
    data: list[Source]


class SourceSelection(SourceSelectionUpdate):
    files: int
    bytes: int
    updated_at: AwareDatetime | None


class SourceUpdate(NxModel):
    name: Annotated[str | None, Field(min_length=1)] = None
    schedule: SyncSchedule | None = None


class Usage(NxModel):
    period: Annotated[str, Field(examples=["2026-10"])]
    period_start: date
    period_end: date
    days_elapsed: int
    total_usd: float
    forecast_usd: float
    """
    At the current run rate.
    """
    meters: list[MeterUsage]
    daily_spend_usd: list[float]
    next_invoice_at: date | None = None
    credit: UsageCredit


class Budget(NxModel):
    id: str
    name: str
    scope: BudgetScope
    scope_label: Annotated[str | None, Field(examples=["Meter · Documents ingested"])] = None
    type: Annotated[Literal["soft", "hard"], Open]
    limit_usd: float
    spent_usd: float
    alert_thresholds: list[Annotated[Literal[50, 80, 100], Open]]
    notify: list[str]
    blocking: bool
    """
    Hard budget at its limit; calls in scope return 402.
    """
    created_at: AwareDatetime


class BudgetCreate(NxModel):
    name: str | None = None
    """
    Default: derived from the scope.
    """
    scope: BudgetScope
    type: Annotated[Literal["soft", "hard"], Open]
    """
    `hard` only with `token` scope (a spend cap); the organization balance governs everything else.
    """
    limit_usd: Annotated[float, Field(gt=0.0)]
    alert_thresholds: list[Annotated[Literal[50, 80, 100], Open]] | None = [50, 80, 100]
    notify: list[str] | None = None


class BudgetList(NxModel):
    data: list[Budget]


class ChatMessage(NxModel):
    id: Annotated[str, Field(examples=["msg_3Fq9"])]
    role: Annotated[Literal["user", "assistant"], Open]
    content: str
    """
    Markdown. Assistant answers cite records with `[n]` markers.
    """
    citations: list[ChatCitation] | None = None
    reasoning: list[ChatReasoningStep] | None = None
    tool_calls: int | None = None
    cost_usd: float | None = None
    created_at: AwareDatetime


class ChatStreamEvent(NxModel):
    """
    One server-sent event of `sendChatMessage`. `status`: what the agent is doing now · `step`: a finished reasoning step · `delta`: answer text to append · `complete`: the stored assistant message · `error`: the answer failed (nothing is billed for an answer that never started).
    """

    type: Annotated[Literal["status", "step", "delta", "complete", "error"], Open]
    status: str | None = None
    step: ChatReasoningStep | None = None
    text: str | None = None
    message: ChatMessage | None = None
    error: str | None = None


class McpServer(NxModel):
    url: Annotated[str, Field(examples=["https://mcp.nx.dev/mcp"])]
    """
    The same URL for every workspace (the deployment's MCP resource). The credential selects the workspace.
    """
    status: Annotated[Literal["online", "degraded", "offline"], Open]
    oauth: Oauth
    tools: list[McpTool]
    price_per_1k_calls_usd: float


class SearchResponse(NxModel):
    took_ms: int
    total: int
    cost_usd: float | None = None
    results: list[SearchResult]


class ChatConversationDetail(NxModel):
    conversation: ChatConversation
    messages: list[ChatMessage]
