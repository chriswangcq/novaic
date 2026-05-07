# Queue Service Durable FSM Host Plan

Status: Closed
Owner: Codex
File 1: yes
Last updated: 2026-05-07

This is the controlling implementation ledger for upgrading Queue Service from
a session-specific coordinator into a durable FSM host for session, task, saga,
and worker lease lifecycles.

The operating loop for this file is strict:

```text
for each phase:
    check this file
    create tickets for the phase
    foreach ticket:
        implement the ticket
        review residue and dependency boundaries
        verify with tests or explicit audits
        update this file and the ticket file
```

## Non-Negotiable Principles

1. The agent is the subject. Queue Service coordinates environment events and
   boundary effects around the agent; it does not encode LLM behavior theory.
2. User messages, scheduler ticks, watchdog findings, and worker observations
   are input events.
3. Shell, Cortex, Saga publishing, task publishing, IM delivery, DB, clock, and
   IDs are explicit boundaries.
4. Pure FSM reducers read no time, IDs, env, files, DB, network, or globals.
5. Durable state transition and durable outbox effects commit atomically.
6. Workers publish committed effects; workers do not own business decisions.
7. Compatibility branches are temporary only inside a ticket. No permanent
   shadow path, fallback branch, or "old path just in case" is acceptable.
8. Generated code is cheap. Branch residue, ambiguous old code, and misleading
   compatibility names are expensive and must be deleted.

## Target Model

Queue Service becomes a durable FSM host:

```text
InputEvent
  -> append durable event
  -> load current machine state
  -> pure reducer(state, event, explicit_context)
  -> atomic state + transition + outbox commit
  -> boundary worker publishes outbox
  -> observed boundary event re-enters the ledger
```

Generic substrate:

```text
FsmState(machine_type, machine_id, state, generation, payload)
FsmEvent(event_id, event_type, payload, idempotency_key)
FsmDecision(action, next_state, effects, reason)
FsmEffect(effect_type, payload, idempotency_key)
```

Machine families:

| Machine | Owner | Baseline before this ledger | Target authority |
|---|---|---|---|
| Session | `SessionRepository` / `SessionOutboxWorker` | Mostly durable FSM | `tq_session_state`, `tq_session_events`, `tq_session_outbox` |
| Task | `TaskQueue` | Direct `tq_tasks` status updates | Task FSM event/state/outbox, with `tq_tasks` as projection or deleted view |
| Saga | `SagaRepository` / `SagaOrchestrator` | Direct `tq_sagas` status updates | Saga FSM event/state/outbox, with `tq_sagas` as projection or deleted view |
| Worker lease | task/saga/session workers | scattered heartbeat fields | Lease FSM or explicit lease projection owned by FSM events |

## Baseline Before This Plan

Completed before this plan:

- Generic pure FSM substrate exists under `queue_service.fsm`.
- Generic SQLite store/outbox substrate exists.
- Session dispatch, wake creation, attach, recovery, and finalize are already
  mostly routed through durable session events and session outbox.
- Production startup launches `session-outbox-worker`.
- Queue readiness exposes session outbox backlog and starting session backlog.

Current completed shape:

- Session, task, saga, and worker lease decisions are modeled by explicit FSM
  reducers and recorded through durable event/state ledgers.
- `tq_tasks`, `tq_sagas`, and heartbeat columns are runtime projections; direct
  SQL writes are isolated in projection writers and guarded by static tests.
- Saga compensation and wake/session side effects are durable outbox effects
  published by workers, not repository-owned direct side effects.
- Worker heartbeat and stale recovery are lease events.
- Queue audit summaries are derived from durable events/state/outbox rows.

## Phase Ledger

