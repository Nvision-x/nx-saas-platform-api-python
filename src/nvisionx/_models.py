from __future__ import annotations

from datetime import date
from typing import Annotated, Any, Literal

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


class ChatNotice(NxModel):
    """
    Something about how an answer was produced that the user should be told. `capacity_wait`: our service hit a capacity limit with its AI model provider and the answer waited before retrying. `fallback`: the answer used a different model than usual because the first choice was unavailable. `degraded`: no model could write the answer (a capacity limit, or the provider unavailable), so it lists the most relevant passages instead.
    """

    kind: Annotated[Literal["capacity_wait", "fallback", "degraded"], Open]
    message: str
    """
    To show the user as is.
    """
    attempt: int | None = None
    """
    `capacity_wait`: which retry this was.
    """
    of: int | None = None
    """
    `capacity_wait`: how many retries there are at most.
    """
    wait_s: int | None = None
    """
    `capacity_wait`: seconds waited before the retry.
    """


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


class DocumentDeleteResult(NxModel):
    matched: int
    """
    Live documents matched.
    """
    deleted: int
    """
    Documents deleted (0 with dry_run).
    """
    bytes: int
    """
    Size of the matched documents.
    """
    excluded: int
    """
    Connector documents excluded from their source's selection (would be, with dry_run).
    """
    purge_after: AwareDatetime
    """
    When the deleted documents' data will be removed.
    """


DocumentDeletedReason = TypeAliasType(
    "DocumentDeletedReason", Annotated[Literal["source", "deselected", "source_removed", "bucket", "user"], Open]
)
"""
`source`: gone from the source system. `deselected`: no longer selected on its source. `source_removed`: its source was disconnected. `bucket`: its original was deleted from the workspace's bucket. `user`: deleted through the API.
"""


class DocumentEvent(NxModel):
    kind: Annotated[Literal["added", "modified", "deleted", "restored", "raw_purged", "data_purged"], Open]
    reason: str | None
    version: str | None
    size: int | None
    at: AwareDatetime


class DocumentParsed(NxModel):
    """
    What the parser read from a document.
    """

    parser: str
    """
    The parser that read it.
    """
    parser_version: str
    page_count: int | None
    language: str | None
    metadata: dict[str, Any]
    """
    Fields the parser found (title, author, …), as the index uses them.
    """
    text: str
    """
    The text as Markdown, the first 1 MB at most.
    """
    chars: int
    """
    Length of the whole text in characters.
    """
    truncated: bool
    """
    `text` holds only the first 1 MB.
    """


class DocumentReparseResult(NxModel):
    matched: int
    """
    Failed live documents matched.
    """
    queued: int
    """
    Documents queued to be parsed again (0 with dry_run).
    """


class DocumentSourceSummary(NxModel):
    source_id: str
    source_name: str
    source_provider: str
    documents: int
    """
    Live documents.
    """
    parsing: int
    """
    Live documents waiting for the parser.
    """
    indexing: int
    """
    Live documents read, waiting for the index build.
    """
    searchable: int
    """
    Live documents an index holds.
    """
    failed: int
    """
    Live documents that could not be read or indexed.
    """
    bytes: int
    """
    Size of the live documents.
    """
    deleted: int
    """
    Deleted documents (their records are kept).
    """
    purge_pending: int
    """
    Deleted documents whose data is not removed yet.
    """


DocumentStage = TypeAliasType("DocumentStage", Annotated[Literal["parsing", "indexing", "searchable", "failed"], Open])
"""
`parsing`: waiting for the parser. `indexing`: read, waiting for the index build. `searchable`: an index holds it. `failed`: it could not be read or indexed.
"""


DocumentStatus = TypeAliasType("DocumentStatus", Annotated[Literal["active", "deleted"], Open])


DocumentStatusFilter = TypeAliasType("DocumentStatusFilter", Annotated[Literal["active", "deleted", "all"], Open])


class DocumentSummary(NxModel):
    documents: int
    parsing: int
    indexing: int
    searchable: int
    failed: int
    bytes: int
    deleted: int
    purge_pending: int
    deleted_retention_days: int
    """
    Days a deleted document's data is kept before it is removed.
    """
    sources: list[DocumentSourceSummary]


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


class GoverningActor(NxModel):
    type: Annotated[Literal["system", "user", "token"], Open]
    id: str
    name: str | None


class GoverningAlternative(NxModel):
    governing_document_id: str
    doc_id: str
    title: str
    version: str | None
    effective_from: date | None
    effective_to: date | None
    source: Annotated[Literal["discovered", "uploaded"], Open]
    status: Annotated[Literal["proposed", "confirmed"], Open]


class Progress(NxModel):
    done: int
    total: int


class Counts(NxModel):
    queries: int
    candidates: int
    classified: int
    cache_hits: int
    skipped_uploaded: int
    skipped_decided: int
    unresolved: int
    discarded: int
    proposals: int


class Failure(NxModel):
    code: str
    message: str


class GoverningDiscoveryRun(NxModel):
    id: Annotated[str, Field(examples=["gdr_01k6c1x0d8f9g2h3j4k5m6n7p8"])]
    trigger: Annotated[Literal["build", "new_documents", "request"], Open]
    status: Annotated[Literal["queued", "running", "completed", "failed", "cancelled"], Open]
    phase: str
    progress: Progress
    counts: Counts
    failure: Failure | None
    cancel_reason: Annotated[Literal["discovery_disabled", "superseded"], Open] | None
    build_id: str | None
    registry_version: int | None
    requested_by: GoverningActor | None
    created_at: AwareDatetime
    started_at: AwareDatetime | None
    finished_at: AwareDatetime | None


