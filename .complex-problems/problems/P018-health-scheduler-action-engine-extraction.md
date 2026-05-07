# P018: Health/Scheduler Action Engine Extraction

Status: done
Parent: P007
Ticket: T018

## Problem

`HealthRecoveryHandler` and `ScheduledWakeHandler` no longer own worker
lifecycle, but they still construct HTTP/action collaborators and execute
protocol-heavy side effects directly in the handler modules.

## Success Criteria

- Health and scheduler handler modules do not construct HTTP clients,
  BusinessClient, or DispatchAssembler.
- Action/protocol work is owned by explicit infrastructure engines.
- Handlers decode tick jobs and delegate to injected engines.
- Existing behavior and tests continue to pass.

## Result

- Added `HealthRecoveryEngine` and moved Queue recovery HTTP client ownership,
  timeout recovery action, metrics updates, and cleanup out of
  `health_worker.py`.
- Added `ScheduledWakeEngine` and moved due-agent scan, wake metadata/key
  construction, dispatch assembler calls, dispatch metrics, and error handling
  out of `scheduler_worker.py`.
- `HealthRecoveryHandler` and `ScheduledWakeHandler` now decode tick jobs and
  delegate to injected engines.
- `worker_assemblies.py` builds concrete clients/assemblers/engines and owns
  cleanup.
- Boundary guards reject action client/engine construction inside
  health/scheduler handler modules.

## Check

- Static scan for HTTP/client/assembler/action methods in health/scheduler
  handler modules returned no matches.
- Targeted health/scheduler boundary suite: `28 passed`.
- Full runtime suite: `508 passed`.
