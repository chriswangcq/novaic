# PR-251 Reliable Evolution FSM-03D Wake Creation Outbox Cutover

Status: `[x]` deployed and closed

## Goal

Move live `subagent_wake` saga creation behind durable session outbox rows.
`SessionRepository` must no longer treat direct `SagaOrchestrator.create()` as
the primary side effect for start/restart wake. The durable outbox row becomes
the replayable account for creating a wake saga, and synchronous dispatch may
publish that row immediately for compatibility.

## Phase Ledger

```text
Phase: FSM-03D wake creation outbox cutover
Subject: start/restart wake saga creation
Old source of truth: direct SagaOrchestrator.create() inside SessionRepository
New source of truth: pending create_wake_saga session outbox row
Input events: input_received(...)
Decision function: current route decision, later pure FSM cutover
State transition: session becomes active only after create_wake_saga outbox publish returns saga/scope
Outbox effects: create_wake_saga pending/retryable
Observation events: dispatch_saga_started, session_restarted
Generation/idempotency key: session-{session_key}-{scope_id} or caller idempotency key
Shadow drift metric: no direct subagent_wake create in SessionRepository start/restart path
Cutover switch: none
Rollback path: revert PR-251
Legacy deletion condition: old observe_create_wake_saga rows stay historical only
Tests: start/restart use pending create_wake_saga; dispatcher creates saga idempotently; publish failure leaves pending row and no active session
Docs/guards to update: architecture implementation record, ticket ledger
```

## Scope

- Add live `create_wake_saga` support to `SessionOutboxDispatcher`.
- Record `create_wake_saga` rows as pending durable effects for dispatch start
  and restart from inbox.
- Synchronously publish the new row when dispatch needs to return a `saga_id`.
- Preserve idempotency across repeated dispatch calls and outbox drain retries.
- Recovery archive remains a separate durable outbox effect.

## Out Of Scope

- Do not make `tq_session_state` the only SSOT in this ticket.
- Do not rewrite all `dispatch()` branches into pure FSM.
- Do not change wake_finalize/finalize ownership.

## Small Tickets

- [x] **FSM-03D-A Effect contract**: define `create_wake_saga` as a live
  retryable outbox effect with explicit payload schema.
- [x] **FSM-03D-B Dispatcher support**: implement idempotent saga creation from
  the outbox row and return the created/existing `saga_id`.
- [x] **FSM-03D-C Dispatch start cutover**: replace direct start-wake
  `orchestrator.create()` with durable outbox creation + immediate publish.
- [x] **FSM-03D-D Restart cutover**: replace direct restart-wake creation with
  durable outbox creation + immediate publish.
- [x] **FSM-03D-E Failure semantics**: if create publish fails, leave the row
  pending and avoid publishing active session ownership as if the wake existed.
- [x] **FSM-03D-F Tests/guards**: cover success, idempotency, retry/drain, and
  no direct start/restart create in `SessionRepository`.

## Explicit Dependency Boundary Review

Verdict: target compliant.

Boundary:
- Core under review: session routing and wake creation side-effect selection.
- Allowed imperative shell: DB repository/outbox dispatcher and Saga repository.

Hidden inputs found:
- Current start/restart logic calls `SagaOrchestrator.create()` directly in
  `SessionRepository`, so side-effect execution order is implicit in the
  branch, not represented as explicit durable data.

Required fixes:
- Pass saga creation details as an explicit outbox payload.
- Let the dispatcher be the imperative adapter that calls `SagaOrchestrator`.
- Inject clock/id providers already present in repositories; add deterministic
  tests for idempotency and publish failure.

Residual risks:
- Until PR-252, `tq_active_sessions` remains the active pointer.

## Verification

- `python -m py_compile queue_service/session_outbox.py queue_service/session_repo.py`
- `pytest tests/test_pr251_wake_creation_outbox_cutover.py -q`
- `pytest tests/test_pr237_session_outbox_observe.py tests/test_pr249_observed_wake_outbox_cleanup.py tests/test_pr250_observed_wake_effect_rename.py -q`
- `pytest -q`
- `git diff --check`

## Review Result

Local pass:

- Live start/restart wake creation is represented by `create_wake_saga`
  session outbox rows.
- `SessionOutboxDispatcher` owns the imperative `SagaOrchestrator.create()`
  adapter and requires an injected orchestrator.
- Start/restart paths no longer call `orchestrator.create()` directly.
- Publish failure leaves a retryable pending row and no active session.
- Transient SQLite lock during synchronous publish retries once against the
  same durable outbox row; permanent failure remains pending.

Verification run:

- `python -m py_compile queue_service/session_outbox.py queue_service/session_repo.py`
- `pytest tests/test_pr251_wake_creation_outbox_cutover.py -q`
- `pytest tests/test_pr237_session_outbox_observe.py tests/test_pr249_observed_wake_outbox_cleanup.py tests/test_pr250_observed_wake_effect_rename.py -q`
- `pytest tests/test_pr153_pending_inbox_metadata.py tests/test_pr233_active_inbox_dispatch.py tests/test_pr235_session_ledger.py tests/test_pr236_session_fsm_decision.py tests/test_pr237_session_outbox_observe.py tests/test_pr239_append_only_inbox.py tests/test_pr240_input_consumption.py tests/test_pr245_suspected_dead_recovery.py tests/test_pr247_recovery_outbox_cutover.py tests/test_pr248_attach_outbox_cutover.py tests/test_pr249_observed_wake_outbox_cleanup.py tests/test_pr250_observed_wake_effect_rename.py tests/test_pr251_wake_creation_outbox_cutover.py -q`

Full suite passes locally.

Deployment closure:

- `./deploy runtime` completed successfully on 2026-05-06.
- `./deploy status` showed api services online on ports 19900, 19999, 19998,
  19993, 19997, 19995, and 19996, with 8 worker processes and relay active.

## Rollback

Revert PR-251. Direct `SagaOrchestrator.create()` start/restart behavior returns.
