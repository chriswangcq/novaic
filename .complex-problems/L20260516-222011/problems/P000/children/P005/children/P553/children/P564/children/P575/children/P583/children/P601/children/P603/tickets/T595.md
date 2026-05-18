# Ticket: Audit Backend Agent Progress Preview Payloads

## Problem Definition

Backend monitor/progress events should send bounded summaries, status, and references. They must not carry raw unredacted image bytes from tool results.

## Proposed Solution

Scan backend queue/runtime/business code for progress events, agent monitor payloads, tool result summaries, and truncation. Read relevant slices and classify the boundary.

## Acceptance Criteria

- Exact scan commands are recorded.
- Backend slices showing bounded summaries or references are cited.
- Result separates monitor events from LLM request context.
- Follow-up is created if raw image bytes can be emitted in monitor progress events.

## Verification Plan

Read-only audit with `rg` and line-numbered slices; run focused backend tests only if directly available.

## Risks

- Some event fields may be named `content` or `summary`; classify based on producer and consumer path, not just field name.

## Assumptions

- The monitor event stream is not part of model context assembly.
