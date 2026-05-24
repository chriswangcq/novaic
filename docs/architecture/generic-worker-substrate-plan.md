# Generic Worker Substrate Plan

Status: Active
Owner: Codex
File 1: yes
Last updated: 2026-05-07

This is the controlling ledger for turning runtime workers into a shared
component-layer worker substrate while keeping business behavior in explicit
FSMs and thin handlers.

The operating loop for this file is strict:

```text
for each phase:
    check this file
    create tickets
    foreach ticket:
        solve(ticket)

solve(ticket):
    if ticket can be done directly:
        do directly
        if ticket can be complete:
            mark complete
        else:
            create gap ticket
            solve(gap ticket)
    else:
        split into smaller tickets
        foreach child ticket:
            solve(child ticket)
```

## Intent

Workers should become generic employees at the component layer. Business code
should only define:

- explicit FSM states/events/decisions;
- typed job/result contracts;
- tiny handler DSL adapters that decode jobs and delegate to injected action
  engines.

The component layer owns the employee lifecycle:

- poll;
- lease or claim;
- heartbeat;
- backoff/retry;
- exception isolation;
- graceful shutdown;
- metrics/logging;
- success/failure reporting.
- concrete source/client/action-engine construction and cleanup.

## Non-Negotiable Boundaries

1. Generic worker substrate does not import task/saga/session business FSMs.
2. Business handlers do not directly update queue lifecycle tables.
3. State transitions remain owned by Queue Service FSM + ledger/outbox.
4. Outbox effects are executed only after durable commit.
5. Every migrated worker deletes or quarantines its displaced bespoke loop.
6. No permanent dual path, fallback branch, or compatibility mode.
7. Time, sleep, IDs, clients, and config enter through explicit dependencies.
8. Tests must prove behavior at component contracts and migration boundaries.

## Target Shape

```text
main_novaic.py
  parse args
  assemble source + handler + policies
  run GenericWorker

queue_service/worker/
  contracts.py
  generic_worker.py
  policies.py
  sources.py

business worker logic
  TaskExecutionHandler
  SagaLaunchHandler
  SessionOutboxHandler
  SagaOutboxHandler
  HealthRecoveryHandler
  ScheduledWakeHandler

worker infrastructure/action engines
  TaskExecutionEngine
  SagaLaunchEngine
  HealthRecoveryEngine
  ScheduledWakeEngine
  TaskQueueJobSource
  SagaClaimSource
  worker_assemblies.py
```

## Phase Ledger

| Phase | Status | Goal | Tickets | Deletion target | Verification gate |
|---|---|---|---|---|---|
| 0 | Closed | Create controlling ledger and ticket files | PR-322 closed | none | File 1 + ticket files exist |
| 1 | Closed | Generic worker component substrate | PR-323 closed, PR-324 closed, PR-325 closed | none | substrate contract tests |
| 2 | Closed | Migrate session/saga outbox workers | PR-326 closed, PR-327 closed | bespoke outbox while loops | outbox tests + runtime smoke |
| 3 | Closed | Migrate tick workers | PR-328 closed, PR-329 closed | bespoke health/scheduler loops | health/scheduler tests |
| 4 | Closed | Migrate task worker | PR-330 closed, PR-331 closed | task worker lifecycle loop | task worker tests |
| 5 | Closed | Migrate saga worker | PR-332 closed, PR-333 closed | saga worker thread bookkeeping | saga worker tests |
| 6 | Closed | Startup registry and residue guards | PR-334 closed, PR-335 closed | duplicated worker entry wiring | full runtime tests + grep guards |
| 7 | Closed | Physical worker residue cleanup | PR-336 closed | retired entrypoint files and scripts | full runtime tests + start script checks |
| 8 | Closed | Declarative worker command registry | PR-337 closed | per-worker `main_novaic.py` run functions and branches | registry tests + full runtime tests |
| 9 | Closed | Lifecycle-free business handlers | P003 closed | business-owned `run()`/GenericWorker assembly | boundary tests + full runtime tests |
| 10 | Closed | Typed worker job/outcome DSL | P004 closed | raw job dict conventions | typed contract tests |
| 11 | Closed | Task/saga execution adapters | P005/P008/P009/P010 closed | task/saga protocol inside business handlers | protocol adapter tests |
| 12 | Closed | Declarative WorkerSpec registry | P006/P011/P012/P013 closed | handwritten registry run functions | WorkerSpec tests + full runtime tests |
| 13 | Closed | DSL residue audit and closure | P007/P014-P019 closed | stale DSL migration residue and handler-owned client/action construction | full checks + parent check |

