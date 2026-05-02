# PR-174 — Remove Execution Logs Diagnostic Entity Tail

| Field | Value |
| --- | --- |
| Status | `[closed]` |
| Owner | Codex |
| Created | 2026-05-02 |
| Repos | `novaic-common`, `novaic-business`, `novaic-agent-runtime`, docs |
| Depends on | PR-169, PR-171 |
| Theme | Old diagnostic path deletion |

## Goal

Physically remove the remaining `execution-logs` entity/action/broadcast tail now that the user-facing Agent Monitor is backed by Cortex Activity Timeline.

## Current-State Analysis

The App no longer uses `execution-logs` as the monitor source, but Business/Common still register the entity and Runtime still broadcasts lightweight thinking/tool status to `/internal/logs/broadcast`.

## Implementation

- Remove `execution-logs` from app-facing and Business schemas.
- Remove `execution-logs.clear`.
- Remove Business `/internal/logs/broadcast` router and helpers.
- Remove Runtime `sync_broadcast_log` calls and the old broadcast utility.
- Keep Cortex trace writes as the product/diagnostic source.
- Add or update guards so `execution-logs` cannot return as a product path.

## Tests / Smoke

- Business schema tests assert no `execution-logs`.
- Common app-facing contract tests assert only active entities.
- Runtime tests assert tool/LLM execution works without broadcast.
- Existing Activity Timeline tests continue to pass.

## Closure

- Removed Business `execution-logs` entity/action/router/helper and Runtime broadcast utility/calls.
- Removed Common execution-log display contract and config keys.
- App config/type residue cleaned; remaining `execution-logs` references are guard tests only.
- Tests passed:
  - `novaic-common`: `PYTHONPATH=.:../novaic-agent-runtime pytest -q`
  - `novaic-business`: `PYTHONPATH=. pytest -q`
  - `novaic-agent-runtime`: `PYTHONPATH=.:../novaic-common pytest -q`
  - `novaic-app`: `npm run test:unit -- ActivityTimeline useActivityTimeline entangledEntityContracts`

## Deploy / GitHub

- Deploy services after tests pass.
- Commit and push touched repos plus parent submodule pointers.
