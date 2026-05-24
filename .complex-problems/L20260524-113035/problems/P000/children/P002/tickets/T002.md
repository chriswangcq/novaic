# Implement release-controller core service

## Problem Definition

The project needs a central release-controller service that replaces ad hoc CI/CD orchestration with an explicit control plane. This ticket covers only the core service implementation: configuration loading, branch rule mapping, run planning, command execution abstraction, persistent release state, and HTTP APIs for status, manual trigger, prod promotion, and rollback.

It does not cover Docker packaging, Nginx exposure, host deployment, CI guard wiring, or branch cleanup. Those are handled by sibling problems in the same ledger.

## Proposed Solution

Add a new repository package for the release-controller with a small Python service and testable core modules:

- `release_controller/config.py` loads JSON config and validates branch rules, registry image names, deploy script paths, poll interval, and dry-run defaults.
- `release_controller/models.py` defines branch rules, release run records, immutable image refs, deployment targets, and run states.
- `release_controller/state.py` persists branch heads, run records, current/previous release pointers, candidates, and failure details using atomic JSON writes under a configured state directory.
- `release_controller/planner.py` maps branches to release actions, rejects unsafe prod automation, validates immutable refs for prod promotion, and produces dry-run command plans.
- `release_controller/runner.py` executes command plans through an injectable runner so unit tests can verify behavior without Docker or network access.
- `release_controller/service.py` exposes FastAPI endpoints: `/health`, `/v1/status`, `/v1/rules`, `/v1/runs`, `/v1/runs/{run_id}`, `/v1/triggers`, `/v1/promotions/prod`, and `/v1/rollbacks/{namespace}`.

The controller should use the existing deployment contract instead of inventing a second deploy mechanism:

- API: `./deploy services-image <namespace> <image-ref>`
- Factory: `./deploy factory-image <namespace> <image-ref>`

## Acceptance Criteria

- Service source exists under a clear release-controller package.
- Config loading supports repo path or URL, branch rules, registry image names, deploy script path, poll interval, and dry-run default.
- Branch rules keep service names stable and map environment through namespace, not renamed service names.
- State persistence records branch heads, run lifecycle, image refs, current and previous pointers, candidates, and failure details.
- Core logic rejects automatic prod deploy from branch polling.
- Core logic rejects prod promotion or rollback image refs that are not sha tags or digests.
- HTTP API exposes health, status, rules, runs, manual trigger, prod promotion, and rollback endpoints.
- Dry-run mode produces explicit verification/build/publish/deploy command plans without executing commands.

## Verification Plan

- Run unit tests for branch mapping, immutable ref validation, state transitions, current/previous pointer updates, and dry-run command planning.
- Run a syntax/import check for the release-controller package.
- Run targeted API tests against the FastAPI app using an in-process test client if dependencies are locally available.

## Risks

- Docker build and registry publishing behavior must stay isolated behind the command runner so tests do not mutate host Docker state.
- Production promotion must be explicit and immutable-ref only; a permissive implementation would recreate the same release ambiguity this controller is meant to remove.
- The service should not quietly fall back to GitHub Actions assumptions or implicit environment detection.

## Assumptions

- Docker packaging and remote deployment will be handled by P003 and P005.
- CI guard integration will be handled by P004.
- Existing deploy commands remain the canonical deployment surface for namespace releases.
- A small FastAPI service is acceptable because the existing backend stack already uses Python service processes.