class Eligibility(NxModel):
    state: Annotated[Literal["eligible", "ineligible"], Open]
    reasons: list[str]


class Document1(NxModel):
    doc_id: str | None
    """
    The knowledge hub document id, used to open the text.
    """
    document_id: str | None
    content_version: str
    filename: str | None
    access: Annotated[Literal["readable", "withheld"], Open]


class Reading(NxModel):
    mode: Annotated[Literal["full", "excerpts"], Open]
    truncated: bool
    supplied_chars: int
    total_chars: int


class GoverningDocumentType(NxModel):
    id: str
    kind: Annotated[Literal["target", "catch_all"], Open]
    label: str
    definition: str
    uploadable: bool
    entity_kinds: list[str]


class GoverningDocumentTypeList(NxModel):
    registry_version: int
    data: list[GoverningDocumentType]


class GoverningQuote(NxModel):
    text: str | None
    """
    `null` when withheld because you cannot read the document.
    """
    start_char: int | None
    """
    Code points into the text identified by `text_sha256`, end-exclusive.
    """
    end_char: int | None
    text_sha256: str
    page: int | None
    heading: str | None


class IngestHour(NxModel):
    start: AwareDatetime
    added: int
    """
    Documents added in the hour.
    """
    parsed: int
    """
    Documents the parser read in the hour.
    """
    searchable: int
    """
    Documents that became searchable in the hour.
    """