## Phase 0: Ledger And Tickets

Tickets:

- `PR-322-generic-worker-substrate-ledger.md`

Acceptance:

- This file exists as the File 1 controller.
- Phase tickets PR-323 through PR-335 exist.
- Each ticket names scope, acceptance, verification, and deletion criteria.

Closure:

- PR-322 created this controlling ledger and materialized PR-323 through
  PR-335 ticket files.

## Phase 1: Generic Worker Component Substrate

Tickets:

- `PR-323-generic-worker-contracts.md`
- `PR-324-generic-worker-loop.md`
- `PR-325-worker-policies-and-metrics.md`

Acceptance:

- Component code is business-agnostic.
- Unit tests cover direct success, empty polling, handler failure, reporter
  failure, shutdown, and metrics.
- No production worker is migrated yet.

Closure:

- PR-323 added business-agnostic worker contracts.
- PR-324 added the generic poll/handle/report loop.
- PR-325 added explicit runtime config, shutdown, and metrics.
- Verification: `pytest -q tests/test_pr323_generic_worker_contracts.py tests/test_pr324_generic_worker_loop.py tests/test_pr325_worker_policies_and_metrics.py`.

## Phase 2: Outbox Worker Migration

Tickets:

- `PR-326-session-outbox-generic-worker.md`
- `PR-327-saga-outbox-generic-worker.md`

Acceptance:

- `session-outbox-worker` and `saga-outbox-worker` still run as visible
  subprocesses.
- `main_novaic.py` no longer owns their bespoke drain loops.
- Effect dispatch semantics are unchanged.

Closure:

- PR-326 migrated `session-outbox-worker` to
  `GenericWorker + SyntheticJobSource + SessionOutboxHandler`.
- PR-327 migrated `saga-outbox-worker` to
  `GenericWorker + SyntheticJobSource + SagaOutboxHandler`.
- The bespoke `while not stop_requested` drain loops were removed from
  `main_novaic.py` for both outbox workers.
- Verification: `pytest -q tests/test_pr286a_session_outbox_worker.py tests/test_pr302_session_outbox_worker_production_wiring.py tests/test_pr326_session_outbox_generic_worker.py tests/test_pr327_saga_outbox_generic_worker.py`.

## Phase 3: Tick Worker Migration

Tickets:

- `PR-328-health-generic-worker.md`
- `PR-329-scheduler-generic-worker.md`

Acceptance:

- Health and scheduler share the generic tick loop.
- Their handlers remain thin and explicit.
- Scheduler still delegates session decisions to Queue Service.

Closure:

- PR-328 migrated the retired health worker loop to
  `GenericWorker + SyntheticJobSource + HealthRecoveryHandler.handle`.
- PR-329 migrated the retired scheduler worker loop to
  `GenericWorker + SyntheticJobSource + ScheduledWakeHandler.handle`.
- Bespoke health/scheduler `while self.running` poll/sleep loops were removed.
- Verification: `pytest -q tests/test_health_dispatch.py tests/test_scheduler_dispatch.py tests/test_pr328_health_generic_worker.py tests/test_pr329_scheduler_generic_worker.py`.

## Phase 4: Task Worker Migration

Tickets:

- `PR-330-task-worker-generic-source.md`
- `PR-331-task-worker-handler-cutover.md`

Acceptance:

- Task worker lifecycle is component-owned.
- Task execution/idempotency remains business handler-owned.
- Task state transitions still go through Queue Service Task FSM.

Closure:

- PR-330 added `TaskQueueJobSource` to translate queue claims and saga
  dependency release decisions into `WorkerJob` values.
- PR-331 cut the retired task worker loop to `GenericWorker` and made
  `TaskExecutionHandler.handle()` the one-job business handler.
- The displaced task-worker `while self._running` claim/sleep/exception loop
  and `_claim_task` method were removed.
