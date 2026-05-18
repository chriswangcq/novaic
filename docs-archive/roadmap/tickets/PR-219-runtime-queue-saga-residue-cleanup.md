# PR-219 Runtime Queue / Saga Residue Cleanup

| Field | Value |
| --- | --- |
| Status | `[closed]` |
| Type | Runtime live-code cleanup |
| Created | 2026-05-05 |
| Scope | `novaic-agent-runtime/queue_service` |
| Dependencies | PR-141, explicit input contract cleanup |

## Goal

Remove misleading compatibility branches and comments from Runtime queue/saga
code so the active implementation reads like the current queue contract is the
only supported contract.

## Current-State Questions

- Is `current_step` still used by any live runtime path?
- Does the queue API still need a silent default for missing delay?
- Are the saga repository compatibility helpers used by production code or only
  tests?

## Small Tickets

### 1. Queue Schema Compatibility Field Review

- Objective: decide whether `current_step` is live state or obsolete residue.
- Scope: queue DB schema, migrations, repository readers/writers, tests.
- Expected result: obsolete state is removed or renamed to current product
  semantics without compatibility wording.
- Verification: targeted search and queue/saga tests.

### 2. Queue API Default Contract Cleanup

- Objective: remove backward-compatible defaults that hide missing explicit
  inputs.
- Scope: `queue_service/queue_db.py` and callers.
- Expected result: callers provide explicit delay semantics, or the method owns
  a current product default without legacy framing.
- Verification: unit tests covering enqueue/schedule behavior.

### 3. Saga Compatibility Helper Cleanup

- Objective: remove or rename saga compatibility interfaces that are not current
  product APIs.
- Scope: `queue_service/saga_repo.py` and tests.
- Expected result: no live class/method/docstring claims legacy compatibility.
- Verification: saga repository tests and residue scan.

## Acceptance

- Runtime queue/saga live code no longer contains compatibility or legacy
  branches for removed contracts.
- Tests express the current queue/saga contract directly.
- No production caller depends on removed compatibility helpers.

## Verification

- `cd novaic-agent-runtime && pytest -q`
- targeted `rg` for `compat`, `compatibility`, `legacy`, and `current_step` in
  `queue_service`.

## Closure Notes

- Removed `tq_sagas.current_step` from the fresh schema and Runtime
  read/write path.
- Replaced the old saga start surface with the current saga create surface.
- Removed saga repository/orchestrator helpers that existed only for the old
  compatibility test coordinator.
- Kept only the schema cleanup step needed to drop the retired column from an
  existing SQLite schema during deployment.
