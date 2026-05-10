# Old data reset and no-compat behavior

## Problem Definition

Event-backed prepare/status currently treats a missing event stream as an empty projection. That is too ambiguous for full cutover: legacy-only roots could silently produce empty context instead of forcing an explicit reset/no-compat path.

## Proposed Solution

- Make `ContextEventReadModel` fail fast when a non-empty root scope path has no ContextEvents.
- Add a domain exception that communicates reset/no-compat is required.
- Translate that exception in active API prepare/status usage paths to an explicit HTTP 409/reset-required error.
- Add tests proving legacy-only materialized roots do not fall back to DFS and do not silently return empty context.

## Acceptance Criteria

- Missing/empty event logs for active prepare/status usage raise explicit reset-required behavior.
- No DFS fallback is attempted in reset-required cases.
- Tests cover read model, prepare endpoint, and status include-usage endpoint.
- Full Cortex suite passes.

## Verification Plan

- Run focused reset/no-compat tests.
- Run read-source guard tests.
- Run full Cortex tests.

## Risks

- Existing tests that create scopes directly through projection helpers may need migration to event-writing APIs.
- HTTP status/detail shape should be stable enough for callers to recognize reset-required.

## Assumptions

- Old data compatibility is intentionally not supported.
- Callers can recover by creating a fresh event-backed wake/root rather than asking Cortex to infer events from old files.