class IngestUploadRequest(NxModel):
    file: Annotated[list[bytes], Field(max_length=100, min_length=1)]
    """
    The files, 1 to 100 per request, up to 2 GB each.
    """
    metadata: Annotated[
        str | None,
        Field(
            examples=[
                '{"governing_doc_type":"access_review","governing_doc_source":"manual","governing_doc_version":"2.0","governing_doc_effective_from":"2026-01-01"}'
            ]
        ),
    ] = None
    """
    JSON-encoded object of strings, sent as a multipart part before every
    file part. Ordinary keys are stored with the record. Governing uploads
    require both `governing_doc_type` (an uploadable registry id) and
    `governing_doc_source` (`manual`), or neither. Optional
    `governing_doc_version` is at most 64 characters;
    `governing_doc_effective_from` and `governing_doc_effective_to` are
    valid `YYYY-MM-DD` dates with from no later than to. These optional
    values are recorded as supplied, never as source quotations.
    Governing validation failures return 422; an unavailable registry
    returns 503 with reason `governing_types_unavailable`. Failed uploads
    keep no stored originals. Keys without the `governing_doc_` prefix
    keep their usual meaning.

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


class JobFailure(NxModel):
    document_id: str
    name: str
    error: str
    """
    The document's `ingest_error`.
    """


class JobProgress(NxModel):
    """
    Progress of background work on the workspace.
    """

    state: Annotated[Literal["running", "stalled", "done", "failed"], Open]
    """
    `stalled`: running, but no progress was reported for over 3 minutes.
    """
    done: int
    """
    Documents processed so far.
    """
    total: int
    """
    Documents to process. 0 while not yet known.
    """
    percent: Annotated[float | None, Field(examples=[12.2])]
    """
    `done` / `total` as a percentage (0–100); `null` while `total` is 0.
    """
    eta_seconds: int | None
    """
    Estimated seconds left while `running`; `null` when it cannot be estimated.
    """
    started_at: AwareDatetime


JobStatus = TypeAliasType("JobStatus", Annotated[Literal["queued", "running", "paused", "completed", "failed"], Open])


class Jobs(NxModel):
    queued: int
    running: int
    completed: int
    failed: int


class JobSummary(NxModel):
    jobs: Jobs
    pending_documents: int
    """
    Live documents not yet searchable and not failed.
    """
    oldest_pending_at: AwareDatetime | None
    """
    When the longest-waiting pending document was added. `null` when none is pending.
    """
    hourly: list[IngestHour]
    """
    The last 24 hours, oldest first; the last bucket is the current, partial hour.
    """
    indexing: JobProgress | None
    """
    The latest update of the workspace's search index. `null` when none is running and none ended in the last 24 hours.
    """
    search_upgrade: JobProgress | None
    """
    The latest upgrade of the workspace's search, reported only while it affects search results. `null` otherwise, and when none is running and none ended in the last 24 hours.
    """


class Oauth(NxModel):
    resource_metadata_url: Annotated[
        str, Field(examples=["https://platform.us.nvisionx.ai/.well-known/oauth-protected-resource"])
    ]
    authorization_server: Annotated[str, Field(examples=["https://platform.us.nvisionx.ai"])]


McpToolName = TypeAliasType(
    "McpToolName",
    Annotated[Literal["search_records", "get_record", "list_sources", "summarize_records", "ingest_document"], Open],
)


Meter = TypeAliasType("Meter", Annotated[Literal["docs", "gb", "search", "agent", "llm_input", "llm_output"], Open])
"""
`docs` documents ingested · `gb` GB processed · `search` search queries · `agent` agent / MCP tool calls · `llm_input` and `llm_output` the language-model tokens an agent read and wrote, per 1M tokens.
"""


class ByModelItem(NxModel):
    model: str
    name: str
    quantity: float
    cost_usd: float


ModelRole = TypeAliasType("ModelRole", Annotated[Literal["answer", "route"], Open])
"""
`answer`: writes answers. `route`: plans how to answer a question (a fast, cheaper call).
"""


NodeSelection = TypeAliasType("NodeSelection", Annotated[Literal["included", "excluded", "partial"], Open])


class Policy(NxModel):
    source: Annotated[Literal["catalog", "workspace_document"], Open]
    policy_id: str
    version: str
    title: str
    approval: Annotated[Literal["approved", "draft", "hypothetical", "not_stated"], Open]
    sha256: str


class RequestedBy(NxModel):
    type: Annotated[Literal["user", "token"], Open]
    id: str
    name: str | None


class Documents(NxModel):
    included: int
    excluded_possible: int


class Engine(NxModel):
    provider_mode: str
    workflow_origin: Annotated[Literal["cached", "extracted", "replayed", "recorded"], Open]
    model_id: str | None
    model_calls: int
    wall_seconds: float
    engine_fingerprint: str


class ProcessAssessmentStart(NxModel):
    policy_id: Annotated[str, Field(max_length=64)]
    version: Annotated[str, Field(max_length=64)]
    snapshot_id: Annotated[str, Field(max_length=128)]
    policy_source: Annotated[Literal["catalog", "workspace_document"], Open] | None = None
    """
    Omitted means `catalog`.
    """
    governing_document_id: Annotated[str | None, Field(max_length=64)] = None


class ProcessDocumentText(NxModel):
    doc_id: str
    text: str
    """
    Plain text; never render as HTML.
    """
    total_chars: int
    """
    Code points in the complete text.
    """
    truncated: bool
    offsets: Annotated[Literal["code_points"], Open]
    content_version: str
    """
    SHA-256 of the original file.
    """
    text_sha256: str
    """
    SHA-256 of the complete text.
    """
    parse_key: str


class Evidence(NxModel):
    doc_id: str
    doc_title: str | None
    quote: str | None


class Decision(NxModel):
    status: Annotated[Literal["accepted", "rejected"], Open]
    by: str
    at: str


class ProcessEntityAlias(NxModel):
    key_type: str
    canonical: str
    surface: str
    status: Annotated[Literal["accepted", "proposed", "rejected"], Open]
    strength: Annotated[Literal["strong", "weak"], Open]
    shared: bool
    source: str
    added_by: str
    added_at: str | None
    evidence: Evidence | None
    df: int | None
    pending_extraction: bool
    decision: Decision | None


class Counts1(NxModel):
    confirmed: int
    likely: int
    possible: int
    rejected: int


class Via(NxModel):
    node: str
    doc_id: str | None


class Thread(NxModel):
    thread_id: str
    subject: str | None
    message_count: int


class Section(NxModel):
    section: str
    document_count: int


class ProcessEntityRef(NxModel):
    entity_id: str
    kind: str
    display_name: str


class MatchedAlias(NxModel):
    key_type: str
    surface: str


class ProcessEntitySummary(ProcessEntityRef):
    created_by: str | None
    matched_alias: MatchedAlias | None


class ProcessEvidenceCoverage(NxModel):
    complete: bool
    """
    True only when nothing below limits the evidence set; otherwise absence of evidence is never reported as a finding.
    """
    file_complete: bool | None
    file_complete_reason: str | None
    members: int
    excluded_possible: int
    missing_text: int
    unreadable: int
    inaccessible: int
    out_of_budget: int
    unplaced_attachments: int
    keys_pending_extraction: int
    reasons: list[str]


class ProcessLinkDecision(NxModel):
    decision: Annotated[Literal["confirmed", "rejected"], Open]
    manual: bool
    by: str
    at: str | None
    reason: str | None


ProcessMandate = TypeAliasType("ProcessMandate", Annotated[Literal["explicit", "inferred"], Open])


class ProcessMapStatus(NxModel):
    enabled: bool
    """
    The knowledge hub is configured. When false every other Process Map operation answers 503.
    """
    entity_index: bool
    review: Annotated[Literal["available", "read_only", "unavailable"], Open]
    document_text: bool
    policies: Annotated[int, Field(ge=0)]
    assessment: Annotated[Literal["available", "no_policies", "provider_off", "unavailable"], Open]


class SnippetMatch(NxModel):
    start: int
    end: int


class ProcessMention(NxModel):
    key_type: str
    surface: str
    canonical: str
    key_status: Annotated[Literal["accepted", "proposed"], Open] | None
    tier: Annotated[Literal["t0", "t1", "t2", "struct"], Open]
    field: str
    chunk_id: str | None
    start_char: int | None
    """
    Code points into the document text, end-exclusive.
    """
    end_char: int | None
    occurrences: int
    snippet: str | None
    snippet_match: SnippetMatch | None


class ProcessPendingKey(NxModel):
    key_type: str
    surface: str


class Availability(NxModel):
    state: Annotated[Literal["available", "unavailable"], Open]
    reason: str | None
    """
    Why the policy is unavailable, including `ambiguous`, `needs_review` and `text_pending`.
    """


class Governing(NxModel):
    """
    Null for catalog policies. An ambiguous workspace slot is unavailable until a document is selected; its singular document ids, source and status are null.
    """

    governing_document_id: str | None
    doc_id: str | None
    document_id: str | None
    source: Annotated[Literal["discovered", "uploaded"], Open] | None
    status: Annotated[Literal["proposed", "confirmed"], Open] | None
    provisional: bool
    ambiguous: bool
    alternatives: list[GoverningAlternative]
    """
    Documents that can resolve an ambiguous slot; empty for an unambiguous slot.
    """
    default_for_today: bool
    eligibility_reasons: list[str]


class ProcessPolicy(NxModel):
    source: Annotated[Literal["catalog", "workspace_document"], Open]
    policy_id: str
    version: str
    title: str
    approval: Annotated[Literal["approved", "draft", "hypothetical", "not_stated"], Open]
    effective_from: date
    effective_to: date | None
    supersedes: str | None
    entity_kinds: list[str]
    availability: Availability
    applicable: bool | None
    governing: Governing | None
    """
    Null for catalog policies. An ambiguous workspace slot is unavailable until a document is selected; its singular document ids, source and status are null.
    """


class ProcessPolicyClause(NxModel):
    locator: str
    heading: str
    text: str


class ProcessPolicyList(NxModel):
    data: list[ProcessPolicy]
    next_cursor: Cursor


class Workflow(NxModel):
    state: Annotated[Literal["ready", "not_read", "invalid"], Open]
    origin: Annotated[Literal["cached", "recorded"], Open] | None
    model_id: str | None
    review: Annotated[Literal["provisional"], Open]


class Locator(NxModel):
    page: int | None
    heading: str
    line: int


class ProcessQuote(NxModel):
    role: Annotated[Literal["supporting", "contradicting", "related", "hold"], Open]
    doc_id: str
    doc_title: str
    quote: str | None
    """
    `null` when withheld.
    """
    start_char: int | None
    """
    Code points into the text identified by `text_sha256`, end-exclusive.
    """
    end_char: int | None
    content_version: str
    parse_key: str
    text_sha256: str
    locator: Locator
    access: Annotated[Literal["readable", "withheld", "changed"], Open]


class ProcessSearchedKey(NxModel):
    key_type: str
    surface: str
    status: Annotated[Literal["accepted", "proposed"], Open]
    strength: Annotated[Literal["strong", "weak"], Open]
    df: int | None


class ProcessSelection(NxModel):
    reason: Annotated[
        Literal[
            "user_selected", "confirmed_upload", "confirmed_discovered", "proposed_discovered", "user_selected_document"
        ],
        Open,
    ]
    provisional: bool
    """
    The policy is a proposal nobody has reviewed.
    """
    governing_document_id: str | None
    document_id: str | None
    content_version: str | None
    source: Annotated[Literal["discovered", "uploaded"], Open] | None
    status: Annotated[Literal["proposed", "confirmed"], Open] | None
    on_date: date | None


AnyOfItem = TypeAliasType("AnyOfItem", Annotated[list[str], Field(min_length=1)])


class ProcessStagePrerequisite(NxModel):
    any_of: Annotated[list[AnyOfItem], Field(min_length=1)]
    mandate: ProcessMandate


class Coverage(NxModel):
    level: Annotated[Literal["complete", "partial", "failed"], Open]
    reasons: list[str]
    documents_in_scope: int
    documents_indexed: int
    unreadable: int


class Occurrence(NxModel):
    occurrence: int | None
    state: str
    label: str
    reason: str
    reason_text: str
    notes: list[str]
    coverage: Coverage


class Engine1(NxModel):
    state: str
    """
    satisfied, exempted, contradicted, not_observed, blocked, not_due, not_applicable, indeterminate or retrieval_failed.
    """
    label: str
    reason: str
    reason_text: str
    occurrences: list[Occurrence]


class Finding(NxModel):
    kind: str
    label: str
    impact: Annotated[Literal["high", "medium", "low"], Open]
    certainty: Annotated[Literal["direct", "scoped_absence", "partial", "unresolved"], Open]
    summary: str
    closes_with: str | None


class ProcessStageResult(NxModel):
    stage_id: str
    order: int
    title: str
    outcome: Annotated[
        Literal["supported", "contradicted", "not_evidenced", "not_applicable", "cannot_determine"], Open
    ]
    basis: Annotated[
        Literal[
            "supporting_evidence",
            "exception",
            "contradicting_evidence",
            "absent_complete_coverage",
            "incomplete_coverage",
            "retrieval_failed",
            "unresolved",
            "not_applicable",
            "not_due",
            "blocked",
        ],
        Open,
    ]
    explanation: str
    engine: Engine1
    findings: list[Finding]
    quotes: list[ProcessQuote]
    clauses: list[ProcessPolicyClause]


class InFile(NxModel):
    state: Annotated[Literal["in_file", "removed", "not_in_file"], Open]
    level: Annotated[Literal["confirmed", "likely", "possible"], Open] | None = None


class ProcessWorkspaceDocument(NxModel):
    doc_id: str
    name: str
    path: str | None
    source_label: str
    modified_at: str | None
    content_version: str | None
    has_text: bool
    in_file: InFile


class ProcessWorkspaceDocumentPage(NxModel):
    data: list[ProcessWorkspaceDocument]
    next_cursor: Cursor


Provider = TypeAliasType("Provider", Annotated[Literal["sharepoint", "s3", "gdrive", "box"], Open])


class Rate(NxModel):
    meter: Meter
    label: Annotated[str, Field(examples=["Documents ingested"])]
    unit: Annotated[str, Field(examples=["per 1K docs"])]
    unit_size: Annotated[int, Field(examples=[1000])]
    price_usd: Annotated[float, Field(examples=[1.2])]
    """
    The price in force: the organization's own price where NVISIONx agreed one, else the list price.
    """


class RegexOptions(NxModel):
    """
    How `regex` mode matches; only with `mode: regex`.
    """

    case_sensitive: bool | None = True
    """
    Inline flags work too: `(?i)` makes the pattern case-insensitive.
    """
    fields: Annotated[list[Annotated[Literal["text", "filename", "path"], Open]] | None, Field(min_length=1)] = ["text"]
    """
    `text`: the passage text · `filename`: the document's file name · `path`: its path in the source.
    """


RetentionStatus = TypeAliasType("RetentionStatus", Annotated[Literal["active", "hold", "expired", "unscheduled"], Open])


Scope = TypeAliasType(
    "Scope",
    Annotated[
        Literal[
            "ingest:read",
            "ingest:write",
            "search:read",
            "search:write",
            "search:compare",
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


class SearchCompareError(NxModel):
    code: Annotated[Literal["timeout", "unavailable", "failed"], Open]
    """
    `timeout`: the engine did not answer in time · `unavailable`: the engine cannot answer for this workspace right now (the next-generation engine is not available for it, or the current engine is still starting up) · `failed`: anything else.
    """
    message: str


class Overlap(NxModel):
    """
    The share (0 to 1) of the baseline's first 10 (`at_10`) and first `limit` (`at_limit`) result ids that are also among the candidate's first 10 (or `limit`). `null` when either side has an `error`, or when neither side returned anything.
    """

    at_10: Annotated[float | None, Field(ge=0.0, le=1.0)]
    at_limit: Annotated[float | None, Field(ge=0.0, le=1.0)]


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


class SnippetRange(NxModel):
    start: Annotated[int, Field(ge=0)]
    end: Annotated[int, Field(ge=0)]
    """
    Exclusive.
    """


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


class TokenUsage(NxModel):
    """
    The language-model tokens an answer used, billed on the `llm_input` and `llm_output` meters.
    """

    input_tokens: int
    """
    Tokens the models read (prompts and retrieved text, cached reads included).
    """
    output_tokens: int
    """
    Tokens the models wrote.
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
    """
    One step of how an answer was made, in order. Messages stored before steps were timed have only `summary` (and `tool`).
    """

    summary: Annotated[str, Field(examples=["Pass 2: searched 3 new queries, 12 new passages"])]
    detail: str | None = None
    tool: McpToolName | None = None
    """
    The tool the step called: `search_records` for a search, `get_record` for reading a whole record. `null` for understanding the question and writing the answer.
    """
    kind: Annotated[Literal["route", "search", "read", "answer"], Open] | None = None
    """
    `route`: understanding the question · `search`: one search pass · `read`: reading a whole record · `answer`: writing and checking the answer after the last tool call.
    """
    at_ms: int | None = None
    """
    When the step started, in milliseconds from the start of the answer.
    """
    duration_ms: int | None = None
    """
    How long the step took, in milliseconds.
    """
    queries: list[str] | None = None
    """
    The searches a `search` step ran, as plain text.
    """


