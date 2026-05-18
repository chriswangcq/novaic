# PR-182A — Delete legacy Business health stubs

Status: `[closed]` — 2026-05-03

## Finding

Business still exposes stub endpoints for retired paths:

- `/health/app-ws-push`
- `/health/stuck-sending`

`stuck_sending_timeout` is also still present in shared config even though no active code uses the old sending queue state.

## Scope

- Remove the two Business health stub routes.
- Remove `STUCK_SENDING_TIMEOUT` and `runtime.stuck_sending_timeout`.
- Add route/config guards.

## Tests

- Business route guard.
- Common strict config test.
- Full Business and Common tests.

## Deployment / Git

- Deploy Business/common config.
- Commit/push `novaic-business`, `novaic-common`, and root docs/pointers.

## Closure

- Removed Business `/health/app-ws-push` and `/health/stuck-sending` stub routes.
- Removed `ServiceConfig.STUCK_SENDING_TIMEOUT` and `runtime.stuck_sending_timeout` from shared and packaged app configs.
- Added Business route guard and Common strict-config guard.
- Tests:
  - `novaic-business`: `PYTHONPATH=. pytest -q tests/test_pr141_compat_cleanup.py`
  - `novaic-business`: `PYTHONPATH=. pytest -q`
  - `novaic-common`: `PYTHONPATH=. pytest -q tests/test_strict_config.py`
  - `novaic-common`: `PYTHONPATH=.:../novaic-agent-runtime pytest -q`
  - `novaic-app`: `npm run build`
- Deploy/smoke:
  - `./deploy business`
  - remote Business `/health` healthy
  - removed health stub routes return 404
