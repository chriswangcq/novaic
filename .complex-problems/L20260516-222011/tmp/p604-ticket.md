# Ticket: Audit Frontend Agent Monitor Timeline Preview

## Problem Definition

The frontend Agent Monitor/timeline must render tool output as safe human UI: escaped, bounded, and artifact-aware. It must not be treated as proof of what was sent to the LLM, and it must not render raw unredacted image/base64 text from tool results as a giant timeline blob.

## Proposed Solution

Scan frontend and UI-serving code for Agent Monitor timeline, step detail modal, raw JSON/detail views, truncation helpers, artifact/image rendering, and any base64/data URL display paths. Capture exact line-numbered slices and run focused UI/frontend tests if available. Classify whether UI presentation is bounded/escaped and separate from LLM request context.

## Acceptance Criteria

- Exact scans are recorded for timeline, tool result, detail/modal, truncation, base64/image, and artifact rendering paths.
- Frontend slices demonstrate escaping/truncation or artifact-specific rendering behavior.
- The result explicitly states that UI presentation is separate from LLM request context.
- A follow-up is created if frontend can render raw unredacted image bytes from tool text.

## Verification Plan

Use `rg` plus line-numbered source slices. Run focused frontend/unit tests when directly available; otherwise record the absence of relevant tests as a gap for problem-level checking.

## Risks

- UI code may be split between static HTML, app frontend packages, and generated schema-driven surfaces.
- Raw JSON/detail views may intentionally display stored content; classify them separately from timeline preview rendering.

## Assumptions

- This is an audit first. Production code changes require a spawned child problem if a concrete frontend bug is found.
