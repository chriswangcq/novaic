# Result: No Active Legacy Session/FSM Path Found, Guard Invocation Needs Bytecode Hygiene

## Summary

The active runtime/queue/task production code scan found no live old session table, pending trigger, shadow, legacy, fallback, or retired worker entrypoint branch. The broad hits are in tests/CI guard scripts, where they intentionally assert old paths stay removed. One hygiene issue was found: Python-based lint/test commands can generate `__pycache__`, so generated-artifacts lint must be run with bytecode disabled or after cleanup.

## Done

- Ran retired runtime vocabulary, runtime supervision, deploy smoke, start config, and generated artifact guards.
- Searched production runtime code for legacy/compat/fallback/shadow/FSM toggle vocabulary and old session tables.
- Searched for retired entrypoints such as bespoke session/saga outbox worker functions and active-session rebuild APIs.
- Classified hits by production code versus tests/CI guard code.
- Cleaned test-created `__pycache__` / `.pytest_cache` generated artifacts from the working tree.

## Verification

- Guard evidence:
  - `PYTHONDONTWRITEBYTECODE=1 python3 scripts/ci/lint_retired_runtime_vocabulary.py` -> `retired runtime vocabulary lint OK`.
  - `PYTHONDONTWRITEBYTECODE=1 python3 scripts/ci/lint_runtime_worker_supervision.py` -> `lint_runtime_worker_supervision OK`.
  - `PYTHONDONTWRITEBYTECODE=1 python3 scripts/ci/lint_deploy_fresh_smoke.py` -> `lint_deploy_fresh_smoke OK`.
  - `PYTHONDONTWRITEBYTECODE=1 python3 scripts/ci/check_start_config_contract.py` -> `start_config_contract OK`.
  - `bash scripts/ci/lint_generated_artifacts.sh` -> `GENERATED_ARTIFACTS_LINT=PASS`.
- Production scan evidence:
  - Scan over `novaic-agent-runtime/queue_service` and `novaic-agent-runtime/task_queue` for `legacy|compat|fallback|shadow_|shadow:|use_new|disable_fsm|enable_fsm|tq_active_sessions|pending_triggers` returned `PRODUCTION_LEGACY_SCAN_COUNT=0`.
  - Scan over production runtime/business paths for `list_active_sessions|rebuild_active_sessions_from_sagas|prompt-splice|prompt_splice|prompt splice|TRANSITIONAL|def run_session_outbox_worker|def run_saga_outbox_worker|run_task_worker(|run_saga_worker(` returned `RETIRED_ENTRYPOINT_SCAN_COUNT=0`.
- Test/CI scan evidence:
  - The same broad vocabulary over `novaic-agent-runtime/tests` and `scripts/ci` returned `TEST_CI_LEGACY_SCAN_COUNT=68`.
  - These hits are guard/test references such as `tests/test_pr315_queue_fsm_final_residue_guard.py`, `tests/test_pr257_remove_active_sessions_table.py`, `tests/test_pr255_legacy_compat_cleanup.py`, and CI scripts that intentionally ban old paths.

## Known Gaps

- Generated artifact guard is sensitive to Python commands that write bytecode. Running Python guard scripts without `PYTHONDONTWRITEBYTECODE=1` can create `__pycache__` and make a later generated-artifacts check fail. This is hygiene/tooling, not a live legacy branch.
- Existing CI coverage appears strong for retired vocabulary and process wiring, but there is not yet a pure-DSL guard that forbids new direct `execute_effect(...)` calls inside business engines. That belongs to the P004 backlog.

## Artifacts

- `.complex-problems/L20260508-165336/artifacts/P003-ticket.md`
- Residue scans over production runtime/task_queue code.
- Guard command outputs.
