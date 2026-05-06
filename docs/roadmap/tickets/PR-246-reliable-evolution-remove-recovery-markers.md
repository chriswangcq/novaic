# PR-246 Reliable Evolution FSM-06B Remove Recovery Marker Path

Status: `[x]`

## Goal

Finish the FSM-06 recovery cutover started in PR-245 by deleting the old
`tq_session_recoveries` marker path. Recovery is now driven by
`session_suspected_dead` events plus the dispatch recovery decision; the
ad hoc recovery marker table/consumer must not remain as a second live source
of truth.

## Phase Ledger

```text
Phase: FSM-06B recovery marker removal
Subject: dead active session recovery source of truth
Old source of truth: tq_session_recoveries marker table and dispatch marker consumer
New source of truth: session_suspected_dead event + unconsumed input_received projection
Input events: input_received, session_suspected_dead
Decision function: SessionRepository dispatch recovery decision
State transition: active/suspected_dead observed -> stale active removed -> recovered wake active(new generation)
Outbox effects: direct recovery cortex.scope_end task remains until durable outbox cutover
Observation events: session_suspected_dead_observed, dispatch_saga_started, input_consumed
Generation/idempotency key: suspected event idempotent by session_key + failed saga id; recovery archive task by failed scope id
Shadow drift metric: no marker fallback path may decide recovery
Cutover switch: none; marker table and consumer are removed
Rollback path: revert PR-246 after PR-245
Legacy deletion condition: PR-245 full tests pass and no tq_session_recoveries live reads/writes remain
Tests: schema no longer creates marker table; dispatch does not read markers; existing event recovery tests pass
Docs/guards to update: ticket index, architecture implementation record, grep guard for tq_session_recoveries
```

## Scope

- Runtime only: `novaic-agent-runtime`.
- Remove `tq_session_recoveries` from schema creation and migrations.
- Remove dispatch fallback that reads/deletes recovery markers.
- Remove diagnostics/test helper for listing recovery markers.
- Update tests to assert the marker table/path is gone and recovery still works
  through `session_suspected_dead` events.

## Out Of Scope

- Do not cut recovery archive publish to durable outbox in this ticket. That is
  the next FSM-03/FSM-06 side-effect cutover.
- Do not make `tq_session_state` the live source of truth for active sessions.
- Do not change finalize payload ownership; Phase 7 handles finalize ownership.

## Small Tickets

- [x] **FSM-06B-A Schema removal**: remove marker table creation/migration and
  bump schema so existing DBs drop `tq_session_recoveries`.
- [x] **FSM-06B-B Dispatch cleanup**: remove the dispatch marker consumer and
  ensure only `session_suspected_dead` events trigger recovery.
- [x] **FSM-06B-C Diagnostics/tests cleanup**: remove marker diagnostics helper
  and update tests to inspect events instead.
- [x] **FSM-06B-D Guard and verification**: add/keep source guard proving no
  live code references `tq_session_recoveries`.

## Explicit Dependency Boundary Review

- Recovery decision remains reproducible from explicit DB events and current
  active pointer snapshot.
- No hidden marker fallback may affect dispatch results outside the event log.
- Schema migration is boundary IO; core routing behavior still depends on
  explicit repository observations.

## Legacy Cleanup Ledger

Delete in this ticket:

- `tq_session_recoveries` table creation and migration creation path.
- Dispatch fallback that reads/deletes `tq_session_recoveries`.
- `SessionRepository.list_session_recoveries()` diagnostics helper.
- Tests that assert old marker table behavior.

Keep for later:

- Direct recovery archive publish until durable outbox cutover.
- `tq_active_sessions` as the live active pointer until state cutover.
- `session_suspected_dead` event and dispatch recovery decision.

## Verification

- `pytest tests/test_pr245_suspected_dead_recovery.py tests/test_pr233_active_inbox_dispatch.py tests/test_pr243_inbox_restart_cutover.py tests/test_pr235_session_ledger_shadow.py -q`
- `pytest -q`
- `git diff --check`
- Guard scan: no live runtime code references `tq_session_recoveries`.

## Review Result

Closed.

- Schema v11 no longer creates `tq_session_recoveries`; existing DBs drop the
  table during migration.
- `SessionRepository.dispatch()` no longer reads/deletes recovery markers.
  Recovery routing now only observes `session_suspected_dead` events for the
  current active scope.
- `SessionRepository.list_session_recoveries()` was removed so diagnostics and
  tests cannot accidentally treat marker rows as live truth.
- Tests now assert the marker table is absent, marker create/select/insert/delete
  paths are not present in live runtime code, and PR-245 event recovery behavior
  still preserves inbox inputs.

## Rollback

Revert PR-246 to restore marker table/consumer. PR-245 remains the intended
source of truth; rollback should only be used if existing deployed DBs still
depend on marker rows.