class Classification(NxModel):
    record_id: str | None = None
    record_type: str
    owner: str
    sensitivity: Sensitivity
    retention: Annotated[str, Field(examples=["7y after termination"])]


class Document(NxModel):
    id: Annotated[str, Field(examples=["doc_01J8Z"])]
    source_id: str
    source_name: str
    source_provider: str
    """
    `upload` for uploaded documents, else the connector.
    """
    name: str
    path: str
    web_url: str | None
    """
    Where the document lives in its source system.
    """
    mime: str | None
    size: int
    """
    Bytes.
    """
    version: str | None
    sha256: str | None
    """
    SHA-256 of the stored original, hex. `null` until the original is stored.
    """
    metadata: dict[str, Any] | None
    """
    The metadata sent with the document when it was ingested (`metadata` of ingestDocuments). `null` when none was sent.
    """
    modified_at: AwareDatetime | None
    created_by: str | None
    ingest_status: Annotated[Literal["pending", "ingested", "failed"], Open]
    ingest_error: Annotated[str | None, Field(examples=["The file is larger than 2 GB."])] = None
    """
    Why the document could not be ingested, in words for the person who sent it: set when `ingest_status` is `failed`, else `null`.
    """
    parsed_at: AwareDatetime | None
    chunk_count: int | None
    """
    Chunks the workspace's search index holds for the document. `null` until an index reports it.
    """
    status: DocumentStatus
    deleted_at: AwareDatetime | None
    deleted_reason: DocumentDeletedReason | None
    data_purged_at: AwareDatetime | None
    """
    When a deleted document's original and parsed text were removed. `null` while they are kept.
    """
    created_at: AwareDatetime


