# Runtime FSM/Worker DSL Status Documented

## Summary

Added durable architecture documentation for the current runtime FSM/worker DSL shape and a focused guard test that prevents the documentation from drifting into stale or overclaimed purity language.

## Done

- Added `docs/architecture/runtime-fsm-worker-dsl-status.md`.
- Linked the new status document from `docs/architecture/overview.md`.
- Added `novaic-agent-runtime/tests/test_pr340_runtime_dsl_status_doc.py`.
- The status document names the live FSM substrate, worker substrate, runtime roster, assembly specs, concrete assembly factories, plan-first effect runner, policy/spec/plan helpers, handler metadata, and accepted Python computation hooks.
- The document explicitly states that the current shape is spec/plan-driven and boundary-explicit, not a claim that every business behavior is already data-only.

## Verification

- `cd novaic-agent-runtime && PYTHONDONTWRITEBYTECODE=1 pytest -q -p no:cacheprovider tests/test_pr340_runtime_dsl_status_doc.py tests/test_pr340_ci_generated_artifact_hygiene.py`
  - Passed: 6 tests.
- `python3 scripts/ci/lint_runtime_worker_supervision.py`
  - Passed: `lint_runtime_worker_supervision OK`.
- `scripts/ci/lint_generated_artifacts.sh`
  - Passed: `GENERATED_ARTIFACTS_LINT=PASS`.
- `cd novaic-agent-runtime && PYTHONDONTWRITEBYTECODE=1 pytest -q -p no:cacheprovider tests/test_pr340_runtime_dsl_status_doc.py tests/test_pr340_ci_generated_artifact_hygiene.py tests/test_pr340_handler_registry_metadata.py tests/test_pr340_scheduler_health_action_specs.py tests/test_pr340_saga_launch_plans.py tests/test_pr340_task_execution_policies.py tests/test_pr340_worker_effect_plan.py tests/test_pr340_action_engine_effect_boundaries.py tests/test_pr302_session_outbox_worker_production_wiring.py tests/test_pr338_business_handlers_lifecycle_free.py tests/test_pr328_health_generic_worker.py tests/test_pr329_scheduler_generic_worker.py tests/test_pr333_saga_worker_handler_cutover.py`
  - Passed: 70 tests.
- Cleaned generated Python artifacts and reran `scripts/ci/lint_generated_artifacts.sh`.
  - Passed: `GENERATED_ARTIFACTS_LINT=PASS`.

## Known Gaps

None for this ticket. The document intentionally records that a future data-only DSL would be a separate design beyond the current accepted Python computation-hook boundary.

## Artifacts

- `docs/architecture/runtime-fsm-worker-dsl-status.md`
- `docs/architecture/overview.md`
- `novaic-agent-runtime/tests/test_pr340_runtime_dsl_status_doc.py`
