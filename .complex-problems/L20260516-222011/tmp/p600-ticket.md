# Ticket: Audit Factory Log Request Context Boundary

## Problem Definition

Factory logs should reflect actual LLM request/response records. If display image bytes appear there, they must be part of a deliberate provider request payload, not leaked monitor preview text or stale tool result storage.

## Proposed Solution

Scan backend and frontend factory-log code for request/response persistence, raw JSON detail rendering, image/base64 fields, and API fetch paths. Read relevant slices and classify the boundary.

## Acceptance Criteria

- Exact scans for factory-log API/storage/UI code are recorded.
- Backend slices show what request/response fields are persisted.
- Frontend raw JSON slices show it renders stored call records, not monitor previews.
- Any unexpected raw media persistence is recorded as a follow-up.

## Verification Plan

Read-only code audit using `rg`, `nl`, and bounded slices. Run focused tests only if factory-log tests exist and are directly relevant.

## Risks

- Factory logs may legitimately contain provider-ready image payloads for current display perception; the result must distinguish that from accidental raw tool text.

## Assumptions

- The desired boundary is transparent observability of LLM requests, not redaction of legitimate provider payloads.
