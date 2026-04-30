# PR-117 — Remove Business TaskManager Legacy Proxy

| Field | Value |
| --- | --- |
| Status | `[ ]` |
| Owner | Codex |
| Created | 2026-04-30 |
| Repos | `novaic-business`, parent docs |
| Depends on | PR-112 |

## 旧分支

`business/internal/task.py` is labeled `TaskManager API (legacy tool compatibility)` and proxies task operations to Queue Service. If no active caller uses it, Business should not keep this compatibility surface.

## Detailed Plan

1. Trace all HTTP route registrations and call sites for the task proxy.
2. If no active caller exists, remove router registration and file.
3. If a caller exists, migrate it to Queue Service directly before deletion.
4. Add guardrail preventing Business from reintroducing the legacy TaskManager proxy.

## Tests

- [ ] Business route/import tests.
- [ ] Any tests touching task proxy updated or deleted.
- [ ] `python -m pytest`
- [ ] `python -m compileall -q business`

## Smoke / Deploy

- [ ] `rg "TaskManager API|tasks/spawn|tasks/create-completed" business tests`.
- [ ] `./deploy business`
- [ ] `./deploy status`

## Git

- [ ] Business commit: `refactor(business): remove task manager legacy proxy (PR-117)`
- [ ] Business push.
- [ ] Parent commit: `docs: close task manager proxy cleanup (PR-117)`
- [ ] Parent push.

