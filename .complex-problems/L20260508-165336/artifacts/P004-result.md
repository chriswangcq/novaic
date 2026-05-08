# Result: Pure DSL Remediation Backlog

## Summary

The current system is live on the new FSM/worker/roster path and has no active old session/FSM branch found, but it is not pure DSL. The next work should not rework the live wiring. It should migrate the remaining Python orchestration islands into explicit specs/planners, then delete or guard against the old hand-coded paths.

## Done

- Synthesized P001/P002/P003 into an implementation backlog.
- Separated already-done infrastructure from remaining pure-DSL gaps.
- Listed each future ticket with target files, end state, deletion/cleanup, and guard requirements.

## Verification

- Source inputs:
  - P001 / R000: runtime path is live through `runtime_roster`, worker registry, and generic FSM ledgers.
  - P002 / R001: not pure DSL; hand-written worker assemblies and action engines remain.
  - P003 / R002: no active old session/FSM branch found; generated artifact guard needs bytecode hygiene.

## Backlog

### DSL-001: Worker Assembly Spec Substrate

- Target files:
  - Add component substrate near `novaic-agent-runtime/task_queue/workers/assembly_specs.py`.
  - Migrate `novaic-agent-runtime/task_queue/workers/worker_assemblies.py`.
  - Keep `novaic-agent-runtime/task_queue/workers/assembly_helpers.py` as component infrastructure.
- End state:
  - Worker assembly becomes data/spec rows: clients, adapters, engine class, handler class, source class, metrics class, poll policy, cleanup policy.
  - Per-worker Python assembly functions shrink to a generic interpreter or are deleted.
- Cleanup:
  - Delete duplicated hand assembly logic for task/saga/health/scheduler/outbox workers after migration.
- Guard:
  - Add a test forbidding direct client/engine/handler instantiation in `worker_assemblies.py` except inside the spec interpreter.

### DSL-002: Plan-First Action Engine Contract

- Target files:
  - `queue_service/worker/effects.py`
  - `task_queue/workers/task_execution.py`
  - `task_queue/workers/saga_launch.py`
  - `task_queue/workers/scheduled_wake.py`
  - `task_queue/workers/health_recovery.py`
- End state:
  - Action engines compute explicit decisions/effect plans first.
  - Generic runner executes plans through adapters.
  - Engines no longer call `execute_effect(...)` directly.
- Cleanup:
  - Delete `_effect(...)` helper methods from engines after cutover.
- Guard:
  - Add a residue test banning `execute_effect(` in action engines.
  - Keep `execute_effect` only in generic runner/substrate or compatibility-free helper if still needed.

### DSL-003: Task Execution Policy Tables

- Target files:
  - `task_queue/workers/task_execution.py`
  - New policy/spec file, for example `task_queue/workers/task_execution_specs.py`.
- End state:
  - Idempotency actions, retry decisions, completion/failure transitions, and saga task adaptation are represented as small policy tables or pure decision functions.
  - Task execution engine becomes orchestration shell around a generic plan runner.
- Cleanup:
  - Remove imperative branching from `_execute_task` where it can be expressed as decision/policy rows.
- Guard:
  - Tests assert retry/idempotency scenarios from explicit input snapshots produce deterministic plans.

### DSL-004: Saga Launch and Saga Definition Purity

- Target files:
  - `task_queue/workers/saga_launch.py`
  - `task_queue/saga.py`
  - `task_queue/sagas/*.py`
- End state:
  - Saga launch emits a plan from saga state + definition + context.
  - Saga definitions remain DSL, but callback-heavy payload builders/deciders are isolated and named as explicit extension points.
- Cleanup:
  - Delete direct publish/mark-launched loops from `SagaLaunchEngine` after generic plan execution exists.
- Guard:
  - Tests assert saga definitions compile to deterministic DAG/effect plans.

### DSL-005: Scheduler and Health Action Specs

- Target files:
  - `task_queue/workers/scheduled_wake.py`
  - `task_queue/workers/health_recovery.py`
  - `task_queue/workers/scheduler_effects.py`
  - `task_queue/workers/health_effects.py`
- End state:
  - Scheduler and health become small action specs: scan effect, classify result, emit follow-up effects/metrics.
  - Direct effect calls move out to the generic plan runner.
- Cleanup:
  - Remove bespoke `_record_dispatch_result`, `_record_dispatch_error`, and recovery effect execution branches where expressible as result classifiers.
- Guard:
  - Tests assert scan/recovery outcomes map to exact plans and metrics deltas.

### DSL-006: Business Handler Registry Review

- Target files:
  - `task_queue/handlers/__init__.py`
  - `task_queue/handlers/*.py`
- End state:
  - Keep real business computation as Python only where it is genuinely computation.
  - Make handler registration/spec metadata declarative: topic, payload schema, pool, side-effect boundary, lifecycle ownership.
- Cleanup:
  - Delete hidden lifecycle/process wiring from handler modules.
- Guard:
  - Add a registry test that handler modules cannot import worker lifecycle, queue DB, or concrete process/runtime ownership.

### DSL-007: CI Guard Hygiene

- Target files:
  - `scripts/ci/*`
  - Any top-level CI entrypoint or deploy check that chains Python lints and generated-artifact lint.
- End state:
  - Python-based guard commands run with `PYTHONDONTWRITEBYTECODE=1`, or the generated-artifact guard is run in a clean/bytecode-free mode.
- Cleanup:
  - Remove generated cache artifacts before final checks.
- Guard:
  - `bash scripts/ci/lint_generated_artifacts.sh` passes after the normal guard sequence.

### DSL-008: Pure DSL Architecture Status Document

- Target files:
  - Existing runtime/FSM design docs or a new ledger/design note under `.complex-problems` or project docs.
- End state:
  - Document the current state honestly: live FSM/roster path, no active old session branch found, not pure DSL yet.
  - Reference the backlog above so future work does not repeat broad rewrites without deletion.
- Cleanup:
  - Remove or update stale docs that imply the runtime is already pure DSL.
- Guard:
  - Optional doc lint/search for forbidden “pure DSL complete” wording unless supported by implementation.

## Already Done / Do Not Rework

- Do not rework worker process launch through `runtime_roster`; P001 proved it is live.
- Do not reintroduce `tq_active_sessions`, pending triggers, shadow dispatch, or old direct worker entrypoints; P003 scans and guards are clean.
- Do not add another parallel FSM path. Further work should sit on the existing `FsmTransitionRunner`, worker registry, runtime roster, and generic worker substrate.

## Known Gaps

- This result is a plan/backlog, not an implementation.
- The highest-impact next ticket is DSL-002, because once engines emit plans, DSL-001/003/004/005 can converge without preserving direct effect branches.

## Artifacts

- `.complex-problems/L20260508-165336/artifacts/P004-ticket.md`
- P001/R000, P002/R001, P003/R002 audit results.