| Phase | Status | Goal | Tickets | Deletion target | Verification gate |
|---|---|---|---|---|---|
| 0 | Closed | Freeze this roadmap as the controlling plan | PR-303 | none | File 1 exists, tickets exist |
| 1 | Closed | Task lifecycle pure FSM foundation | PR-304 closed, PR-305 closed | none yet | Pure reducer tests, no hidden inputs |
| 2 | Closed | Cut `TaskQueue` to Task FSM and delete old status writers | PR-306 closed, PR-307 closed | direct task status branches | Task suite + residue grep |
| 3 | Closed | Saga lifecycle pure FSM foundation | PR-308 closed, PR-309 closed | none yet | Pure reducer tests, no hidden inputs |
| 4 | Closed | Cut saga repository/orchestrator to Saga FSM and outbox | PR-310 closed, PR-311 closed, PR-312 closed | direct saga status and compensation branches | Saga/session integration suite + residue grep |
| 5 | Closed | Worker lease/heartbeat FSM | PR-313 closed | direct heartbeat recovery mutation | stale recovery tests + lease audit |
| 6 | Closed | Unified audit/replay and final residue guard | PR-314 closed, PR-315 closed | compatibility names, dual routes, old docs | full runtime/common/business tests |
| 7 | Closed | Quarantine task/saga projection tables from lifecycle candidate decisions | PR-316 closed, PR-317 closed, PR-318 closed | projection-table status/heartbeat candidate selectors | state-table candidate tests + residue guards |

## Phase 0: Planning Ledger

Ticket:

- `docs/roadmap/tickets/PR-303-queue-service-durable-fsm-host-plan.md`

Acceptance:

- This file is the single phase controller.
- Every phase names ticket files before implementation.
- Every ticket names implementation scope, deletion scope, and verification.

Closure:

- PR-303 created this controlling plan and PR-304 through PR-315 tickets.

## Phase 1: Task Lifecycle FSM Foundation

Tickets:

- `PR-304-task-lifecycle-fsm-vocabulary.md` (closed)
- `PR-305-task-fsm-store-ledger.md` (closed)

Implementation intent:

- Add a pure task lifecycle reducer that models current task transitions without
  reading DB, clock, random IDs, env, or globals.
- Add task FSM persistence tables or a generic-store binding.
- Keep `tq_tasks` live only as a projection until Phase 2 cutover.

Task states:

```text
pending -> claimed -> done
pending -> claimed -> pending     # retry
pending -> claimed -> failed      # terminal failure
pending -> cancelled
claimed -> pending                # release or stale retry
claimed -> failed                 # stale terminal
```

Explicit event vocabulary:

```text
task_published
task_claim_requested
task_completed
task_failed_retry
task_failed_terminal
task_released
task_cancel_requested
task_heartbeat_timed_out_retry
task_heartbeat_timed_out_terminal
```

Boundary inputs:

- task id
- worker id
- attempt count
- max retry count
- stale cutoff computed by caller
- retry scheduling timestamp computed by caller

Deletion scope for follow-up:

- direct status updates in `TaskQueue.claim`, `complete`, `fail`,
  `recover_stale`, `release_task`, and `cancel_all`.

Closure:

- PR-304 added the pure task lifecycle reducer and tests.
- PR-305 added task FSM event/state/outbox tables and a thin generic-store
  adapter.

## Phase 2: TaskQueue FSM Cutover

Tickets:

- `PR-306-taskqueue-fsm-cutover.md` (closed)
- `PR-307-taskqueue-old-sql-residue-cleanup.md` (closed)

Implementation intent:

- Route `TaskQueue` mutations through task FSM transitions.
- Make direct SQL writes projection-only, or remove them if projections are no
  longer needed.
- Add residue guards proving old imperative branches are gone.

Completion gate:

- Runtime task tests pass.
- No active task lifecycle method has an unguarded `UPDATE tq_tasks SET status`
  decision branch outside the FSM projection writer.

Progress:

- PR-306 routes publish, claim, complete, fail, stale recovery, release, and
  cancel through task FSM decisions and records task FSM ledger events/state.
- PR-307 moves lifecycle projection writes behind
  `TaskQueue._apply_task_projection(...)` and adds a static residue guard that
  fails if active task lifecycle methods reintroduce direct `UPDATE tq_tasks` /
  `SET status` SQL.

