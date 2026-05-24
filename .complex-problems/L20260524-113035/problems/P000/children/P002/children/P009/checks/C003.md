# P009 Success Check

## Summary

P009 is successful. The release-controller now has a planner that maps branch rules into deterministic release command plans, rejects prod branch automation, validates immutable image refs for prod/rollback paths, and a command runner that supports dry-run and real subprocess execution with captured results.

## Evidence

- `main` branch planning returns namespace `staging` and includes deploy and smoke steps.
- `preview/*` branch planning resolves a namespace from the configured template.
- `release/*` branch planning returns candidate-only mode and contains no deploy step.
- A branch-triggered namespace resolving to `prod` is rejected.
- Image ref validation accepts digest refs and `sha-<hex>` tags while rejecting `latest`, mutable environment tags, and semantic tags.
- Prod promotion rejects mutable refs and plans deploy steps only for explicit immutable refs.
- Rollback planning reads the previous pointer and rejects missing previous state.
- The runner dry-runs without executing commands and captures subprocess failure details in real mode.
- Verification ran and passed: `PYTHONPATH=novaic-release-controller python3 -m pytest novaic-release-controller/tests -q`.
- Additional planner output check confirmed dry-run steps: `git-fetch`, `git-checkout`, `verify-1`, `build-api-backend`, `build-llm-factory`, `push-api-backend`, `push-llm-factory`, `deploy-api-staging`, `deploy-factory-staging`, `smoke-staging`.

## Criteria Map

- `main` maps to staging auto-deploy: covered by `test_main_maps_to_staging_deploy_plan`.
- `preview/*` template namespace: covered by `test_preview_namespace_uses_template_slug`.
- `release/*` candidate-only without deployment: covered by `test_release_branch_is_candidate_only_without_deploy`.
- Branch triggers cannot deploy prod: covered by `test_branch_trigger_cannot_resolve_prod`.
- Prod promotion immutable refs only: covered by `test_prod_promotion_requires_immutable_refs` and `test_immutable_image_ref_validation`.
- Rollback uses previous pointer and reports missing previous clearly: covered by `test_rollback_uses_previous_pointer`.
- Dry-run command planning includes verify/build/push/deploy/smoke: confirmed by direct planner output check.
- Runner records stdout, stderr, exit code, and failure: covered by `test_runner_captures_subprocess_failure`.

## Execution Map

- Implemented planner, immutable ref validation, command plan construction, and runner.
- Added `CommandResult` model and package exports.
- Added planner/runner tests.
- Ran all current release-controller tests.

## Stress Test

- The rollback test first asserts that missing previous state fails before planning a valid rollback.
- The runner failure test confirms execution stops after the first non-zero command and does not execute subsequent steps.
- The immutable ref tests ensure strict validation is not weakened for convenience.

## Residual Risk

- The planner currently creates command plans but does not yet persist run lifecycle transitions during execution. That belongs to the HTTP/API execution slice, where the controller can coordinate state updates around user-triggered runs.

## Result IDs

- R003
