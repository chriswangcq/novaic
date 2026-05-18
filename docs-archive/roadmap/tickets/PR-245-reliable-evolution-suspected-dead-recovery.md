# PR-245 Reliable Evolution FSM-06A Suspected-Dead Recovery Event

Status: `[x]`

## Goal

Move wake-finalize failure handling out of the watchdog's direct session
mutation path. A failed `wake_finalize` should first become an explicit
`session_suspected_dead` event; the next dispatch observes that event and starts
a recovery wake from the append-only inbox projection.

## Phase Ledger

```text
Phase: FSM-06A suspected-dead recovery event cutover
Subject: wake_finalize failure / dead active session recovery
Old source of truth: SagaOrchestrator directly deletes tq_active_sessions and writes tq_session_recoveries
New source of truth: session_suspected_dead event + SessionRepository dispatch recovery decision
Input events: input_received, session_suspected_dead
Decision function: dispatch active-session check + suspected-dead event observation
State transition: active -> suspected_dead observed -> recovery wake / active(new generation)
Outbox effects: direct recovery cortex.scope_end task remains until outbox cutover
Observation events: session_suspected_dead, dispatch_saga_started, input_consumed
Generation/idempotency key: suspected event idempotent by session_key + failed saga id
Shadow drift metric: recovery wake must not attach input to failed generation
Cutover switch: none; direct delete path removed in this ticket
Rollback path: revert PR-245
Legacy deletion condition: PR-245 tests pass and no direct active delete in wake_finalize failure branch
Tests: watchdog does not clear active; next dispatch recovers once; pending inbox migrates
Docs/guards to update: ticket index, architecture implementation record, direct mutation guard
```

## Scope

- Runtime only: `novaic-agent-runtime`.
- `SagaOrchestrator.mark_failed(wake_finalize)` writes a suspected-dead event
  instead of deleting `tq_active_sessions`.
- `SessionRepository.dispatch()` detects the suspected-dead event for the active
  scope, removes the stale active pointer inside its own dispatch transaction,
  starts a recovery wake, and merges unconsumed inbox inputs.
- Recovery structural archive task can still be published directly for now; the
  durable outbox cutover remains a later FSM phase.

## Out Of Scope

- Do not remove `tq_session_recoveries` table yet; older markers may still be
  consumed until recovery event cutover is fully proven.
- Do not cut direct publish paths to durable outbox.
- Do not change wake finalize payload contract beyond recovery metadata carried
  through the suspected-dead event.

## Small Tickets

- [x] **FSM-06A-A Suspected-dead event**: record
  `session_suspected_dead` idempotently when `wake_finalize` fails.
- [x] **FSM-06A-B Dispatch recovery decision**: if active scope has a
  suspected-dead event, do not attach to it; start recovered wake instead.
- [x] **FSM-06A-C Inbox preservation**: recovered wake receives unconsumed inbox
  projection, including the new user input that triggered recovery.
- [x] **FSM-06A-D Guard and tests**: prove watchdog does not directly delete
  active session and no input is lost.

## Explicit Dependency Boundary Review

- Watchdog event payload is constructed from explicit saga context, error, and
  injected clock.
- Dispatch recovery decision reads explicit DB state/events inside the repository
  transaction and does not depend on hidden in-memory flags.
- Recovery wake context is reproducible from `input_received` events plus the
  `session_suspected_dead` event payload.

## Legacy Cleanup Ledger

Delete in this ticket:

- Wake-finalize failure branch direct `DELETE FROM tq_active_sessions`.
- Wake-finalize failure branch direct `tq_session_recoveries` upsert.

Keep for later:

- `tq_session_recoveries` table and consumer for pre-existing recovery markers.
- Direct recovery archive publish until durable outbox cutover.
- `tq_active_sessions` as the live active pointer until state cutover.

## Verification

- `pytest tests/test_pr245_suspected_dead_recovery.py tests/test_pr233_active_inbox_dispatch.py tests/test_pr243_inbox_restart_cutover.py -q`
- `pytest -q`
- `git diff --check`

## Review Result

Closed.

- `SagaOrchestrator.mark_failed(wake_finalize)` now records an idempotent
  `session_suspected_dead` event from explicit saga context, error, and injected
  clock. It no longer deletes `tq_active_sessions` or writes
  `tq_session_recoveries`.
- `SessionRepository.dispatch()` observes a matching suspected-dead event for
  the current active scope inside the routing transaction, removes that stale
  active pointer there, starts a recovered wake, and merges unconsumed inbox
  projection into the recovered wake context.
- Recovery archive remains a direct `cortex.scope_end` task for this phase, but
  it is queued by the dispatch recovery decision rather than by the watchdog.
- Tests cover idempotent suspected-dead event creation, no direct active delete,
  next-dispatch recovery, inbox preservation, and source guard against direct
  mutation in the wake-finalize failure branch.

## Rollback

Revert PR-245 to restore immediate wake-finalize failure cleanup.
