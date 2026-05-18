# PR-210 Maintenance Tail Cleanup

| Field | Value |
| --- | --- |
| Status | `[closed]` |
| Type | Maintenance entropy cleanup |
| Created | 2026-05-04 |
| Scope | Runtime worker names, current roadmap/ticket archaeology boundaries |
| Dependencies | PR-209 |

## Large Work Order

Clean the remaining small maintenance tails that still make the current system look like an earlier version:

1. `saga_worker.py` / `task_worker.py` are active Runtime files whose names still carry `_sync`.
2. Old roadmap tickets still contain `message_outbox`, `SPAWN_SUBAGENT`, and removed subagent tool archaeology that can be mistaken for active work unless clearly fenced as historical.

## Current-state Analysis

Already true:

- Runtime workers are synchronous by contract.
- `health_worker.py` and `scheduler_worker.py` were already renamed.
- Saga/Task worker module filenames still carried `_sync` before this ticket.
- Old `message_outbox` / `SPAWN_SUBAGENT` / removed subagent-tool paths are deleted or guarded in active code.

Missing:

- Saga/Task worker module names still use `_sync`.
- Imports, tests, packaging hiddenimports, and sync guard still reference those old module names.
- Some roadmap/ticket entries present historical mechanisms as if they were normal active roadmap material.

## Small Tickets

### PR-210A Runtime Worker Module Rename

- Objective: remove `_sync` from active Saga/Task worker module filenames and references.
- Scope:
  - `novaic-agent-runtime/task_queue/workers/saga_worker.py`
  - `novaic-agent-runtime/task_queue/workers/task_worker.py`
  - Runtime entrypoints, tests, PyInstaller spec, CI guard, and current docs.
- Expected result:
  - No active code imports `saga_worker_sync` or `task_worker_sync`.
  - Current docs no longer explain those names as historical leftovers.
- Verification:
  - `rg -n "saga_worker_sync|task_worker_sync" novaic-agent-runtime scripts docs/architecture docs/runtime-architecture.md docs/runtime docs/cortex`
  - Runtime focused tests.
  - `python scripts/ci/check_no_internal_async.py`

### PR-210B Roadmap Archaeology Fence

- Objective: keep old tickets as history without letting stale mechanisms look like current backlog or implementation guidance.
- Scope:
  - Tickets README current index and current architecture/roadmap docs.
  - Historical PR files only when a live-facing sentence is misleading.
- Expected result:
  - Current docs point to Environment/Cortex/Entangled main path.
  - Old mechanisms remain discoverable only as historical ticket context.
- Verification:
  - `rg` checks for stale terms in current docs.
  - Manual review that historical tickets are not presented as active next steps.

## Result Review

To close this ticket:

- [x] Active Runtime imports use the new worker module names.
- [x] CI guard follows the renamed files.
- [x] Focused Runtime tests pass.
- [x] Current docs no longer normalize `_sync` as a harmless active leftover.
- [x] Roadmap archaeology is fenced as historical and not presented as active guidance.

## Verification Log

- Runtime focused tests:
  - `cd novaic-agent-runtime && PYTHONPATH=.:../novaic-common pytest -q tests/unit/task_queue/test_saga_worker_boundary.py tests/unit/task_queue/test_high_concurrency_retry_replay.py tests/unit/task_queue/test_dedup_guard_failure_path.py tests/unit/task_queue/test_retry_policy_and_idempotency.py`
  - Result: `9 passed`.
- Guards:
  - `python3 scripts/ci/check_no_internal_async.py`
  - `python3 scripts/ci/lint_roadmap_ticket_archaeology.py`
  - `./scripts/ci/lint_current_docs_residue.sh`
  - `git diff --check`
- Residue scan:
  - `rg -n "saga_worker_sync|task_worker_sync" novaic-agent-runtime scripts docs/architecture docs/runtime-architecture.md docs/runtime docs/cortex docs/roadmap/technical-debt.md`
  - Result: no matches.

## Closure

Closed. Runtime worker module filenames are now `saga_worker.py` and `task_worker.py`; historical roadmap/review files that mention retired wake/subagent paths are explicitly fenced by archive banners and guarded by CI.
