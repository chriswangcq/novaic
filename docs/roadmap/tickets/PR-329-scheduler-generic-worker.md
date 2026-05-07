# PR-329 Scheduler Generic Worker

Status: Closed
Phase: 3
Owner: Codex

## Goal

Migrate scheduled wake polling to a generic tick worker.

## Scope

- Use the same tick source substrate as health.
- Extract due-agent scan and dispatch into a thin handler.
- Keep session decisions in Queue Service dispatch/FSM.

## Deletion Target

- Bespoke scheduler worker poll/sleep/exception loop.

## Acceptance

- Scheduled wakes still return queued/buffered/deduped metrics.
- Missing user/subagent data handling remains explicit.
- No session state mutation is introduced in scheduler.

## Verification

- Scheduler tests.
- Runtime scheduler startup smoke.

## Closure Notes

Implemented `ScheduledWakeHandler` as a thin generic tick-worker handler. The
component loop now owns polling, sleeping, exception isolation, metrics, and
shutdown through `GenericWorker`; scheduler business logic remains in
`_check_and_wake()` and session decisions stay delegated to Queue Service
dispatch/FSM.

Verification:

```bash
pytest -q tests/test_scheduler_dispatch.py tests/test_pr329_scheduler_generic_worker.py
```
