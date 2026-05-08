# P019 Ticket - Migrate Worker Assemblies To Helper Substrate

## Problem Definition

`task_queue/workers/worker_assemblies.py` still owns repeated worker assembly mechanics even after the generic helper substrate exists. Business assembly functions continue to hand-roll runtime bundles, `GenericWorker`/`ConcurrentGenericWorker`/`SyntheticJobSource` construction, reporter defaults, and error logging. That keeps business-facing assembly thicker than the target DSL shape and leaves old construction paths easy to preserve by accident.

## Proposed Solution

Migrate concrete worker assembly functions onto `task_queue.workers.assembly_helpers`.

The migration should:

- Use helper builders for generic, concurrent, and synthetic workers.
- Extend helpers only with business-agnostic primitives if outbox assemblies need explicit runtimes.
- Keep effect adapters explicit at assembly boundaries.
- Remove direct worker-construction mechanics from `worker_assemblies.py`.
- Update tests that asserted old constructor text so they assert helper-backed behavior and boundary cleanliness instead.

## Acceptance Criteria

- Task, saga, health, scheduler, session-outbox, and saga-outbox assemblies use helper builders for worker construction.
- `worker_assemblies.py` no longer directly constructs `GenericWorker`, `ConcurrentGenericWorker`, or `SyntheticJobSource`.
- Repeated runtime/config/reporter boilerplate in `worker_assemblies.py` is reduced.
- Tests prove helper-backed assembly behavior for the migrated workers.
- Existing effect adapter boundary tests still pass.
- Compile checks pass.

## Verification Plan

- Run focused assembly/helper tests.
- Run task/saga/health/scheduler cutover and dispatch tests.
- Run effect boundary guard tests.
- Run outbox-related tests found by repository search.
- Run compile checks for `task_queue/workers`.
- Use `rg` to confirm old worker-construction residue is gone from `worker_assemblies.py`.
- Record final line-count and residue evidence.

## Risks

- Outbox workers use custom runtime dependencies and may need helper extension.
- Tests may currently assert implementation text rather than behavior and need cleanup.
- A shallow migration could leave new helper code unused, so residue checks must be explicit.

## Assumptions

- The helper substrate from P018 is accepted as the generic infra boundary.
- Business assembly may still instantiate explicit effect adapters; the goal is to remove worker lifecycle construction mechanics, not hide business adapters.
