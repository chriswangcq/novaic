# T004: Typed Worker Job And Outcome DSL

Status: done
Problem: P004

## Objective

Replace hidden raw dict conventions with explicit worker job and outcome specs.

## Scope

- Worker job source modules.
- Worker handler boundaries.
- Tests for decoding and invalid payloads.

## Expected Result

Business handlers receive explicit typed/spec objects or a single validated
envelope instead of repeatedly inspecting raw dicts.

## Verification

- Targeted job/outcome tests.
- Existing runtime tests.

## Execution Notes

- Added generic `WorkerJobSpec`, `WorkerJobDecodeError`, and
  `decode_worker_job` to `queue_service.worker`.
- Task, saga, health, scheduler, session-outbox, and saga-outbox handlers now
  declare accepted job specs and decode once at the `handle(job)` boundary.
- Registry synthetic jobs now reuse spec constants for health, scheduler, and
  outbox workers.
- Added invalid kind/payload tests across task, saga, health, scheduler, and
  outbox handlers.
- Verification: compileall and targeted pytest suite passed (`56 passed`).
