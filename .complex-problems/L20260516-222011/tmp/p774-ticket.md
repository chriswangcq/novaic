# App factory log and raw JSON detail discovery ticket

## Problem Definition

Factory log, Monitor detail, and raw JSON UI code may still surface raw tool payloads, `_mcp_content`, base64 media strings, or unprojected request/response bodies instead of compact shell text and BlobRef/artifact manifests.

## Proposed Solution

Run bounded source discovery under `novaic-app/src` for factory log, monitor, activity timeline, raw JSON detail, request/response, truncation, BlobRef, display, and base64 handling. Inspect high-signal files and classify each suspicious path as either contract-compliant projection/scrubbing, legitimate UI-only rendering, or a remediation candidate.

## Acceptance Criteria

- Relevant factory log, monitor, raw JSON, request/response detail, and truncation files are discovered.
- Suspicious `_mcp_content`, raw JSON, request/response body, display result, base64, BlobRef, artifact, and truncation hits are classified.
- Exact remediation candidates are listed, or absence is explicitly recorded.
- No frontend/log UI files are modified.

## Verification Plan

Use `rg --files`, focused `rg -n -i`, and targeted file slices under `novaic-app/src`. Cross-check any guard tests or projection tests that claim to prevent raw payload exposure.

## Risks

- Factory logs may intentionally preserve raw request/response JSON for debugging; classify this separately from user-facing Monitor or chat display leakage.
- Truncation code can mask symptoms while the underlying projection contract remains wrong, so raw source classification must identify whether payloads are sanitized before UI display.

## Assumptions

- App frontend code for the user-visible logs and Monitor lives under `novaic-app/src`.
- Backend LLM factory persistence is outside this child unless referenced by app-facing contracts.
