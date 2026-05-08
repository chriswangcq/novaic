# P016 Check - Scheduler Engine Effect Adapter Migration

## Summary

P016 is solved. `ScheduledWakeEngine` no longer owns `business_client` or `assembler`; due-agent scans and dispatch are explicit effect-adapter calls.

## Evidence

- `scheduled_wake.py` accepts `effect_executor` and calls `scheduler.get_due_for_wake` / `scheduler.dispatch_wake`.
- `scheduler_effects.py` owns the concrete business client and assembler.
- `assemble_scheduler_worker` wires `ScheduledWakeEffectAdapter`.
- Focused scheduler tests passed with 7 tests.
- Residue scan found no direct collaborator ownership or direct collaborator calls in `scheduled_wake.py`.

## Criteria Map

- Engine owns no business client or assembler -> satisfied by constructor refactor and residue scan.
- Due-agent scan and dispatch use `EffectExecutor` -> satisfied by explicit effects.
- Scheduler tests pass -> satisfied by focused test run.
- Assembly wires adapter explicitly -> satisfied by `assemble_scheduler_worker`.

## Execution Map

- T009 -> R006: migrated scheduler action engine and tests.

## Stress Test

- Queued dispatch path -> existing test still asserts the assembler receives the same SCHEDULED_WAKE/idempotency payload via adapter.
- Metrics path -> queued result still increments `dispatch_queued`.
- Direct collaborator regression -> P017 will automate boundary rejection; manual scan is clean.

## Residual Risk

- none for scheduler engine migration.

## Result IDs

- R006

## Blocking Gaps

- none
