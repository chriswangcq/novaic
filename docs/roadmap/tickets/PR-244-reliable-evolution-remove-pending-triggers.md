# PR-244 Reliable Evolution FSM-05F Remove Pending Trigger Store

Status: `[x]`

## Goal

Remove `tq_pending_triggers` from the live Queue session harness. After
PR-243, `session_ended()` restarts from the append-only inbox projection; this
ticket removes the old single-row pending store so future code cannot
accidentally route through it again.

## Phase Ledger

```text
Phase: FSM-05F remove legacy pending store
Subject: pending input storage
Old source of truth: tq_pending_triggers
New source of truth: unconsumed input_received events
Input events: input_received
Decision function: pending projection builder
State transition: active -> buffered records input only; ending -> restart/close from projection
Outbox effects: unchanged observe-only effects
Observation events: dispatch_buffered, pending_projection_observed
Generation/idempotency key: unchanged
Shadow drift metric: pending_projection_observed.drift treats absent legacy row as clean
Cutover switch: none; direct deletion
Rollback path: revert PR-244
Legacy deletion condition: PR-243 restart cutover green
Tests: no pending table writes/reads; non-attachable input restarts from inbox; stale table removed by migration
Docs/guards to update: ticket index, architecture implementation record, tests
```

## Scope

- Runtime only: `novaic-agent-runtime`.
- Remove `tq_pending_triggers` schema/table creation and upgrade existing DBs
  by dropping the table.
- Remove dispatch/session_end/rebuild reads and writes to the old pending table.
- Replace diagnostics with pending inbox event diagnostics.
- Keep recovery marker behavior, but merge unconsumed inbox projection into
  recovery wake context so deleted pending rows cannot cause input loss.

## Out Of Scope

- Do not change durable outbox publish cutover.
- Do not change watchdog/recovery FSM ownership.
- Do not remove `tq_active_sessions`.

## Small Tickets

- [x] **FSM-05F-A Schema cleanup**: bump schema and drop
  `tq_pending_triggers`.
- [x] **FSM-05F-B Repository cleanup**: remove pending table reads/writes from
  dispatch, session end, rebuild, diagnostics.
- [x] **FSM-05F-C Diagnostics cleanup**: `/pending` reports unconsumed inbox
  inputs instead of pending triggers.
- [x] **FSM-05F-D Tests and guards**: update old pending tests to assert inbox
  semantics and add a guard that no live runtime code references
  `tq_pending_triggers`.

## Explicit Dependency Boundary Review

- Pending state is derived only from explicit `input_received` event payloads.
- No hidden single-row merge remains as a second source of truth.
- DB reads stay inside repository/ledger diagnostic boundaries.

## Legacy Cleanup Ledger

Delete in this ticket:

- `tq_pending_triggers` schema/table.
- pending upsert merge code.
- session end pending row drain code.
- rebuild orphan pending drain code.
- pending trigger diagnostics method.

Keep for later:

- `tq_active_sessions` as live active pointer until state cutover.
- direct publish paths until durable outbox cutover.

## Verification

- `pytest tests/test_pr244_remove_pending_triggers.py tests/test_pr243_inbox_restart_cutover.py tests/test_pr241_pending_inbox_projection.py tests/test_pr240_input_consumption_observe.py tests/test_pr239_append_only_inbox_observe.py tests/test_pr153_pending_inbox_metadata.py tests/test_pr233_active_inbox_dispatch.py tests/test_pr242_strict_input_ledger.py tests/test_pr235_session_ledger_shadow.py tests/test_pr236_session_fsm_shadow_decision.py tests/test_pr237_session_outbox_observe.py -q`
- `pytest -q`
- `git diff --check`

## Review Result

Closed. `tq_pending_triggers` is no longer created on fresh schema and is
dropped by v10 migration. `SessionRepository` no longer receives or stores a
trigger id provider, no live dispatch/session-end/rebuild/diagnostic path reads
or writes the old table, `/pending` reports unconsumed inbox inputs, and recovery
wakes merge unconsumed inbox projection so buffered inputs are preserved without
the old orphan pending row.

## Rollback

Revert PR-244 to restore the old pending trigger table and merge path.
