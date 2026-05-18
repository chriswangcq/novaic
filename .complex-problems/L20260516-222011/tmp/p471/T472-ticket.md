# Session explicit-boundary final verification ticket

## Problem Definition

P466 needs final verification after inventory, remediation, duplicate cleanup, and follow-up reruns. This ticket must prove the hidden-input/duplicate-config audit is closed with current code.

## Proposed Solution

Run aggregate guards for runtime env reads, retained `ServiceConfig` classification, react saga decision adapter cleanliness, duplicate residue, and focused tests covering session FSM/outbox/runtime contracts. Save all artifacts under `.complex-problems/L20260516-222011/tmp/p471/`.

## Acceptance Criteria

- Guard artifacts are saved and clean or explicitly classified.
- Focused tests pass.
- Each P466 success criterion is mapped to evidence.
- Any residual risk is explicit and non-blocking.

## Verification Plan

Run `rg` guards and focused pytest suites from correct working directories. Inspect logs before recording the result.

## Risks

- Running relative-path tests from repo root will fail; use `novaic-agent-runtime` as cwd for runtime guard tests.

## Assumptions

- This is verification-only; no further code edits should be needed unless the checks expose a real issue.
