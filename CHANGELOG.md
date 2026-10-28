# Changelog

## 0.2.0

Models regenerated from the current API spec. Regex search mode (`mode="regex"` with `regex` options), search
highlights and `total_is_lower_bound`, chat notices and the `notice` stream event, per-stage document counts in
the documents summary, a document's ingest error, job failures and ingest progress, usage by model, plus models
for the governing documents, process assessment and model catalog endpoints. Uploads are limited to 1–100 files per
request, matching the server.

## 0.1.0

First release. Sync and async clients for the Nx Platform API data plane: ingest, documents (list, parsed text,
summary, delete), jobs, search, agents, chat (with streaming), data sources, MCP settings, usage and budgets.