Closure:

- Phase 2 is closed for task lifecycle. `tq_tasks` remains as the runtime
  projection table, but the task lifecycle decision path is the task FSM plus
  task FSM ledger.
- Direct heartbeat mutation remains outside Phase 2 by design and is tracked
  under Phase 5 / PR-313 worker lease FSM.

## Phase 3: Saga Lifecycle FSM Foundation

Tickets:

- `PR-308-saga-lifecycle-fsm-vocabulary.md` (closed)
- `PR-309-saga-fsm-store-ledger.md` (closed)

Implementation intent:

- Add a pure saga lifecycle reducer for create, claim, launched, step result,
  complete, fail, retry/recover, and cancel.
- Separate saga lifecycle decisions from compensation side effects.
- Persist saga events/state/effects through the generic store.

Saga states:

```text
pending -> running -> launched -> completed
pending -> running -> failed
pending -> cancelled
running -> pending       # stale retry
running -> failed        # stale terminal
```

Boundary inputs:

- saga id
- task summary snapshot
- retry count / max retries
- worker lease snapshot
- failure reason
- compensation policy selected by caller

Closure:

- PR-308 added the pure saga lifecycle reducer and tests.
- PR-309 added saga FSM event/state/outbox tables and a thin generic-store
  adapter.
- `tq_sagas` remains the runtime projection table until Phase 4 cutover.

## Phase 4: Saga Cutover And Compensation Outbox

Tickets:

- `PR-310-saga-repository-fsm-cutover.md` (closed)
- `PR-311-saga-compensation-outbox-cutover.md` (closed)
- `PR-312-saga-old-sql-residue-cleanup.md` (closed)

Implementation intent:

- Route `SagaRepository` state changes through Saga FSM.
- Turn wake finalize creation and session suspected-dead recording into durable
  saga/session outbox effects, not direct repository side effects.
- Delete old direct mutation and compatibility paths after tests prove cutover.

Completion gate:

- Failed wake saga compensation is represented as durable effects.
- `SagaOrchestrator.mark_failed` no longer directly creates follow-up sagas or
  writes session events outside the effect publisher.

Closure:

- PR-310 routes active saga lifecycle decisions through the Saga FSM and records
  saga event/state rows while keeping `tq_sagas` as the runtime projection.
- PR-311 moves wake-finalize creation and session suspected-dead recording into
  durable saga outbox effects, adds a retry/dead-letter publisher, and wires a
  visible `saga-outbox-worker` process into the backend start script.
- PR-312 adds residue guards proving active saga lifecycle methods no longer
  embed direct `UPDATE tq_sagas` / `SET status` decision SQL and
  `SagaOrchestrator.mark_failed` no longer publishes compensation directly.
- PR-312 also removes the wake-created observed-event race-loser direct
  `UPDATE tq_sagas` branch; stale/race saga cancellation now goes through the
  SagaRepository FSM projection path.
- Remaining direct saga heartbeat mutation is intentionally outside Phase 4 and
  is tracked under Phase 5 / PR-313 worker lease FSM.

## Phase 5: Worker Lease / Heartbeat FSM

Ticket:

- `PR-313-worker-lease-fsm.md` (closed)

Implementation intent:

- Model claim, heartbeat, timeout, release, and reclaim as explicit lease
  events.
- Make watchdog/stale recovery produce events, not direct state mutations.
- Keep task/saga specific workers as publishers/executors, not decision owners.

Completion gate:

- Stale task and stale saga recovery run through lease events.
- Heartbeat data is a projection of lease state.

Closure:

- PR-313 added the pure worker lease FSM and a thin generic-store lease ledger.
- Task and saga claim/heartbeat/release/timeout paths now record
  `lease_acquired`, `lease_heartbeat_recorded`, `lease_released`, and
  `lease_timed_out` events.
