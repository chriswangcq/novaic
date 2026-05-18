# PR-80 — Enforce single summary writer: only `skill_end(report=...)`

| Field | Value |
| --- | --- |
| Status | `[x]` done |
| Severity | P1 memory correctness |
| Owner | Codex |
| Branch | `codex/focus-new-llm-context` |

## Problem

`/v1/scope/end` still accepts a `report` field for historical compatibility even though structural close must not write `summary.md`. Keeping the field accepted makes it look like a second summary channel.

## Desired Contract

- `/v1/context/skill_end` is the only API that persists `report` into `summary.md`.
- `/v1/scope/end` is structural only.
- Non-empty `/v1/scope/end.report` is rejected with a clear error.
- Runtime finalization sends no report.

## Implementation Checklist

- [x] Reject non-empty `ScopeEndRequest.report` in Cortex API.
- [x] Keep empty/missing report idempotent for runtime finalize.
- [x] Update Cortex tests that previously expected ignored reports.
- [x] Update runtime tests to assert no report reaches structural close.

## Unit Tests

- [x] Cortex API rejects non-empty structural `scope_end.report`.
- [x] Cortex API still accepts empty structural `scope_end.report`.
- [x] `context_skill_end(report=...)` still writes exact `summary.md`.
- [x] Runtime finalize payload has no report content.

## Smoke Test

- [x] Remote `/v1/scope/end` with non-empty report returns client error.
- [x] Remote `/v1/context/skill_end` still writes and folds summary.

## Deployment

- [x] Deploy Cortex.
- [x] Deploy agent-runtime if payload shape changed.

## GitHub / Commit Work

- [x] Commit `novaic-cortex` changes.
- [x] Commit `novaic-agent-runtime` changes if touched.
- [x] Commit parent repo submodule pointers and ticket.
- [x] Push branches.
