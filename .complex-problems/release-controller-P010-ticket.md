# Implement release-controller HTTP control plane

## Problem Definition

The release-controller needs a central HTTP API so operators and later automation can inspect state, trigger non-prod branch releases, promote immutable refs to prod, and roll back namespaces without shelling into the host.

## Proposed Solution

Add `release_controller.service` with a FastAPI app factory that wires together:

- `ControllerConfig`
- `ReleaseStateStore`
- `ReleasePlanner`
- `CommandRunner`

Expose:

- `GET /health`
- `GET /v1/status`
- `GET /v1/rules`
- `GET /v1/runs`
- `GET /v1/runs/{run_id}`
- `POST /v1/triggers`
- `POST /v1/promotions/prod`
- `POST /v1/rollbacks/{namespace}`

Mutating endpoints should support `dry_run`, persist the run record, execute the command plan through the runner, record success/failure, and update release pointers only on successful non-dry-run deployments. Read endpoints should return explicit state from the store.

## Acceptance Criteria

- `/health` returns a minimal healthy response.
- `/v1/status` reports state root, branch heads, current pointers, previous pointers, candidates, and recent runs.
- `/v1/rules` returns configured branch rules.
- `/v1/runs` lists persisted runs.
- `/v1/runs/{run_id}` returns one run or 404.
- `/v1/triggers` starts or dry-runs a branch release through the shared planner.
- `/v1/promotions/prod` requires explicit immutable refs through the planner.
- `/v1/rollbacks/{namespace}` uses the recorded previous pointer or returns a clear 400 error.
- API tests cover health, rules, trigger dry-run, promotion rejection, and rollback missing-previous error.

## Verification Plan

- Add FastAPI in-process tests using `TestClient`.
- Run all release-controller tests.
- Run import check for app factory.

## Risks

- Mutating endpoints must not silently deploy prod from branch trigger input.
- Dry-run endpoint calls must not update current release pointers.
- API error responses must be explicit enough for automation to act on.

## Assumptions

- Authentication hardening and Docker network exposure can be finalized during deployment integration.
- Polling loop can be added after the basic API exists; manual triggers are enough for this slice.