- Verification: `pytest -q tests/test_pr324_generic_worker_loop.py tests/test_pr330_task_worker_generic_source.py tests/test_pr331_task_worker_handler_cutover.py tests/unit/task_queue/test_retry_policy_and_idempotency.py tests/unit/task_queue/test_dedup_guard_failure_path.py tests/unit/task_queue/test_high_concurrency_retry_replay.py`.

## Phase 5: Saga Worker Migration

Tickets:

- `PR-332-concurrent-generic-worker.md`
- `PR-333-saga-worker-handler-cutover.md`

Acceptance:

- Concurrent execution is component-owned.
- Saga handler only builds DAG and reports launch/failure.
- Saga state transitions still go through Queue Service Saga FSM.

Closure:

- PR-332 added a business-agnostic `ConcurrentGenericWorker` with bounded
  concurrency, cleanup, shutdown, and result accounting.
- PR-333 added `SagaClaimSource` and cut the retired saga worker loop to the
  concurrent substrate.
- Saga-specific thread bookkeeping (`_running_sagas`, `_start_saga_thread`,
  cleanup/wait methods) was deleted from the saga business handler path.
- Verification: `pytest -q tests/test_pr332_concurrent_generic_worker.py tests/test_pr333_saga_worker_handler_cutover.py tests/unit/task_queue/test_saga_worker_boundary.py tests/test_pr310_saga_repository_fsm_cutover.py tests/test_pr313_worker_lease_cutover.py`.

## Phase 6: Registry And Residue Closure

Tickets:

- `PR-334-worker-registry-and-thin-entrypoints.md`
- `PR-335-worker-residue-guards.md`

Acceptance:

- Worker entrypoints are declarative assembly code.
- Static guards prevent reintroduced bespoke worker lifecycle loops where a
  generic substrate should be used.
- Runtime tests pass across queue, task, saga, session, scheduler, and health.

Closure:

- PR-334 added `task_queue.workers.process_runner` and wired task, saga,
  health, and scheduler entrypoints through the shared sync process runner.
- PR-335 added static residue guards for migrated worker lifecycle loops and
  entrypoint runner usage.
- Verification: `pytest -q tests/test_pr334_worker_process_runner.py tests/test_pr335_worker_residue_guards.py tests/test_pr328_health_generic_worker.py tests/test_pr329_scheduler_generic_worker.py tests/test_pr331_task_worker_handler_cutover.py tests/test_pr333_saga_worker_handler_cutover.py`.

## Phase 7: Physical Residue Closure

Tickets:

- `PR-336-worker-physical-residue-cleanup.md`

Acceptance:

- Retired standalone worker entrypoints are deleted, not left as dual-path
  bridges.
- `main_novaic.py` is the only Agent Runtime process entrypoint for task,
  saga, health, scheduler, and durable outbox workers.
- Active start scripts and packaging hints no longer point at unsupported worker
  modes or obsolete worker CLI flags.
- Static guards fail if the old launch helpers, gateway dual-path plumbing,
  or retired entrypoints return.

Closure:

- PR-336 deleted `main_task.py` and `main_saga.py`.
- Saga worker assembly moved directly into `main_novaic.py`.
- Migrated worker modules no longer expose module-local `start_worker` helpers
  or direct `__main__` blocks.
- Runtime/app start scripts were aligned with the unified worker modes:
  task-worker, saga-worker, session-outbox-worker, saga-outbox-worker, health,
  scheduler.
- Verification: `pytest -q`, `python -m compileall -q main_novaic.py task_queue/workers tests/test_pr335_worker_residue_guards.py`, `bash -n scripts/start.sh`, `bash -n novaic-app/scripts/start-backends.sh`, `python scripts/ci/check_start_config_contract.py`, `pytest -q scripts/ci/test_no_legacy_file_hot_paths.py`.

## Phase 8: Declarative Worker Command Registry

Tickets:

- `PR-337-worker-command-registry.md`

Acceptance:

- All Agent Runtime worker modes are declared in one registry.
- `main_novaic.py` delegates worker modes through the registry instead of
  carrying one `run_xxx_worker()` function and one branch per worker mode.
- Worker command parsing is explicit `WorkerSpec` data.
- Concrete `GenericWorker`/`ConcurrentGenericWorker` construction,
  `ServiceConfig` mutation, cleanup hooks, and startup text live in
  component-level `worker_assemblies.py` factories.
