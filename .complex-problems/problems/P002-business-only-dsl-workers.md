# P002: Business-Only DSL Worker Architecture

Status: done
Parent: none
Ticket: T002

## Problem

Runtime workers now share a generic worker substrate and a declarative command
registry, but business worker modules still contain execution mechanics:

- per-worker `run()` methods;
- `GenericWorker` / `ConcurrentGenericWorker` construction;
- heartbeat wrappers;
- raw dict job decoding;
- queue complete/fail/mark-launched side effects;
- task idempotency and retry protocol;
- handwritten command assembly in registry.

The target is stricter: business code should read like a small DSL/spec for
business computation, while component/infrastructure code owns lifecycle,
protocol, retries, heartbeat, reporting, and state advancement.

## Success Criteria

- Business worker modules no longer own `run()` lifecycle methods or construct
  `GenericWorker` / `ConcurrentGenericWorker`.
- Worker jobs and business outcomes are typed or spec-shaped rather than raw
  dict conventions hidden inside handlers.
- Task execution protocol is explicit infrastructure: heartbeat, idempotency,
  retry, complete/fail reporting, and handler dispatch are not tangled in the
  business handler class.
- Saga launch protocol is explicit infrastructure: heartbeat, DAG publish, and
  mark-launched/failed reporting are not tangled in the business handler class.
- Scheduler and health handlers expose small action specs instead of carrying
  worker lifecycle wiring.
- `WorkerRegistry` becomes mostly declarative `WorkerSpec` data rather than a
  long list of handwritten assembly functions.
- Residue guards reject old lifecycle methods, old class names, compatibility
  wrappers, and untyped raw job-path patterns where the DSL has replaced them.
- Runtime tests pass, plus targeted static DSL boundary tests.

## Subproblems

- P003: Lifecycle-free business handlers.
- P004: Typed worker job and outcome DSL.
- P005: Task and saga execution protocol adapters.
- P006: Declarative WorkerSpec registry.
- P007: DSL residue audit and parent closure.

## Results

- Worker business modules now expose only typed job specs and small delegating
  handlers.
- Component/infrastructure modules own generic worker lifecycle, sources,
  concrete clients, action/protocol engines, retries, heartbeat, reporting,
  logging, config injection, and cleanup.
- Retired entrypoints and stale worker labels were deleted.
- Architecture documentation and ledger checks record the final shape.

## Check

- Success. Criteria-to-evidence mapping is recorded in
  `C002-business-only-dsl-workers.md`.
- Full runtime suite: `508 passed`.

## Follow-ups

- None.