class DocumentDetail(Document):
    events: list[DocumentEvent]


class DocumentFilter(NxModel):
    """
    Live documents matching every field given. An empty filter matches every live document.
    """

    source_id: str | None = None
    q: Annotated[str | None, Field(max_length=200)] = None
    """
    Matches the name or path, case-insensitively.
    """
    modified_after: AwareDatetime | None = None
    modified_before: AwareDatetime | None = None
    stage: DocumentStage | None = None


class DocumentList(NxModel):
    data: list[Document]
    next_cursor: Cursor


class DocumentReparseRequest(NxModel):
    """
    `ids` or `filter`, not both.
    """

    ids: Annotated[list[str] | None, Field(max_length=200, min_length=1)] = None
    filter: DocumentFilter | None = None
    expected_count: Annotated[int | None, Field(ge=0)] = None
    """
    Required with `filter` unless `dry_run`: the failed documents you expect it to re-parse.
    """
    dry_run: bool | None = False
    """
    Count what would be re-parsed; queue nothing.
    """


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
    reason: str | None = None
    """
    Why a service was unavailable, when known: `capacity` means our service hit a capacity limit with its AI model provider (Retry-After says when to try again). Process Map reasons: `entity_index_unavailable`, `registry_unavailable`, `document_text_unavailable`, `policy_unavailable`, `stale_cursor`, `registry_conflict`, `content_changed`, `stale_input`, `policy_not_applicable` and `capacity`; invalid link changes use `already_in_file`, `not_in_file` or `invalid_reason`. Other validation failures use the returned detail. Governing document reasons: `discovery_disabled`, `governing_conflict`, `governing_type_invalid`, `governing_type_not_uploadable`, `governing_source_invalid`, `governing_metadata_incomplete`, `governing_field_invalid`, `governing_transition_invalid`, `governing_types_unavailable`, `policy_ambiguous`, `policy_content_changed`, `registry_unavailable`.
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


class GoverningDiscovery(NxModel):
    enabled: bool
    available: bool
    unavailable_reason: (
        Annotated[Literal["classifier_unavailable", "registry_unavailable", "knowledge_hub_unavailable"], Open] | None
    )
    can_change: bool
    """
    Whether you can turn discovery on or off.
    """
    latest_run: GoverningDiscoveryRun | None
    active_run: GoverningDiscoveryRun | None


class EmbeddedRole(NxModel):
    type: str
    quote: GoverningQuote


class GoverningField(NxModel):
    value: str | None
    origin: Annotated[Literal["extracted", "uploader", "reviewer"], Open] | None
    status: Annotated[Literal["verified", "supplied", "not_stated", "rejected"], Open]
    reason: str | None
    quote: GoverningQuote | None


class Job(NxModel):
    id: Annotated[str, Field(examples=["job_7Hq2xK"])]
    source: Annotated[Literal["api", "upload", "sharepoint", "s3", "gdrive", "box"], Open]
    source_id: str | None = None
    documents: int
    status: JobStatus
    progress: Annotated[int, Field(ge=0, le=100)]
    """
    Documents ingested (searchable) as a percentage of all of them.
    """
    parsed: Annotated[int | None, Field(ge=0)] = None
    """
    Documents the parser has finished with (read, or failed to read). A `running` job with `parsed` below `documents` is parsing; one with every document parsed is waiting for the workspace's index to be built.
    """
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
    """
    What went wrong, in one line: `No document could be ingested.` or `2 of 10 documents could not be ingested.`. `failures` says which and why.
    """
    failures: Annotated[list[JobFailure] | None, Field(max_length=20)] = None
    """
    Up to 20 of the job's documents that failed, with why, oldest first. Empty while none has.
    """
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
    by_model: list[ByModelItem] | None = None
    """
    `llm_input` and `llm_output`: the quantity and cost per model. For these meters `price_usd` is the price of the first model in the organization's order; each model's price is in listModels.
    """


class Model(NxModel):
    id: Annotated[str, Field(examples=["us.anthropic.claude-opus-5-5"])]
    name: Annotated[str, Field(examples=["Claude Opus 5.5"])]
    vendor: Annotated[str, Field(examples=["Anthropic"])]
    roles: list[ModelRole]
    status: Annotated[Literal["available", "deprecated"], Open]
    """
    `deprecated`: still answers; move off it.
    """
    input_price_per_1m_usd: float
    """
    What this organization pays per 1M input tokens.
    """
    output_price_per_1m_usd: float
    """
    What this organization pays per 1M output tokens.
    """
    allowed: bool
    """
    The workspace's answers may use it.
    """
    blocked_by: Annotated[Literal["vendor", "model"], Open] | None
    """
    Why it is not allowed: its vendor or the model itself is blocked by the organization.
    """


class ModelList(NxModel):
    data: list[Model]
    preferred: list[str]
    """
    The order answers try models in: the first, then each fallback.
    """
    router: str | None
    """
    The allowed model that plans questions. `null`: none is allowed, so planning is skipped.
    """


class Input(NxModel):
    snapshot_id: str
    input_key: str
    documents: Documents
    coverage: ProcessEvidenceCoverage


class ProcessAssessment(NxModel):
    id: Annotated[str, Field(examples=["pas_01k6c1x0d8f9g2h3j4k5m6n7p8"])]
    entity_id: str
    policy: Policy
    status: Annotated[Literal["queued", "running", "completed", "failed", "cancelled"], Open]
    phase: str
    progress: Progress
    completeness: Annotated[Literal["complete", "partial"], Open] | None
    current: bool
    """
    The assessment's input matches what an assessment would read now.
    """
    failure: Failure | None
    requested_by: RequestedBy
    as_of: date
    created_at: AwareDatetime
    started_at: AwareDatetime | None
    finished_at: AwareDatetime | None
    input: Input
    engine: Engine | None
    results: list[ProcessStageResult] | None
    """
    Completed assessments only; `null` in lists.
    """
    selection: ProcessSelection


class ProcessAssessmentInput(NxModel):
    entity: ProcessEntityRef
    policy: ProcessPolicy
    applicable: bool
    not_applicable_reason: str | None
    inclusion_rule: Annotated[Literal["confirmed_and_likely"], Open]
    snapshot_id: str
    input_key: str
    build_id: str
    registry_version: int
    document_ids: list[str]
    documents: Documents
    coverage: ProcessEvidenceCoverage


class ProcessAssessmentPage(NxModel):
    data: list[ProcessAssessment]
    next_cursor: Cursor
    current_input_key: str | None


class ProcessEntity(ProcessEntityRef):
    created_by: str | None
    provenance: list[str]
    aliases: list[ProcessEntityAlias]
    registry_version: int
    build_id: str


class ProcessEntityCoverage(NxModel):
    """
    Whole-file coverage after access filtering. `null` means unknown, never complete.
    """

    keys_searched: list[ProcessSearchedKey] | None
    keys_pending_extraction: list[ProcessPendingKey] | None
    sources_searched: list[str] | None
    sources_not_connected: list[str] | None
    unconnected_structure: list[str] | None
    counts: Counts1 | None
    unplaced_attachments: int | None
    complete: bool | None
    complete_reason: str | None


class ProcessEntityDocument(NxModel):
    doc_id: str
    urn: str | None
    title: str | None
    filename: str | None
    path: str | None
    source_type: str
    doc_date: str | None
    content_version: str | None
    section: str
    level: Annotated[Literal["confirmed", "likely", "possible"], Open]
    level_reason: str
    decision: ProcessLinkDecision | None
    mentions: list[ProcessMention]
    via: Via | None
    thread: Thread | None
    unplaced_attachments: list[str]


class ProcessEntityFilePage(NxModel):
    entity: ProcessEntityRef
    build_id: str
    registry_version: int
    coverage: ProcessEntityCoverage
    sections: list[Section]
    data: list[ProcessEntityDocument]
    next_cursor: Cursor


class ProcessEntityPage(NxModel):
    data: list[ProcessEntitySummary]
    next_cursor: Cursor
    total: int | None


class ProcessPolicyStage(NxModel):
    """
    A step of the policy workflow. `prerequisites` and `starts_after` carry the order the policy sets between steps; an `inferred` mandate means it was read from context rather than stated.
    """

    stage_id: str
    order: int
    title: str
    description: str
    clause_locators: list[str]
    mandate: ProcessMandate
    prerequisites: list[ProcessStagePrerequisite]
    """
    Every group must be met before this step; a group is met when all stages of any one option are.
    """
    starts_after: str | None
    """
    Stage whose completion starts this step, when the policy times it that way.
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