- Outbox workers use the same shared process runner as task, saga, health, and
  scheduler.
- Static tests fail if per-worker `main_novaic.py` functions or branches return.

Closure:

- PR-337 added `task_queue.workers.registry`; PR-338/P006 tightened it to
  declarative `WorkerSpec` data plus component-level assembly factories.
- `main_novaic.py` now uses one registry dispatch path for all worker modes and
  no longer contains per-worker run functions or per-worker branches.
- Outbox workers now use `run_sync_worker_process`, matching task, saga, health,
  and scheduler.
- Verification: `pytest -q` in `novaic-agent-runtime` -> 504 passed; targeted
  WorkerSpec/assembly suites passed.

## Phase 9: Lifecycle-Free Business Handlers

Tickets:

- `P003-lifecycle-free-business-handlers.md`

Acceptance:

- Business worker modules no longer import or construct component lifecycle
  classes such as `GenericWorker`, `ConcurrentGenericWorker`,
  `WorkerRuntime`, `WorkerRuntimeConfig`, `SyntheticJobSource`,
  `NoopReporter`, or `ShutdownController`.
- Business handler classes expose `handle(job)` and cleanup/metrics helpers
  only.
- Component-level `worker_assemblies.py` owns
  `GenericWorker`/`ConcurrentGenericWorker` construction.
- Old sync-worker `run()` and `shutdown()` shapes are deleted.

Closure:

- P003 closed. Business handler modules are lifecycle-free; tests prevent
  lifecycle substrate imports from returning.

## Phase 10: Typed Worker Job/Outcome DSL

Tickets:

- `P004-typed-worker-job-outcome-dsl.md`

Closure:

- P004 closed. Worker handlers decode explicit `WorkerJobSpec` contracts and
  return typed `WorkerResult` outcomes instead of hidden raw dict conventions.

## Phase 11: Task/Saga Execution Adapters

Tickets:

- `P005-task-saga-execution-adapters.md`
- `P008-task-execution-engine-extraction.md`
- `P009-saga-launch-engine-extraction.md`
- `P010-execution-adapter-residue-audit.md`

Closure:

- P008/P009 extracted task execution and saga launch protocols into
  `TaskExecutionEngine` and `SagaLaunchEngine`.
- P010 added static guards so business handlers cannot quietly re-own
  heartbeat, idempotency, DAG publish, mark-launched, or retry protocol paths.

## Phase 12: Declarative WorkerSpec Registry

Tickets:

- `P006-declarative-worker-spec-registry.md`
- `P011-worker-command-option-dsl.md`
- `P012-component-worker-assembly-dsl.md`
- `P013-worker-registry-residue-closure.md`

Closure:

- P011 replaced parser callbacks with `WorkerOption` data.
- P012 moved concrete process assembly into component-level
  `worker_assemblies.py` factories.
- P013 updated tests to guard the new shape and reject old registry
  `_configure_*` / `_run_*worker` residue.

## Phase 13: DSL Residue Audit And Closure

Tickets:

- `P007-dsl-residue-audit-parent-closure.md`
- `P014-worker-source-adapter-extraction.md`
- `P015-explicit-worker-handler-configuration.md`
- `P016-worker-runtime-dependency-label-cleanup.md`
- `P017-task-saga-handler-engine-injection.md`
- `P018-health-scheduler-action-engine-extraction.md`
- `P019-business-dsl-final-audit-closure.md`

Closure:

- P014 moved task/saga claim sources out of business handler modules.
- P015 removed implicit `ServiceConfig` reads from business handler and action
  boundary modules; assembly injects explicit values.
- P016 removed stale `*-sync` runtime dependency labels.
- P017 moved task/saga client and engine construction into component assembly;
  handlers now receive explicit engines and metrics.
- P018 moved health/scheduler HTTP/client/assembler action logic into
  `HealthRecoveryEngine` and `ScheduledWakeEngine`.
- P019 final audit confirmed business handler modules contain job specs and
  small handlers only; lifecycle, sources, clients, engines, retries,
  heartbeat, reporting, and cleanup are component/infrastructure owned.
- Verification: `python -m compileall -q queue_service/worker task_queue/workers main_novaic.py`, static residue scans, and `pytest -q` in
  `novaic-agent-runtime` -> 508 passed.
