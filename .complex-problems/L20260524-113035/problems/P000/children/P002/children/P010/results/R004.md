# P010 Result

## Summary

Implemented the release-controller HTTP control plane as a FastAPI app factory over the shared config, state, planner, and runner modules.

## Changes

- Added `release_controller.service.create_app`.
- Added `GET /health`.
- Added `GET /v1/status`.
- Added `GET /v1/rules`.
- Added `GET /v1/runs`.
- Added `GET /v1/runs/{run_id}`.
- Added `POST /v1/triggers`.
- Added `POST /v1/promotions/prod`.
- Added `POST /v1/rollbacks/{namespace}`.
- Added mutation execution flow that persists run records, executes through `CommandRunner`, records success or failure, and updates release pointers only for successful non-dry-run runs.
- Added `release_controller.main` entrypoint using `NOVAIC_RELEASE_CONTROLLER_CONFIG`.
- Added state store list helpers for current and previous release pointers.
- Added API tests for health, rules, trigger dry-run, run lookup 404, prod promotion rejection, rollback missing previous, and status state reporting.

## Verification

- `PYTHONPATH=novaic-release-controller python3 -m pytest novaic-release-controller/tests -q`
  - Passed: 25 tests.
- `PYTHONPATH=novaic-release-controller python3 - <<'PY' ...`
  - Created app factory with sample config plus temporary state store and confirmed title and configured port.

## Notes

- A direct app factory check with the sample config attempted to create `/opt/novaic/release-controller/state` and failed locally due permissions. The sample remains deployment-shaped; local verification now injects a temporary state store.
- Authentication and network exposure are intentionally left for deployment integration.
