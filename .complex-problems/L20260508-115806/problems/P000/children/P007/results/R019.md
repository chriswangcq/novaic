# Final residue closure and verification result

## Summary

Completed the final residue audit. The audit found two real closure gaps and fixed both: direct HTTP client construction remained in Cortex/Runtime paths, and a lifecycle ownership lint still checked an obsolete private helper name. After fixes, the runtime test suite and root lint suite pass.

## Done

- Ran focused runtime/FSM/worker test suites:
  - Worker assembly/effect boundaries.
  - Session harness/generic FSM/session outbox boundaries.
  - Task/saga FSM and generic worker substrate tests.
- Ran full `novaic-agent-runtime` pytest suite.
- Fixed direct HTTP client residue:
  - `novaic-cortex/novaic_cortex/blob_payload.py` now uses `common.http.clients.internal_async_client`.
  - `novaic-cortex/novaic_cortex/blob_store.py` now uses `common.http.clients.internal_async_client`.
  - `novaic-agent-runtime/task_queue/handlers/tool_handlers.py` now uses `internal_sync_client` for Blob file fetches.
  - Removed stale `novaic-cortex/novaic_cortex/file_resolver.py` httpx allowlist entry.
  - Updated tool handler tests to patch the explicit `internal_sync_client` boundary instead of `httpx.Client`.
- Fixed lifecycle ownership lint drift:
  - `scripts/ci/lint_lifecycle_loop_ownership.sh` now guards `session_projection.merge_pending_metadata` and `SessionRepository` usage of `build_pending_input_projection`.
- Re-ran root lint chain after fixes.
- Ran final compile and diff checks.

## Verification

- `pytest -q` in `novaic-agent-runtime`: `530 passed`.
- Focused test sweeps before full run:
  - `38 passed`
  - `103 passed`
  - `136 passed`
  - `14 passed`
  - `13 passed`
- Root lint chain:
  - `./scripts/ci/lint_dispatch.sh`
  - `./scripts/ci/lint_httpx.sh`
  - `python3 scripts/ci/check_no_internal_async.py`
  - `./scripts/ci/lint_lifecycle.sh`
  - `./scripts/ci/lint_subagent_status.sh`
  - `./scripts/ci/lint_scope_phase.sh`
  - `./scripts/ci/lint_legacy_message_columns.sh`
  - `./scripts/ci/lint_chat_messages_read.sh`
  - `./scripts/ci/lint_wake_continuity_contract.sh`
  - `./scripts/ci/lint_cortex_boundary.sh`
  - `./scripts/ci/lint_retired_service_residue.sh`
  - `./scripts/ci/lint_frontend_phantom_tools.sh`
  - `./scripts/ci/lint_agent_loop_path.sh`
  - `./scripts/ci/lint_entangled_schema_ssot.sh`
  - `./scripts/ci/lint_current_docs_residue.sh`
  - `python3 scripts/ci/lint_roadmap_ticket_archaeology.py`
  - `python3 scripts/ci/lint_docs_status_consistency.py`
  - `python3 scripts/ci/lint_deploy_fresh_smoke.py`
  - `python3 scripts/ci/lint_runtime_worker_supervision.py`
  - `python3 scripts/ci/check_start_config_contract.py`
  - `./scripts/ci/lint_agent_main_path_acceptance.sh`
  - `./scripts/ci/lint_retired_agent_paths.sh`
  - `./scripts/ci/lint_lifecycle_loop_ownership.sh`
- Compile:
  - `python3 -m compileall -q novaic-cortex/novaic_cortex`
  - `python3 -m compileall -q scripts/ci`
  - `python3 -m compileall -q queue_service task_queue tests` in `novaic-agent-runtime`
- Diff hygiene:
  - `git diff --check`
  - `git -C novaic-agent-runtime diff --check`
  - `git -C novaic-cortex diff --check`
- Residue scans:
  - `rg -n "GenericWorker\\(|ConcurrentGenericWorker\\(|SyntheticJobSource\\(|WorkerRuntimeConfig\\(|ShutdownController\\(|WorkerRuntime\\(|NoopReporter\\(|ResultLoggingReporter\\(" novaic-agent-runtime/task_queue/workers/worker_assemblies.py` returned no matches.
  - `rg -n "httpx\\.(Async)?Client\\(" novaic-agent-runtime novaic-cortex -g '*.py'` returned no matches.

## Known Gaps

- No remote deployment was run during this ticket.
- LLM Factory and Business provider direct HTTP clients remain on the pre-existing lint allowlist because they are outside the Runtime FSM/business-DSL gap being closed here.

## Artifacts

- `novaic-agent-runtime/task_queue/handlers/tool_handlers.py`
- `novaic-agent-runtime/tests/unit/task_queue/test_tool_handlers_display_chat_history.py`
- `novaic-cortex/novaic_cortex/blob_payload.py`
- `novaic-cortex/novaic_cortex/blob_store.py`
- `scripts/ci/lint_httpx.sh`
- `scripts/ci/lint_lifecycle_loop_ownership.sh`
