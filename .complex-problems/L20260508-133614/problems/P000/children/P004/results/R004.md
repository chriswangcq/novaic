## T005 Result: 旧词汇、退休注释、transitional allowlist 清理

### Done

- Renamed active-session diagnostic API internals from `list_active_sessions` to `list_active_session_states`.
- Renamed saga startup projector from `rebuild_active_sessions_from_sagas` to `rebuild_session_state_from_running_sagas`.
- Rewrote retired continuity comments and tests so active code no longer carries prompt-splice vocabulary.
- Removed the `TRANSITIONAL` label from `scripts/ci/lint_httpx.sh`; remaining allowlist entries now name their owning integration boundaries.
- Added `scripts/ci/lint_retired_runtime_vocabulary.py` to reject retired runtime vocabulary in active runtime/business/script paths.

### Verification

- `python3 scripts/ci/lint_retired_runtime_vocabulary.py`
- `bash scripts/ci/lint_httpx.sh`
- `python3 -m py_compile queue_service/session_repo.py queue_service/session_rebuild.py queue_service/routes.py task_queue/handlers/runtime_handlers.py`
- `python3 -m py_compile tests/test_pr57_prev_scope_history_inject.py tests/test_pr153_pending_inbox_metadata.py tests/test_pr242_strict_input_ledger.py tests/test_pr243_inbox_restart_cutover.py tests/test_pr252_session_state_ssot.py tests/test_pr257_remove_active_sessions_table.py tests/test_pr279_session_rebuild_projector_boundary.py tests/test_pr315_queue_fsm_final_residue_guard.py`
- `pytest -q tests/test_pr153_pending_inbox_metadata.py tests/test_pr242_strict_input_ledger.py tests/test_pr243_inbox_restart_cutover.py tests/test_pr252_session_state_ssot.py tests/test_pr257_remove_active_sessions_table.py tests/test_pr279_session_rebuild_projector_boundary.py tests/test_pr315_queue_fsm_final_residue_guard.py tests/test_pr57_prev_scope_history_inject.py`
- `pytest -q tests/test_im_aggregation.py`

### Artifacts

- `novaic-agent-runtime/queue_service/session_repo.py`
- `novaic-agent-runtime/queue_service/session_rebuild.py`
- `novaic-agent-runtime/queue_service/routes.py`
- `novaic-agent-runtime/task_queue/handlers/runtime_handlers.py`
- `novaic-agent-runtime/tests/test_pr57_prev_scope_history_inject.py`
- `novaic-agent-runtime/tests/test_pr153_pending_inbox_metadata.py`
- `novaic-agent-runtime/tests/test_pr242_strict_input_ledger.py`
- `novaic-agent-runtime/tests/test_pr243_inbox_restart_cutover.py`
- `novaic-agent-runtime/tests/test_pr252_session_state_ssot.py`
- `novaic-agent-runtime/tests/test_pr257_remove_active_sessions_table.py`
- `novaic-agent-runtime/tests/test_pr279_session_rebuild_projector_boundary.py`
- `novaic-business/tests/test_im_aggregation.py`
- `scripts/ci/lint_httpx.sh`
- `scripts/ci/lint_retired_runtime_vocabulary.py`

### Gaps

- None for this ticket. P005 will wire the new guard into the broader CI matrix.