- `TaskQueue.heartbeat` and `SagaRepository.heartbeat` no longer embed direct
  SQL updates; heartbeat fields are updated through projection writers from
  lease decisions.
- Full `novaic-agent-runtime` suite passed with `425 passed`.

## Phase 6: Unified Audit, Replay, And Residue Guard

Tickets:

- `PR-314-queue-control-plane-audit-replay.md` (closed)
- `PR-315-queue-fsm-final-residue-guard.md` (closed)

Implementation intent:

- Add a read-only audit/replay helper for session/task/saga/lease event streams.
- Add grep/static guards against old direct lifecycle mutation terms.
- Update architecture docs and runbooks to reflect the Queue Service durable
  FSM host model.

Completion gate:

- Full runtime suite passes.
- Common/business contract tests pass if touched.
- Residue scan has no active old path for task/saga/session lifecycle writes.

Closure:

- PR-314 added a deterministic read-only Queue FSM audit report helper for
  session/task/saga/lease event streams, state rows, and outbox effects.
- PR-315 added final static residue guards for pure reducers, projection-only
  direct SQL writes, legacy/compat/shadow/fallback names, and generation
  authority.
- Task/Saga generation fallback to projection rows was removed; missing FSM
  state now fails fast.
- Historical schema rewrite wording was removed from active runtime code and
  matching tests.
- Full suites passed: `novaic-agent-runtime` (`434 passed`),
  `novaic-business` (`176 passed`), and `novaic-common` with runtime contracts
  (`140 passed`). `git diff --check` passed.

## Phase 7: Projection Table Quarantine

Tickets:

- `PR-316-taskqueue-state-candidate-cutover.md` (closed)
- `PR-317-sagarepository-state-candidate-cutover.md` (closed)
- `PR-318-projection-table-quarantine-guard.md` (closed)

Implementation intent:

- Keep `tq_tasks` and `tq_sagas` only as content/result/context projection
  tables for this phase.
- Move candidate selection for claim, stale recovery, cancellation, pending
  listing, and saga completion checks to FSM state tables and worker lease
  state.
- Make the remaining projection-table lifecycle columns visibly non-authority
  until a later physical schema deletion phase can remove or replace them.

Completion gate:

- `TaskQueue.claim`, `recover_stale`, `cancel_all`, and `get_topics` select
  lifecycle candidates from `tq_task_state` and `tq_worker_lease_state`, not
  `tq_tasks.status` / `tq_tasks.heartbeat_at`.
- `SagaRepository.claim`, `recover_stale`, `get_pending`, `cancel_all`, and
  `check_saga_complete` select lifecycle candidates from `tq_saga_state`,
  `tq_task_state`, and `tq_worker_lease_state`, not `tq_sagas.status`,
  `tq_sagas.heartbeat_at`, or `tq_tasks.status`.
- Static residue guards fail if projection-table lifecycle candidate queries
  are reintroduced.

Deletion scope:

- Delete projection-table lifecycle status/heartbeat selectors from active
  candidate paths.
- Do not physically delete projection columns in this phase; that requires a
  separate API/read-model and migration cut because callers still read projected
  status/result/context rows.

Closure:

- PR-316 moved TaskQueue claim, stale recovery, cancel-all, topic listing, and
  status counting candidate reads to `tq_task_state` and worker lease state.
- PR-316 also removed projection-status CAS authority from task projection
  writes and made task reducer inputs read state from the task FSM ledger.
- PR-316 closes the claimed-task cancel lease as part of cancel-all, avoiding a
  dangling acquired lease after a task lifecycle cancellation.
- PR-317 moved SagaRepository claim, stale recovery, pending listing,
  cancel-all, and completion checks to `tq_saga_state`, `tq_task_state`, and
  worker lease state.
- PR-317 also removed projection-status CAS authority from saga projection
  writes and made saga reducer inputs read state from the saga FSM ledger.
- PR-318 updated schema comments and index declarations so `tq_tasks` and
  `tq_sagas` are explicitly projection/read-model tables, while lifecycle
  authority lives in FSM event/state ledgers.
