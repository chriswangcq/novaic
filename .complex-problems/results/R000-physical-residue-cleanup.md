# R000: Physical Residue Cleanup Result

Problem: P000
Ticket: T000
Status: done

## What Changed

- Removed retired standalone worker entrypoints:
  - `novaic-agent-runtime/main_task.py`
  - `novaic-agent-runtime/main_saga.py`
- Moved Saga worker assembly into `novaic-agent-runtime/main_novaic.py`.
- Removed stale worker-side `gateway_url` compatibility plumbing from migrated
  worker classes and constructor call sites.
- Removed migrated worker module-local launch helpers and direct `__main__`
  blocks.
- Updated `novaic-app/scripts/start-backends.sh` so the worker section no
  longer invokes unsupported `watchdog` mode or removed worker CLI flags, and
  starts durable outbox workers explicitly.
- Updated `novaic-agent-runtime/novaic-agent-runtime.spec` hidden imports and
  comments away from retired worker module names.
- Expanded `novaic-agent-runtime/tests/test_pr335_worker_residue_guards.py`.
- Documented the physical cleanup in `docs/architecture/generic-worker-substrate-plan.md`
  and `docs/roadmap/tickets/PR-336-worker-physical-residue-cleanup.md`.

## Residue Scan

Worker hot paths no longer contain:

- `def start_worker(`
- `def start_multiple_workers(`
- migrated worker `__main__` blocks
- worker-side `gateway_url` compatibility arguments
- `main_saga` delegation from `main_novaic.py`
- app-script `watchdog` worker invocation
- runtime packaging references to retired `*_worker_sync` module names

Remaining `--gateway-url` occurrences in `scripts/start.sh` are for Business
and Device service boundaries, not Agent Runtime worker compatibility.
