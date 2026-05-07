# PR-334 Worker Registry And Thin Entrypoints

Status: Closed
Phase: 6
Owner: Codex

## Goal

Make worker process entrypoints declarative assembly code.

## Scope

- Add a small worker registry or builder.
- Reduce `main_novaic.py` worker modes to argument parsing plus worker
  assembly.
- Preserve process names, logs, and CLI behavior.

## Deletion Target

- Repeated startup wiring that should be shared.
- Duplicate signal handling and loop setup.

## Acceptance

- Start script process layout unchanged.
- Each worker mode shows its source, handler, policies, and dependencies.

## Verification

- Runtime startup tests or CLI smoke.
- Deploy script remains compatible.

## Closure Notes

Added `task_queue.workers.process_runner` with `WorkerProcessSpec` and
`run_sync_worker_process()`. Task, saga, health, and scheduler entrypoints now
delegate signal handling, startup printing, run/finally cleanup, and shutdown
completion logging to the shared component runner while preserving CLI process
layout.

Verification:

```bash
pytest -q tests/test_pr334_worker_process_runner.py
```
