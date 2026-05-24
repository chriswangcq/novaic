# P010 Success Check

## Summary

P010 is successful. The release-controller now exposes the required HTTP control plane and the mutating endpoints execute through the shared planner and runner rather than duplicating release rules.

## Evidence

- `/health`, `/v1/status`, `/v1/rules`, `/v1/runs`, `/v1/runs/{run_id}`, `/v1/triggers`, `/v1/promotions/prod`, and `/v1/rollbacks/{namespace}` are implemented in `release_controller.service`.
- Dry-run trigger persists a run and does not update the current staging pointer.
- Prod promotion with a mutable ref returns 400.
- Rollback with no previous pointer returns 400.
- Status returns branch heads, current pointers, previous pointers, candidates, and recent runs.
- Verification ran and passed: `PYTHONPATH=novaic-release-controller python3 -m pytest novaic-release-controller/tests -q`.
- Additional API check confirmed immutable prod promotion dry-run returns 200 and does not update the prod current pointer.

## Criteria Map

- `/health`: covered by `test_health_and_rules`.
- `/v1/status`: covered by `test_status_reports_release_pointers_and_candidates`.
- `/v1/rules`: covered by `test_health_and_rules`.
- `/v1/runs`: covered by `test_trigger_dry_run_persists_run_without_release_pointer`.
- `/v1/runs/{run_id}` 404 behavior: covered by `test_run_lookup_404`.
- `/v1/triggers`: covered by dry-run trigger test.
- `/v1/promotions/prod`: covered by rejection test and positive immutable dry-run API check.
- `/v1/rollbacks/{namespace}`: covered by missing previous 400 test.

## Execution Map

- Implemented app factory and endpoint handlers.
- Added state listing helpers.
- Added executable entrypoint.
- Added in-process FastAPI API tests.
- Ran all current release-controller tests.

## Stress Test

- Dry-run mutation verifies that command execution is represented while release pointers remain unchanged.
- Promotion rejection verifies that API calls cannot bypass immutable-ref planner rules.
- Missing rollback state verifies that the API returns an explicit operator-facing error instead of fabricating a fallback.

## Residual Risk

- Authentication, network exposure, and container runtime configuration are intentionally deferred to deployment integration. The control plane surface itself is implemented and verified locally.

## Result IDs

- R004
