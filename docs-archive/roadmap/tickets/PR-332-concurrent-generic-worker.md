# PR-332 Concurrent Generic Worker

Status: Closed
Phase: 5
Owner: Codex

## Goal

Add component-layer concurrency support for workers that run multiple jobs at
once.

## Scope

- Add bounded concurrency policy or `ConcurrentGenericWorker`.
- Keep concurrency independent of saga business logic.
- Make shutdown and heartbeat lifecycle explicit.

## Deletion Target

- Saga worker-specific thread bookkeeping once PR-333 migrates.

## Acceptance

- Component tests cover max concurrency, cleanup, shutdown, and handler errors.
- No saga imports in concurrency substrate.

## Verification

- Generic concurrency tests.

## Closure Notes

Added `ConcurrentGenericWorker` as a business-agnostic bounded-concurrency
substrate. It owns job thread lifecycle, cleanup, shutdown, handler error
capture, reporter error accounting, and generic worker metrics without
importing saga/task/session business modules.

Verification:

```bash
pytest -q tests/test_pr332_concurrent_generic_worker.py
```
