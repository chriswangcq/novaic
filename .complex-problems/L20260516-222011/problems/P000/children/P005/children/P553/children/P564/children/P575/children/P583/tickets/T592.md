# Ticket: Audit Display Monitor and UI Projection Boundary

## Problem Definition

Human-facing monitor/factory-log UI may show truncated tool output, previews, or thumbnails. That rendering boundary must be clearly separate from LLM request context so UI truncation does not hide raw media bytes being sent to the model, and UI display does not persist unredacted image base64.

## Proposed Solution

Scan monitor, factory logs, and UI rendering code for display/tool result rendering, truncation, raw JSON views, base64/image handling, and BlobRef/thumbnail behavior. Read relevant slices and classify whether each path is human preview only or LLM-context-affecting.

## Acceptance Criteria

- Exact scan commands are recorded.
- Relevant UI/log rendering slices are cited with line references.
- Human UI preview/truncation is separated from LLM request context in the result.
- Any path that stores or renders unredacted raw image bytes is forwarded as a follow-up.

## Verification Plan

Use read-only scans and line-slice inspection. If tests already cover UI rendering boundaries, cite them; otherwise record that this is a code audit rather than a runtime UI test.

## Risks

- Frontend code may intentionally show raw JSON for debugging; the audit must distinguish dangerous storage/transmission from bounded human-only debug rendering.

## Assumptions

- LLM request context correctness is already covered by P581/P582; this ticket focuses on human monitor/log surfaces.
