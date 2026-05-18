# App factory logs page and detail discovery result

## Summary

The LLM Factory Logs UI is not in `novaic-app/src`; it lives in `novaic-llm-factory/static/factory-logs.html` and is deployed separately. The table/list API is already bounded because `/v1/logs` omits bodies, and `/v1/logs/{log_id}` bounds request/response bodies by default. However the static detail page still renders raw request/response JSON and message/tool content with only simple character slicing, not binary/media scrubbing. This is a remediation candidate because old or malformed logs can still show `_mcp_content`/base64-like payload prefixes in both visual and raw tabs.

## Done

- Scanned `novaic-app/src` for factory-log/raw JSON UI and confirmed the factory logs page is not part of the app frontend.
- Expanded discovery to the whole repository and located the real factory logs page at `novaic-llm-factory/static/factory-logs.html`.
- Inspected the static page renderers, log routes, log snapshot contract, and log-route tests.
- Classified list vs detail behavior and identified exact remediation candidates.

## Verification

- Scan artifact: `.complex-problems/L20260516-222011/tmp/p776-factory-log-scan.txt`.
- Evidence artifact: `.complex-problems/L20260516-222011/tmp/p776-factory-log-evidence.txt`.
- `docs/architecture/agent-pipeline.md` and `docs/runbooks/cloud-production.md` point the Factory Logs page at `novaic-llm-factory/static/factory-logs.html`.
- `novaic-llm-factory/factory/routes/log_routes.py` has `/v1/logs` call `query_logs(..., include_bodies=False)`, so the table/list path does not fetch full request/response bodies.
- `novaic-llm-factory/factory/routes/log_routes.py` bounds detail request/response bodies to 20,000 chars by default and 200,000 max.
- `novaic-llm-factory/factory/contracts.py` redacts provider-native `image_url` data URLs and Anthropic-style `image.source.data` base64 in request log snapshots.
- `novaic-llm-factory/tests/test_log_routes.py` covers omitted list bodies, default detail truncation, explicit smaller body limits, and multimodal request-body redaction.
- `novaic-llm-factory/static/factory-logs.html` lines 376-379 slice message content to 2,000 chars but do not detect or replace `_mcp_content`, data URLs, or binary/base64-looking payload text.
- `novaic-llm-factory/static/factory-logs.html` lines 387-396 render tool-call arguments verbatim except JSON pretty-printing.
- `novaic-llm-factory/static/factory-logs.html` lines 567-579 render raw request/response bodies verbatim after backend truncation.

## Known Gaps

- Remediation candidate: add shared client-side safe rendering/scrubbing in `novaic-llm-factory/static/factory-logs.html` for visual message content, tool-call arguments, raw request body, and raw response body. It should replace base64/data URL/binary-looking payloads and `_mcp_content` envelopes with concise placeholders while preserving useful BlobRef/artifact/text diagnostics.
- Remediation candidate: add factory-log tests or a lightweight static-source guard so future raw/base64 renderer regressions are caught. Current tests cover backend redaction/truncation but not static page UI scrubbing.
- No files were modified in this discovery child.

## Artifacts

- `.complex-problems/L20260516-222011/tmp/p776-factory-log-scan.txt`
- `.complex-problems/L20260516-222011/tmp/p776-factory-log-evidence.txt`
