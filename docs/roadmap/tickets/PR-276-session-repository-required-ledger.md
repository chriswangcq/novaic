# PR-276 — SessionRepository Required Ledger

Status: Closed

## Goal

Remove false optional `SessionLedgerRepository` branches from
`SessionRepository`.

## Why

The session ledger is now the state/event/outbox boundary for the harness.
Leaving `ledger is None` fallbacks in active code suggests that dispatch,
finalize, and outbox publication may run without the durable ledger, which is
no longer a valid architecture.

## Scope

- Remove `session_ledger` / `ledger` `None` guards from active helper paths.
- Keep defensive exception handling around actual ledger operations where the
  current behavior intentionally logs and continues.
- Preserve test fakes that implement only the methods they exercise.
- Add guard coverage that the repository no longer contains ledger optional
  bypasses.

## Non-Goals

- Do not change ledger schema.
- Do not change list/diagnostic compatibility for fake ledgers that do not
  implement `list_active_states`.
- Do not change dispatch/finalize behavior.

## Acceptance Criteria

- `SessionRepository` has no `ledger is None` / `not self.session_ledger`
  bypasses in active dispatch/finalize/outbox helpers.
- Input append, transition accounting, pending projection, generation reads,
  and outbox append all require the injected ledger.
- Targeted session tests pass.
- Full `novaic-agent-runtime` test suite passes.
- `git diff --check` is clean.

## Closure Notes

- Removed optional ledger bypass branches from session transition, input,
  pending projection, generation, and outbox helper paths.
- Kept diagnostic `list_active_states` compatibility for deliberately narrow
  test fakes; this is not an active dispatch/finalize/outbox bypass.
- Added `tests/test_pr276_session_repository_required_ledger.py`.
- Targeted tests passed: 10 passed.
- Full `novaic-agent-runtime` test suite passed: 321 passed.
