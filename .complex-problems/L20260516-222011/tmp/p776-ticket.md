# App factory logs page and detail discovery ticket

## Problem Definition

The factory logs frontend may still expose raw request/response bodies, `_mcp_content`, display tool result payloads, or base64 media through its table/detail/raw JSON UI instead of showing bounded debug text and BlobRef/artifact references.

## Proposed Solution

Discover factory-log frontend files and inspect the list fetch path, table rendering, detail modal/raw JSON tabs, response/request display helpers, and tests. Classify all suspicious hits for raw JSON, request body, response body, `_mcp_content`, base64, BlobRefs, artifacts, display results, and truncation.

## Acceptance Criteria

- Factory-log page, hook/service, table, detail modal, raw JSON, and API-client files are discovered.
- Suspicious raw payload and media hits are classified by exact file/path.
- Remediation candidates are listed if the UI still leaks or misrepresents payloads.
- No factory-log UI files are modified.

## Verification Plan

Run bounded `rg --files` and focused `rg -n -i` scans under `novaic-app/src`, then inspect high-signal factory-log files with `sed`/`nl`.

## Risks

- Raw JSON may be intentionally available for debugging, so the classification must distinguish acceptable raw debug views from broken or empty detail rendering.
- Some factory-log data may originate from backend schemas outside the app; this ticket only discovers the app-facing slice.

## Assumptions

- The factory logs UI is implemented in `novaic-app/src` and named with factory/log/llm/detail/raw terminology.