class SearchCompareRequest(NxModel):
    """
    A `SearchRequest` without `cursor`, checked the same way.
    """

    query: Annotated[str, Field(min_length=1)]
    """
    Natural-language or keyword query. In `regex` mode, an RE2 regular expression of at most 1,000 characters (no backreferences or lookaround).
    """
    sources: list[str] | None = None
    """
    Limit to these source IDs. Default: every source the token can read.
    """
    mode: Annotated[Literal["hybrid", "semantic", "keyword", "regex"], Open] | None = "hybrid"
    """
    As in `SearchRequest`. Both sides run the same mode.
    """
    regex: RegexOptions | None = None
    filters: Filters | None = None
    limit: Annotated[int | None, Field(ge=1, le=100)] = 10
    """
    Results per side.
    """


class SearchRequest(NxModel):
    query: Annotated[str, Field(min_length=1)]
    """
    Natural-language or keyword query. In `regex` mode, an RE2 regular expression of at most 1,000 characters (no backreferences or lookaround).
    """
    sources: list[str] | None = None
    """
    Limit to these source IDs. Default: every source the token can read.
    """
    mode: Annotated[Literal["hybrid", "semantic", "keyword", "regex"], Open] | None = "hybrid"
    """
    `hybrid`: keyword and semantic results fused, then reranked · `semantic`: by meaning only (vector similarity) · `keyword`: by terms only (BM25) · `regex`: documents with a passage matching `query` as a regular expression, one result each (its passage with the most matches), most matches first. Every mode pages (`cursor`) and keeps to the sources and permissions of the token.
    """
    regex: RegexOptions | None = None
    cursor: str | None = None
    """
    The `next_cursor` of the previous page, in any mode. Send the same `query`, `mode`, `regex`, `sources`, `filters` and `limit` as that page; a cursor from another search is a 400 on `cursor`. Each page runs the search again, so documents changed since the previous page may move.
    """
    filters: Filters | None = None
    limit: Annotated[int | None, Field(ge=1, le=100)] = 10
    """
    Documents per page, one result each, in every mode. A page is short only when it is the last.
    """


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
    match_count: int | None = None
    """
    Regex mode: how many times the pattern matched in this result's best passage, over the searched fields.
    """
    highlights: list[SnippetRange] | None = None
    """
    Regex mode: the parts of `snippet` that matched, as character offsets (Unicode code points). Empty in the other modes.
    """


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
    usage: TokenUsage | None = None
    model: str | None = None
    """
    The model that wrote the answer (its name).
    """
    notices: list[ChatNotice] | None = None
    """
    What the user should know about how the answer was produced, in order (empty when nothing happened).
    """
    cost_usd: float | None = None
    """
    What the answer cost: its tokens (tool calls are not billed on their own).
    """
    duration_ms: int | None = None
    """
    How long the answer took, in milliseconds. `null` on answers stored before it was recorded.
    """
    created_at: AwareDatetime


