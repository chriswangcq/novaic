# PR-242 Reliable Evolution FSM-05D Strict Input Ledger Boundary

Status: `[x]`

## Goal

Make `input_received` ledger writes a required dispatch boundary before any
live cutover uses the inbox as source of truth. The current observe-only path
logs and continues when the input event write fails; that is acceptable for
shadow mode but unsafe once restart reads from inbox.

## Phase Ledger

```text
Phase: FSM-05D strict input ledger prerequisite
Subject: dispatch input recording reliability
Old source of truth: tq_pending_triggers can still save buffered inputs if shadow input write fails
New source of truth: input_received event must exist before dispatch routing continues
Input events: input_received
Decision function: existing dispatch route decision
State transition: none; fail-fast before routing when input ledger write fails
Outbox effects: none
Observation events: input_received
Generation/idempotency key: dispatch idempotency key controls logical input dedupe
Shadow drift metric: tests assert no silent shadow-write bypass
Cutover switch: none
Rollback path: revert to best-effort shadow write
Legacy deletion condition: restart cutover can proceed only after strict input ledger tests pass
Tests: input write failure propagates and does not create pending/active side effects
Docs/guards to update: ticket index and architecture implementation record
```

## Scope

- Runtime only: `novaic-agent-runtime`.
- Require `SessionRepository` to have a `SessionLedgerRepository`.
- Make the initial `input_received` append fail-fast instead of warning and
  continuing.
- Keep later shadow observation writes best-effort until their respective
  cutover tickets.
- Prove a failed input ledger write stops dispatch before active/pending side
  effects.

## Out Of Scope

- Do not switch `session_ended()` restart source yet.
- Do not delete `tq_pending_triggers`.
- Do not make pending projection authoritative.
- Do not add durable outbox publishing.

## Small Tickets

- [x] **FSM-05D-A Required ledger dependency**: remove the optional constructor
  default and update repository test helpers to pass a ledger.
- [x] **FSM-05D-B Fail-fast input append**: initial `input_received` write must
  raise on failure before live routing mutates active/pending state.
- [x] **FSM-05D-C Side-effect guard test**: prove failed input append does not
  create active sessions, pending triggers, sagas, or tasks.
- [x] **FSM-05D-D Regression tests**: keep previous inbox observe tests passing.

## Implementation Files

- `novaic-agent-runtime/queue_service/session_repo.py`
- `novaic-agent-runtime/tests/test_pr153_pending_inbox_metadata.py`
- `novaic-agent-runtime/tests/test_pr233_active_inbox_dispatch.py`
- `novaic-agent-runtime/tests/test_pr242_strict_input_ledger.py`

## Explicit Dependency Boundary Review

Required shape:

- `SessionLedgerRepository` is an explicit constructor dependency, not hidden
  optional state.
- Failure is explicit and testable.
- No fallback should silently preserve old behavior after the input ledger write
  fails.

## Legacy Cleanup Ledger

Keep these deliberately for now:

- `tq_pending_triggers` remains live pending/restart state.
- Later shadow event/state/outbox writes remain best-effort until their cutover
  tickets.

Deletion criteria:

- PR-243 can safely cut `session_ended()` to inbox restart only after strict
  input ledger write is enforced.

## Verification

- `pytest tests/test_pr242_strict_input_ledger.py tests/test_pr241_pending_inbox_projection.py tests/test_pr240_input_consumption_observe.py tests/test_pr239_append_only_inbox_observe.py tests/test_pr153_pending_inbox_metadata.py tests/test_pr233_active_inbox_dispatch.py`
- `pytest`
- `git diff --check`

## Review Result

Pass. `SessionRepository` now requires a session ledger and the initial
`input_received` append is fail-fast. A failure at that boundary raises before
active sessions, pending triggers, sagas, or tasks are created. Later
observe-only event/state/outbox writes remain best-effort until their own
cutover tickets.

## Rollback

Revert this PR to restore best-effort input ledger writes.
