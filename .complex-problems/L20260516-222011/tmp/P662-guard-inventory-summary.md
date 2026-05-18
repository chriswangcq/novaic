# P662 Architecture Guard Inventory Summary

## CI workflow entrypoint

- `.github/workflows/lint.yml` runs the root guard suite on PR/push, including dispatch, httpx, lifecycle, subagent/scope, message lifecycle, wake continuity, Cortex boundary, Blob workspace boundary, retired-service residue, frontend phantom tools, docs residue/status, deploy fresh smoke, runtime worker supervision, retired runtime vocabulary, start/config, agent main paths, lifecycle loop ownership, and generated artifacts.

## Root CI/static guards

- `scripts/ci/lint_blob_workspace_boundary.py`: Blob is byte store; LogicalFS/workspace is live authority. Scans live runtime source roots and rejects direct Blob object authority or BlobRef/API references outside allowed boundary files.
- `scripts/ci/lint_cortex_boundary.sh` -> `novaic-cortex/scripts/check_cortex_boundary.py`: keeps Cortex focused on scope lifecycle/context assembly and rejects boundary drift.
- `scripts/ci/lint_generated_artifacts.sh`: rejects `__pycache__`, `.pytest_cache`, egg-info, and `.pyc` artifacts in active source/resource trees.
- `scripts/ci/lint_lifecycle_loop_ownership.sh`: enforces Queue/Runtime ownership of notification lifecycle and rejects retired subscriber-owned message lifecycle paths.
- `scripts/ci/lint_wake_continuity_contract.sh`: rejects retired implicit-continuity field vocabulary in active source.
- `scripts/ci/lint_deploy_fresh_smoke.py`: enforces timestamp-aware deploy fresh smoke and retired backend package removal.
- `scripts/ci/lint_retired_runtime_vocabulary.py`: rejects retired runtime terms (`list_active_sessions`, `rebuild_active_sessions_from_sagas`, prompt splice, `TRANSITIONAL`) in active Queue/Runtime/Business/CI paths.
- `scripts/ci/test_no_legacy_file_hot_paths.py`: pytest-style active runtime source guard against retired file-service/storage paths.
- Existing adjacent guards also cover dispatch, service residue, docs residue/status, roadmap archaeology, frontend phantom tools, worker supervision, start/config, agent path acceptance, and entangled schema artifacts.

## Module-level guard clusters

- `novaic-cortex/tests/test_blob_boundary_guard.py` + `novaic-cortex/cortex_tests/blob_boundary_policy.py`: module-level counterpart to root Blob/LogicalFS boundary policy.
- `novaic-cortex/tests/test_shell_capabilities_blob_contract.py`, `test_tool_output_projection.py`, `test_step_result_projection.py`: shell/display/artifact projection boundaries and no raw base64 in shell output.
- `novaic-cortex/tests/test_context_event_*`, `test_context_event_no_compat.py`, `test_context_event_read_source_guards.py`: event-stream context source and no legacy DFS fallback.
- `novaic-cortex/tests/test_sandbox_requires_mount_namespace.py`, `test_pr75_proxy_boundary.py`: no local backing path reuse or implicit localhost fallback.
- `novaic-agent-runtime/tests/test_pr25x..test_pr33x*`, `test_pr315_queue_fsm_final_residue_guard.py`, `test_pr323_generic_worker_contracts.py`, `test_pr335_worker_residue_guards.py`: session FSM, outbox, generic worker, and old SQL/projection residue guards.
- `novaic-agent-runtime/tests/unit/task_queue/test_no_historical_tool_image_injection.py`, `test_shell_output_contract.py`, `test_tool_output_contract.py`, `test_tool_handlers_display_chat_history.py`: LLM/tool context projection and shell/display output contract guards.
- `novaic-common/tests/test_tool_definitions_contract.py`, `test_cortex_observation_contract.py`, `test_resource_ref_contract.py`: shared tool/observation/resource-ref contracts.
- `novaic-business/tests/test_pr153_lifecycle_guardrails.py`, `test_pr141_compat_cleanup.py`, `test_pr151_device_binding_contract.py`, `test_pr152_file_metadata_boundary.py`: business boundary and compatibility cleanup guards.
- `novaic-logicalfs/tests/test_logicalfs.py`, `test_authority.py`, `test_blob_store.py`: lower-layer LogicalFS and BlobObjectStore behavior, not Cortex live-contract policy.
- `novaic-sandbox-service/tests/test_sandbox_boundary.py`: sandbox service must not import Cortex/Blob/LogicalFS or own workspace identity semantics.

## Evidence files

- Raw file inventory: `.complex-problems/L20260516-222011/tmp/P662-guard-files-inventory.txt`
- Keyword scan: `.complex-problems/L20260516-222011/tmp/P662-guard-keyword-scan.txt`
