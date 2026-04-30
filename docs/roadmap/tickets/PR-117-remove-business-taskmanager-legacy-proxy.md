# PR-117 — Remove Business TaskManager Legacy Proxy

| Field | Value |
| --- | --- |
| Status | `[✓]` |
| Owner | Codex |
| Created | 2026-04-30 |
| Repos | `novaic-business`, parent docs |
| Depends on | PR-112 |

## 旧分支

`business/internal/task.py` is labeled `TaskManager API (legacy tool compatibility)` and proxies task operations to Queue Service. If no active caller uses it, Business should not keep this compatibility surface.

## Detailed Plan

1. [x] Trace all HTTP route registrations and call sites for the task proxy.
   - No active caller found for Business `/internal/tasks/spawn`, `/internal/tasks/create-completed`, `/internal/tasks/{task_id}`, `/internal/tasks/{task_id}/cancel`, `/internal/tasks/{task_id}/result`.
   - Queue Service callers already use `/api/queue/tasks/*` directly.
2. [x] Keep `business/internal/task.py` registered because it still owns separate `agent-tasks` / `growth-logs` business routes.
3. [x] Delete only the legacy Queue TaskManager proxy routes and `_forward_*` helpers.
4. [x] Add guardrail preventing Business from reintroducing the legacy TaskManager proxy.

## Tests

- [x] Business route/import tests.
- [x] Any tests touching task proxy updated or deleted.
- [x] `python -m pytest`
- [x] `python -m compileall -q business`

## Smoke / Deploy

- [x] `rg "TaskManager API|tasks/spawn|tasks/create-completed" business tests` only hits guardrail tests / unrelated Queue URL config tests.
- [x] `./deploy business`
- [x] `./deploy status`
- [x] Remote source confirms legacy proxy markers absent and `quadrant-tasks` / `growth-logs` still present.

## Git

- [x] Business commit: `refactor(business): remove task manager legacy proxy (PR-117)`
- [x] Business push.
- [x] Parent commit: `docs: close task manager proxy cleanup (PR-117)`
- [x] Parent push.