class ChatStreamEvent(NxModel):
    """
    One server-sent event of `sendChatMessage`. `status`: what the agent is doing now · `step`: a finished reasoning step · `notice`: something the user should be told now, such as our service hitting a capacity limit with its AI model provider and waiting to retry · `delta`: answer text to append · `complete`: the stored assistant message · `error`: the answer failed (nothing is billed for an answer that never started).
    """

    type: Annotated[Literal["status", "step", "notice", "delta", "complete", "error"], Open]
    status: str | None = None
    step: ChatReasoningStep | None = None
    notice: ChatNotice | None = None
    text: str | None = None
    message: ChatMessage | None = None
    error: str | None = None
    code: Annotated[Literal["capacity"], Open] | None = None
    """
    On `error`, why when it is known: `capacity` means our service hit a capacity limit with its AI model provider; trying again in a minute usually works.
    """


class DocumentDeleteRequest(NxModel):
    """
    `ids` or `filter`, not both.
    """

    ids: Annotated[list[str] | None, Field(max_length=200, min_length=1)] = None
    filter: DocumentFilter | None = None
    expected_count: Annotated[int | None, Field(ge=0)] = None
    """
    Required with `filter` unless `dry_run`: the documents you expect it to delete.
    """
    dry_run: bool | None = False
    """
    Count what would be deleted; delete nothing.
    """


