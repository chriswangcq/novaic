# T001: Declarative Worker Registry Perfect-Shape Cutover

Status: done
Problem: P001

## Objective

Move Agent Runtime worker command assembly into a declarative registry and make
`main_novaic.py` dispatch all worker modes through that registry.

## Scope

- `novaic-agent-runtime/main_novaic.py`
- `novaic-agent-runtime/task_queue/workers/process_runner.py`
- new registry module under `novaic-agent-runtime/task_queue/workers/`
- generic worker substrate shutdown compatibility if needed
- worker residue/registry tests
- generic worker architecture docs and ticket files

## Expected Result

Worker modes are data/registry entries, not scattered imperative command
branches. The only remaining explicit `main_novaic.py` branches are non-worker
services such as gateway, queue-service, and vmcontrol.

## Verification

- New registry tests.
- Existing worker cutover/residue tests.
- `python -m compileall`.
- Full `novaic-agent-runtime` pytest.
- Startup script syntax and config contract checks.

## Execution Notes

- Started 2026-05-07.
- Predicted one-go: scope is focused, current tests are strong, and failure is
  reversible in the uncommitted branch.
- Completed 2026-05-07.
- Added `task_queue.workers.registry` and made `main_novaic.py` dispatch worker
  modes through `run_worker_mode_if_registered`.
- Updated outbox and production-wiring tests to assert registry ownership
  instead of old `main_novaic.py` worker functions.
- Added PR-337 architecture/ticket docs and static registry tests.
