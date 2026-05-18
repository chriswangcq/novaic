# PR-318 Projection Table Quarantine Guard

Status: Closed
Owner: Codex
Phase: 7

## Goal

Make projection-table lifecycle authority impossible to accidentally reintroduce
after PR-316 and PR-317.

## Scope

- Static residue tests around TaskQueue and SagaRepository candidate methods.
- Schema comments and architecture ledger wording.

## Deletion Scope

- Delete misleading comments that call `tq_tasks` or `tq_sagas` the lifecycle
  state authority.
- Replace them with explicit projection/read-model wording.

## Acceptance Criteria

- Tests fail if candidate methods reintroduce `tq_tasks.status`,
  `tq_sagas.status`, projection heartbeat stale selectors, or
  `tq_tasks.status = 'done'` saga completion checks.
- Schema comments state that FSM state tables are lifecycle authority and
  projection tables are not.
- File 1 and ticket statuses reflect closure.

## Verification

- Targeted PR-318 tests.
- `git diff --check`.
- Full `novaic-agent-runtime` test suite if runtime changes are stable.

## Closure Notes

- Added static guards in
  `tests/test_pr318_projection_table_quarantine_guard.py` so TaskQueue and
  SagaRepository candidate methods cannot silently reintroduce projection
  lifecycle selectors.
- Updated `session_rebuild` to rebuild active sessions from `tq_saga_state`
  instead of `tq_sagas.status`.
- Updated schema comments and index declarations: old projection-status
  candidate indexes are dropped, and projection tables are explicitly marked
  non-authoritative for lifecycle decisions.
- Verification: PR-318 targeted guard tests, full runtime suite, business
  suite, common suite, and `git diff --check` passed.