class GoverningDocument(NxModel):
    id: Annotated[str, Field(examples=["gdoc_01k6c1x0d8f9g2h3j4k5m6n7p8"])]
    governing_type: str
    type_origin: Annotated[Literal["classifier", "uploader", "reviewer"], Open]
    status: Annotated[Literal["proposed", "confirmed", "rejected"], Open]
    source: Annotated[Literal["discovered", "uploaded"], Open]
    active: bool
    inactive_reason: (
        Annotated[Literal["text_pending", "content_changed", "document_unreadable", "discovery_off"], Open] | None
    )
    """
    `text_pending`: an uploaded document that is not searchable yet.
    """
    eligibility: Eligibility
    document: Document1
    title: GoverningField
    version: GoverningField
    effective_from: GoverningField
    effective_to: GoverningField
    supersedes: GoverningField
    approval: GoverningField
    owner: GoverningField
    confidence: Annotated[Literal["high", "medium", "low"], Open] | None
    """
    The classifier's own rating; not a probability.
    """
    review_signal: Annotated[Literal["ready", "needs_review", "not_selectable"], Open] | None
    """
    Null for uploaded documents. Candidates whose classification is unresolved have no row; they are counted on the discovery run.
    """
    review_reasons: list[str]
    type_quote: GoverningQuote | None
    embedded_roles: list[EmbeddedRole]
    reading: Reading | None
    revision: int
    registry_version: int
    created_at: AwareDatetime
    created_by: GoverningActor
    decided_at: AwareDatetime | None
    decided_by: GoverningActor | None


class GoverningDocumentPage(NxModel):
    data: list[GoverningDocument]
    next_cursor: Cursor


class McpServer(NxModel):
    url: Annotated[str, Field(examples=["https://platform.us.nvisionx.ai/mcp"])]
    """
    The same URL for every workspace (the deployment's MCP resource). The credential selects the workspace.
    """
    status: Annotated[Literal["online", "degraded", "offline"], Open]
    oauth: Oauth
    tools: list[McpTool]
    price_per_1k_calls_usd: float
    """
    What 1K calls of the tools other than summarize_records cost.
    """
    price_per_1m_input_tokens_usd: float
    """
    What 1M language-model input tokens cost (summarize_records).
    """
    price_per_1m_output_tokens_usd: float
    """
    What 1M language-model output tokens cost.
    """


class ProcessPolicyPreview(NxModel):
    policy: ProcessPolicy
    workflow: Workflow
    stages: list[ProcessPolicyStage]
    clauses: list[ProcessPolicyClause]


class SearchCompareSide(NxModel):
    """
    One search engine's answer.
    """

    results: list[SearchResult]
    """
    As `search` returns them. Empty when `error` is set.
    """
    total: int
    """
    Regex mode: every document the pattern matches. Other modes: the results returned.
    """
    total_is_lower_bound: bool
    """
    Regex mode: true when the engine stopped counting early, so there are at least `total` matching documents. False in the other modes.
    """
    took_ms: int
    """
    How long this engine took.
    """
    error: SearchCompareError | None
    """
    Why this side has no results; `null` when it answered.
    """


class SearchResponse(NxModel):
    took_ms: int
    total: int
    """
    The documents available over all pages (one result each), or a lower bound on them (`total_is_lower_bound`). Regex mode: every document the pattern matches. Other modes: the ranked documents the search can page through, at most 1,000 for `keyword` and `semantic` and 200 for `hybrid` (the pool it reranks). Other modes look one document past the page, so while more pages follow `total` is usually the documents so far plus one, a lower bound; it is exact once the ranking ends before the cap, and at the cap it is the cap, with no page past it.
    """
    total_is_lower_bound: bool
    """
    True when there may be more documents than `total`: in `hybrid`, `semantic` and `keyword` while more pages follow or at the cap; in `regex` when the engine stopped counting early.
    """
    cost_usd: float | None = None
    results: list[SearchResult]
    """
    This page: one result a document (its best passage), best first. Ranks continue from the previous page, and a document is on one page only (unless it changed between pages).
    """
    next_cursor: str | None = None
    """
    Send it as `cursor` for the next page, in any mode; `null` on the last page. Each page runs the search again and is billed as a search.
    """


class ChatConversationDetail(NxModel):
    conversation: ChatConversation
    messages: list[ChatMessage]


class SearchCompareResponse(NxModel):
    query: str
    mode: Annotated[Literal["hybrid", "semantic", "keyword", "regex"], Open]
    took_ms: int
    """
    The whole comparison.
    """
    cost_usd: float | None = None
    """
    What the call cost (one `search` query).
    """
    baseline: SearchCompareSide
    candidate: SearchCompareSide
    overlap: Overlap
    """
    The share (0 to 1) of the baseline's first 10 (`at_10`) and first `limit` (`at_limit`) result ids that are also among the candidate's first 10 (or `limit`). `null` when either side has an `error`, or when neither side returned anything.
    """
    only_baseline: list[str]
    """
    The ids of the results only the baseline returned, in its order. Empty when either side has an `error`.
    """
    only_candidate: list[str]
    """
    The ids of the results only the candidate returned, in its order. Empty when either side has an `error`.
    """
