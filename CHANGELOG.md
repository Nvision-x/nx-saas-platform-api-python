# Changelog

## 0.3.0

Models regenerated from the current API spec.

- Search: `mode="regex"` is now accepted by `search`, with `regex=` options (a `RegexOptions` or a dict) including
  `patterns` (several RE2 patterns at once, instead of `query`), `require` (`any` or `all`) and
  `passages_per_document`. Results carry `passages`, per-document counts (`document_match_count`,
  `document_passage_count`, `document_pattern_counts`, `counts_are_lower_bound`), per-pattern `pattern_counts`, and
  each highlight's `pattern`. New `dense_mode` (`auto`, `full`, `fast`) and `cursor` for paging any mode with
  `next_cursor`. `query` is optional, since `regex.patterns` can replace it.
- Documents: `documents.matches` finds every match of several patterns in one document's parsed text, paged;
  `documents.chunks` lists how a document was chunked for search, paged; `documents.parsed(offset=)` reads the parsed
  text past the first 1 MB, and `documents.parsed_text` downloads all of it; `documents.reparse` re-parses failed
  documents by id or filter. Documents carry `failure_stage`.
- `jobs.summary()` and `models.list()`.
- Tokens that reach several workspaces: the `workspace` client option (or `NX_WORKSPACE`) sends `Nx-Workspace` on
  every call, and `with_options(workspace=…)` switches workspace on a copy that shares the connection pool. Setting
  the header through `default_headers` keeps working.
- Pages expose the whole response of each page as `page.body` (for example `total` on chunks, `cost_usd` on
  matches).
- The README covers authentication, workspaces and short-lived tokens issued by the MCP server's `create_api_token`
  tool.

## 0.2.0

Models regenerated from the current API spec. Regex search mode (`mode="regex"` with `regex` options), search
highlights and `total_is_lower_bound`, chat notices and the `notice` stream event, per-stage document counts in
the documents summary, a document's ingest error, job failures and ingest progress, usage by model, plus models
for the governing documents, process assessment and model catalog endpoints. Uploads are limited to 1–100 files per
request, matching the server.

## 0.1.0

First release. Sync and async clients for the Nx Platform API data plane: ingest, documents (list, parsed text,
summary, delete), jobs, search, agents, chat (with streaming), data sources, MCP settings, usage and budgets.
