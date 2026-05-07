# P015: Explicit Worker Handler Configuration

Status: done
Parent: P002
Ticket: T015

## Problem

Worker business handlers still read `ServiceConfig` as constructor fallbacks and
some names still contain the old `sync` wording. That violates explicit
dependency boundaries and leaves misleading residue even though the live
lifecycle path has been migrated.

## Success Criteria

- Business handlers require explicit runtime URLs/timeouts/keys through
  constructor arguments.
- Business handler modules do not import `ServiceConfig`.
- Handler names no longer contain stale `sync` suffixes.
- Assembly layer remains responsible for reading `ServiceConfig` once and
  injecting explicit values.
- Tests cover explicit construction.

## Result

- Worker business handlers now require explicit URLs, timeouts, keys, retry
  policy, and runtime dependencies through constructor arguments.
- `task_execution.py` receives `saga_step_timeout` explicitly instead of
  reading `ServiceConfig`.
- `wake/assembler_factory.py` receives `business_url` and
  `queue_service_url` explicitly instead of reading `ServiceConfig`.
- Handler names use live names (`task-worker`, `saga-worker`,
  `health-worker`, `scheduler`) with stale `sync` names removed.
- `worker_assemblies.py` remains the boundary that reads process config and
  injects explicit values into component/business objects.

## Check

- `python -m compileall -q task_queue/workers`
- Static scan for `ServiceConfig` and retired `*-sync` names in worker
  boundary modules returned no matches.
- Targeted worker boundary suite: `40 passed`.
- Full runtime suite: `506 passed`.