- Verification passed: Phase 7 targeted tests (`15 passed`), FSM/lease
  targeted tests (`20 passed`), full `novaic-agent-runtime` (`449 passed`),
  `novaic-business` (`176 passed`), `novaic-common` with runtime contracts
  (`140 passed`), and `git diff --check`.

## Phase 8: Physical Projection Deletion

Status: Closed

Tickets:

- `PR-319-task-projection-physical-schema-cut.md` (closed)
- `PR-320-saga-projection-physical-schema-cut.md` (closed)
- `PR-321-physical-projection-residue-guard.md` (closed)

Implementation intent:

- Physically remove task/saga lifecycle columns from `tq_tasks` and
  `tq_sagas`.
- Preserve API read-model shape by joining projection rows with
  `tq_task_state` / `tq_saga_state`.
- Keep lifecycle details such as status, claim owner, retry counters,
  heartbeat, errors, and terminal timestamps in FSM state rows only.
- Make old projection-column resurrection fail via schema and static tests.

Completion gate:

- `tq_tasks` contains only task identity, idempotency key, topic, payload,
  result, saga DAG pointers, and created timestamp.
- `tq_sagas` contains only saga identity, idempotency key, saga type, context,
  and created timestamp.
- TaskQueue and SagaRepository read through explicit joined read models.
- Static guards fail if lifecycle columns or lifecycle SQL writes return to
  projection tables.
- Full runtime suite passes, plus business/common contract suites if the public
  Queue API shape is touched.

Deletion scope:

- Delete lifecycle projection columns from `tq_tasks`: status, claimed_by,
  claimed_at, heartbeat_at, retry_count, max_retries, next_retry_at, error,
  started_at, finished_at, and version.
- Delete lifecycle projection columns from `tq_sagas`: status, claimed_by,
  claimed_at, heartbeat_at, dag_task_count, step_results, error, updated_at,
  and completed_at.
- Delete any projection-table SQL write that targets these columns.

Closure:

- PR-319 physically removed task lifecycle columns from `tq_tasks` and moved
  claimed timestamp, heartbeat, retry counters, errors, terminal timestamps,
  and generation-backed version into `tq_task_state`.
- PR-319 preserved TaskQueue public read-model shape through an explicit join
  between `tq_tasks` and `tq_task_state`; `tq_tasks` now keeps only task
  identity, idempotency key, topic, payload, result, saga DAG pointers, and
  created timestamp.
- PR-320 physically removed saga lifecycle columns from `tq_sagas` and moved
  claim timestamp plus all lifecycle/result progress fields into
  `tq_saga_state`.
- PR-320 preserved SagaRepository public read-model shape through an explicit
  join between `tq_sagas` and `tq_saga_state`; `tq_sagas` now keeps only saga
  identity, idempotency key, saga type, context, and created timestamp.
- Task and saga heartbeat now record explicit lifecycle FSM events instead of
  relying on projection-table heartbeat columns.
- PR-321 added schema and static residue guards proving projection lifecycle
  columns cannot reappear silently.
- Verification passed: Phase 8 targeted tests (`45 passed`), full
  `novaic-agent-runtime` (`451 passed`), `novaic-business` (`176 passed`),
  `novaic-common` with runtime contracts (`140 passed`), `python -m
  compileall -q queue_service`, and `git diff --check`.

## Ticket Update Rule

Every closed ticket must update:

1. Its own `Status`, `Verification`, and `Closure Notes`.
2. This file's Phase Ledger status if phase progress changed.
3. Any deletion scope that was actually removed.

## Review Rule

At review time, ask these questions before accepting a ticket:

- Did this add a new active path without deleting or explicitly scheduling the
  old path?
- Can a unit test reproduce the decision from explicit input arguments?
- Does any reducer read time, random, env, DB, file, network, or globals?
- Does any worker perform business decisions instead of publishing committed
  outbox effects?
- Is there a grep-able guard for the old behavior when deletion is claimed?
