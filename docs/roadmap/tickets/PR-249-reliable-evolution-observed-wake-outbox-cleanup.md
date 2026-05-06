# PR-249 Reliable Evolution FSM-03B Observed Wake Outbox Cleanup

Status: `[x]`

## Goal

Stop recording observe-only `create_wake_saga` effects as retryable
`pending` session outbox rows. PR-237 created these rows before wake saga
creation was cut over to the durable outbox; after PR-247 and PR-248, the live
retryable outbox effects are recovery archive and attach input. Leaving
observe-only wake rows in `pending` pollutes backlog semantics and makes future
agents think there is a retryable worker path that does not exist.

## Phase Ledger

```text
Phase: FSM-03B observed wake outbox cleanup
Subject: observe-only wake saga creation account
Old source of truth: create_wake_saga shadow outbox row with status=pending
New source of truth: create_wake_saga shadow outbox row with status=observed
Input events: input_received(user_message / system_wake / recovered)
Decision function: unchanged; wake creation is still direct until a later cutover ticket
State transition: unchanged; direct saga creation records active state
Outbox effects: create_wake_saga observed-only, recovery_archive_scope/publish_attach_input retryable pending
Observation events: dispatch_saga_started, session_restarted, outbox status
Generation/idempotency key: shadow:effect:create_wake_saga:{saga_id}
Shadow drift metric: pending outbox list must not include observe-only create_wake_saga
Cutover switch: none; this is residue cleanup, not wake saga outbox cutover
Rollback path: revert PR-249 to restore pending observe rows
Legacy deletion condition: later wake saga outbox cutover replaces direct SagaOrchestrator.create
Tests: create_wake_saga records observed status; pending outbox drain ignores observed rows; live effects remain pending/published
Docs/guards to update: ticket index, architecture implementation record, outbox status tests
```

## Scope

- Runtime only: `novaic-agent-runtime`.
- Let `SessionLedgerRepository.append_outbox()` accept an explicit initial
  status for migration bookkeeping.
- Record `create_wake_saga` observe-only effects as `observed`.
- Add schema v12 migration so existing diagnostic `create_wake_saga/pending`
  rows are also marked `observed`.
- Keep `recovery_archive_scope` and `publish_attach_input` as durable retryable
  effects.

## Out Of Scope

- Do not cut over `SagaOrchestrator.create()` in this ticket.
- Do not introduce a new `starting` session state.
- Do not make `tq_session_state` authoritative.
- Do not add a long-running session outbox worker.

## Small Tickets

- [x] **FSM-03B-A Ledger status boundary**: add explicit initial outbox status
  and reject unsupported initial statuses.
- [x] **FSM-03B-B Observe-only wake rows**: mark `create_wake_saga` rows as
  `observed` in start and restart paths.
- [x] **FSM-03B-C Tests and guards**: prove observed rows do not appear in
  pending drain queries while attach/recovery effects remain retryable.
- [x] **FSM-03B-D Docs**: update architecture and ticket ledger.

## Explicit Dependency Boundary Review

- Initial outbox status is an explicit argument at the ledger boundary; no
  hidden status inference from effect type inside the repository.
- Runtime tests inject clocks and ID providers.
- This ticket does not add IO to the pure FSM decision path.

## Legacy Cleanup Ledger

Delete or neutralize in this ticket:

- Misleading `pending` status for observe-only `create_wake_saga` rows.
- Tests that describe `create_wake_saga` as retryable pending outbox work.

Keep for later:

- Direct `SagaOrchestrator.create()` for wake/restart until the later cutover
  ticket can introduce a clean `starting` or preallocated saga model.
- `tq_active_sessions` as the live active pointer.

## Verification

- `python -m py_compile queue_service/session_ledger.py queue_service/session_repo.py tests/test_pr249_observed_wake_outbox_cleanup.py`
- `pytest tests/test_pr249_observed_wake_outbox_cleanup.py tests/test_pr237_session_outbox_observe.py tests/test_pr248_attach_outbox_cutover.py tests/test_pr247_recovery_outbox_cutover.py -q`
- schema v12 migration updates only `create_wake_saga/pending` rows to
  `observed`; retryable attach/recovery rows remain untouched.
- `pytest -q`
- `git diff --check`

## Review Result

Closed.

- `SessionLedgerRepository.append_outbox()` now accepts an explicit initial
  status and rejects unsupported values instead of inferring a hidden lifecycle.
- `create_wake_saga` rows from dispatch start and session restart are recorded
  with `status=observed`.
- Schema v12 updates existing `create_wake_saga/pending` diagnostic rows to
  `observed`, while preserving retryable pending rows for live effects.
- Retryable session outbox effects still default to `pending`; this preserves
  recovery archive and attach input durability semantics.
- Pending outbox queries no longer return observe-only wake saga rows.

Verification passed:

- `python -m py_compile queue_service/db/schema.py queue_service/session_ledger.py queue_service/session_repo.py tests/test_pr249_observed_wake_outbox_cleanup.py`
- `pytest tests/test_pr249_observed_wake_outbox_cleanup.py tests/test_pr237_session_outbox_observe.py tests/test_pr248_attach_outbox_cutover.py tests/test_pr247_recovery_outbox_cutover.py -q`

## Rollback

Revert PR-249. This restores `create_wake_saga` observe-only rows to
`pending`; no data migration is required because existing rows are only
diagnostic.
