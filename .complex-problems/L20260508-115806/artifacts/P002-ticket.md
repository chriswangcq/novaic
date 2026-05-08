# Declarative Worker Assembly DSL Shrink

## Problem Definition

`task_queue/workers/worker_assemblies.py` is still thick component code. It now wires correct effect adapters, but each business assembly repeats generic worker lifecycle construction (`GenericWorker`, `ConcurrentGenericWorker`, `SyntheticJobSource`, `WorkerRuntime`, `WorkerRuntimeConfig`, `ShutdownController`) inline. That makes business assembly look like infrastructure and weakens the goal of small declarative business worker specs.

## Proposed Solution

Introduce component-level assembly helpers for common worker runtime shapes:

- runtime bundle and worker log construction
- standard generic worker construction
- concurrent generic worker construction
- synthetic tick/drain worker construction
- process spec construction remains explicit but small

Then migrate worker assembly functions to those helpers so each function mostly describes its clients, engine, handler, source, startup lines, and cleanup.

## Acceptance Criteria

- `worker_assemblies.py` has meaningfully fewer lifecycle-construction lines.
- Generic lifecycle objects are constructed through component helpers instead of repeated inline blocks.
- Task, saga, session-outbox, saga-outbox, health, and scheduler assemblies still build equivalent `WorkerProcessSpec`s.
- Focused worker assembly/handler tests pass.
- Worker modules compile.

## Verification Plan

- Compare `worker_assemblies.py` line count before/after.
- Run focused worker tests for task, saga, health, scheduler, and outbox workers where available.
- Run compile checks.

## Risks

- Over-abstracting assembly can hide important explicit dependencies; helpers should stay generic and business-agnostic.
- Cleanup ownership must remain explicit and not be swallowed by generic helpers.

## Assumptions

- Concrete client creation can remain in assembly functions for now; this ticket shrinks lifecycle construction, not client factory DSL.
