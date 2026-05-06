# PR-235 Reliable Evolution FSM-01 Baseline & Shadow Ledger

Status: `[x]`

## Goal

Create the first Reliable Evolution ledger layer for Queue session harness:
append-only session events, materialized shadow session state, and a future
durable outbox table. This PR must start recording observable shadow accounts
without changing live wake routing.

## Scope

- Runtime only: `novaic-agent-runtime`.
- Add SQLite schema v9 tables:
  - `tq_session_events`
  - `tq_session_state`
  - `tq_session_outbox`
- Add a repository layer for explicit event/state/outbox writes.
- Inject clock and ID providers explicitly.
- Wire observe-only shadow dual-write into `SessionRepository`.
- Add unit tests proving schema, idempotency, and no live routing change.

## Out Of Scope

- Do not replace `tq_active_sessions` as source of truth.
- Do not replace `tq_pending_triggers`.
- Do not publish from `tq_session_outbox`.
- Do not change attach/restart/finalize runtime behavior.
- Do not delete legacy session code in this PR.

## Small Tickets

- [x] **FSM-01-A Schema baseline**: add v9 tables and migration path.
- [x] **FSM-01-B Explicit repository**: add `SessionLedgerRepository` with injected clock/event ID/outbox ID providers.
- [x] **FSM-01-C Runtime wiring**: construct the ledger in Queue service startup and pass it into `SessionRepository`.
- [x] **FSM-01-D Observe-only dual-write**: record dispatch/session-end shadow event and state rows while preserving live return values.
- [x] **FSM-01-E Tests**: cover schema creation, atomic write/read, idempotency, and live route preservation.
- [x] **FSM-01-F Review**: verify explicit dependency boundary and no accidental cutover.

## Implementation Files

- `novaic-agent-runtime/queue_service/db/schema.py`
- `novaic-agent-runtime/queue_service/dependencies.py`
- `novaic-agent-runtime/queue_service/main.py`
- `novaic-agent-runtime/queue_service/session_ledger.py`
- `novaic-agent-runtime/queue_service/session_repo.py`
- `novaic-agent-runtime/tests/test_pr235_session_ledger_shadow.py`

## Legacy Cleanup Ledger

Keep these deliberately for now:

- `tq_active_sessions`: still live source of truth until FSM-07.
- `tq_pending_triggers`: still live pending inbox until FSM-05.
- Direct `TaskQueue.publish` for attach input: still live side effect path until FSM-03 outbox cutover.
- `session_ended()` direct cleanup/restart: still live lifecycle path until FSM-07.

Deletion criteria:

- Delete none in PR-235.
- Every future deletion must cite the replacement FSM phase and a passing old/new drift check.

## Verification

- `pytest tests/test_pr235_session_ledger_shadow.py tests/test_pr233_active_inbox_dispatch.py tests/test_pr153_pending_trigger_metadata.py`
- `pytest`
- `git diff --check`

## Review Result

Pass. The new ledger is observe-only: if it fails, live routing still follows
the old coordinator and emits a warning. Time and IDs are explicit injected
providers, so unit tests can reproduce behavior without hidden clock or UUID
reads. The durable outbox table exists but has no live publisher yet.

## Rollback

Code rollback is safe by reverting this PR. Database rollback does not require
dropping tables; the v9 tables are additive and ignored by the old live path.
