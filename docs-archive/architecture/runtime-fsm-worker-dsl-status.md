# Runtime FSM And Worker DSL Status

Status: Current implementation status
Owner: Queue Service / Runtime
Last updated: 2026-05-08

This document records the implemented runtime shape after the FSM and generic
worker cleanup. It is a status document, not a roadmap claim: the runtime is now
spec-driven and plan-first in the worker layer, with explicit accepted Python
computation hooks. It is not a claim that every business behavior has become a
data-only DSL.

## Current Shape

```text
runtime process
  -> worker command registry
  -> WorkerRuntimeSpec
  -> WorkerAssemblySpec
  -> GenericWorker / ConcurrentGenericWorker
  -> typed source + thin handler
  -> action engine
  -> pure policy/spec/plan helpers
  -> EffectPlanRunner
  -> concrete effect adapter
```

The Queue Service remains the authoritative state coordinator. Durable state,
inbox/outbox records, and generation checks live in Queue Service persistence;
worker processes are execution hosts that poll, lease, handle, and report.

## Live Code Pointers

| Layer | Live path | Role |
|---|---|---|
| Generic FSM substrate | `novaic-agent-runtime/queue_service/fsm/` | Business-agnostic FSM runner and SQLite-backed FSM store. |
| Worker substrate | `novaic-agent-runtime/queue_service/worker/` | Generic worker contracts, sources, reporters, policies, and plan-first effect execution. |
| Runtime worker roster | `novaic-agent-runtime/task_queue/workers/runtime_roster.py` | Single source of truth for enabled runtime worker commands. |
| Worker command specs | `novaic-agent-runtime/task_queue/workers/command_specs.py` | Declarative command metadata used by runtime startup. |
| Worker assembly specs | `novaic-agent-runtime/task_queue/workers/assembly_specs.py` | Data-oriented assembly contract for source, handler, runtime config, and concurrency. |
| Assembly registry | `novaic-agent-runtime/task_queue/workers/worker_assemblies.py` | Spec-backed worker lookup surface. |
| Concrete assembly factories | `novaic-agent-runtime/task_queue/workers/assembly_factories.py` | Explicit construction boundary for clients, sources, handlers, engines, and workers. |
| Effect plan runner | `novaic-agent-runtime/queue_service/worker/effects.py` | Executes `EffectPlan` values and enforces success through `require_success`. |
| Task execution policies | `novaic-agent-runtime/task_queue/workers/task_execution_policies.py` | Pure task execution decisions and effect plans. |
| Saga launch plans | `novaic-agent-runtime/task_queue/workers/saga_launch_plans.py` | Pure saga launch normalization and mark-failed plans. |
| Scheduler action specs | `novaic-agent-runtime/task_queue/workers/scheduler_action_specs.py` | Pure scheduled wake scan and dispatch decisions. |
| Health action specs | `novaic-agent-runtime/task_queue/workers/health_action_specs.py` | Pure health recovery scan specs. |
| Handler metadata | `novaic-agent-runtime/task_queue/handlers/__init__.py` | Topic-to-handler metadata without worker lifecycle ownership. |
| Saga hook declaration | `novaic-agent-runtime/task_queue/saga.py` | Explicit callback extension points accepted as Python computation hooks. |

## What Is Spec Driven Now

- Runtime startup resolves worker commands from roster and command specs.
- Worker assembly is described by `WorkerAssemblySpec`; concrete dependency
  construction is isolated in assembly factories.
- Poll, lease, heartbeat, retry, shutdown, and report behavior is owned by the
  generic worker substrate.
- Worker handlers are thin adapters over typed jobs and action engines.
- Action engines compile explicit `EffectPlan` values and execute them through
  `EffectPlanRunner`; they no longer directly scatter ad hoc effect execution.
- Task execution, saga launch, scheduler dispatch, and health recovery each have
  named pure policy/spec/plan helpers.
- Handler registration exposes metadata so runtime orchestration can reason
  about pools and topics without importing lifecycle code into business
  handlers.

## Accepted Computation Hooks

These are intentional boundaries, not hidden fallback paths:

- Business handlers remain Python adapters because they decode typed jobs,
  invoke domain action engines, and return typed outcomes.
- Saga definitions may call explicitly named callback extension points declared
  by `SAGA_CALLBACK_EXTENSION_POINTS`.
- Concrete clients, repositories, clocks, and adapters are built in
  `assembly_factories.py`; this is the dependency boundary for I/O objects.
- Action engines may own logging, metrics, and small orchestration decisions
  around pure plans.
- Effect adapters own external I/O. Pure policy modules only produce effect
  descriptions.

## What This Is Not

- It is not a permanent dual path with old bespoke worker loops.
- It is not a dual-path bridge for no-generation attach or retired lifecycle
  branches.
- It is not a declaration that all business behavior is data-only.
- It is not a place for worker handlers to create worker runtimes, connect
  directly to queue lifecycle tables, or bypass Queue Service FSM ownership.

## Guardrails

The current status is guarded by targeted tests and lints:

- `novaic-agent-runtime/tests/test_pr340_worker_effect_plan.py`
- `novaic-agent-runtime/tests/test_pr340_task_execution_policies.py`
- `novaic-agent-runtime/tests/test_pr340_saga_launch_plans.py`
- `novaic-agent-runtime/tests/test_pr340_scheduler_health_action_specs.py`
- `novaic-agent-runtime/tests/test_pr340_handler_registry_metadata.py`
- `novaic-agent-runtime/tests/test_pr340_action_engine_effect_boundaries.py`
- `novaic-agent-runtime/tests/test_pr340_ci_generated_artifact_hygiene.py`
- `scripts/ci/lint_runtime_worker_supervision.py`
- `scripts/ci/lint_generated_artifacts.sh`

## Residual Shape

The important remaining distinction is conceptual, not hidden wiring: the
runtime is now explicit and boundary-driven, but it still uses Python functions
for domain computation hooks. A future data-only DSL would need a separate
design that replaces those hooks with durable declarative semantics. Until then,
the correct status is:

```text
generic FSM substrate
+ generic worker substrate
+ declarative roster/assembly specs
+ pure policy/spec/plan helpers
+ explicit Python computation hooks
+ plan-first effect execution
```
