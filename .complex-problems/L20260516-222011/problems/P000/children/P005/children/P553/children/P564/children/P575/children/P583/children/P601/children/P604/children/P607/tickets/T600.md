# Ticket: Audit Detail Modal and Raw JSON Rendering

## Problem Definition

Detail/modal/raw JSON surfaces are allowed to be more diagnostic than normal timeline previews, but they still must escape user-controlled content, bound very large request/response bodies, and remain clearly separate from actual LLM request construction.

## Proposed Solution

Scan Agent Monitor, ActivityTimeline modal, and LLM Factory Logs raw/detail views for raw JSON rendering, modal/detail components, truncation, escaping, and request/response body display. Capture exact line-numbered slices and run focused tests where available.

## Acceptance Criteria

- Exact scans are recorded for raw/detail/modal rendering paths.
- Slices show escaping, bounded body rendering, or explicit raw-inspection constraints.
- Result distinguishes debug/raw UI views from LLM request context assembly.
- A follow-up is created if unescaped HTML or unbounded raw image/base64 text can be rendered in detail views.

## Verification Plan

Use source inspection and focused tests for ActivityTimeline modal and factory log redaction/bounds when available. If a raw UI path lacks tests, record it as a gap for checking.

## Risks

- Factory logs raw JSON views intentionally display stored request/response JSON, so the audit must distinguish “escaped raw inspection” from “unsafe HTML injection”.
- Some detail views may be static HTML without unit tests.

## Assumptions

- Raw/detail views are allowed to show escaped diagnostic text up to explicit limits; they should not silently become model context.
