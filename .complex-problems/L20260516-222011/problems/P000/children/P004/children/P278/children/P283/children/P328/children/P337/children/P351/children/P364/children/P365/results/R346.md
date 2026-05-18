# T353 Result: Remove Startup Rebuild Generation Default

## Changes

- Updated `novaic-agent-runtime/queue_service/session_rebuild.py`.
  - Added explicit positive `session_generation` parsing.
  - Skips running saga contexts that lack positive generation.
  - Removed the old `generation=int(context.get("session_generation") or 1)` fallback.
- Updated `novaic-agent-runtime/tests/test_pr279_session_rebuild_projector_boundary.py`.
  - Added DB-backed projector tests for missing, invalid, and valid generation contexts.
  - Verified missing/invalid contexts are skipped.
  - Verified valid integer and numeric-string generations are projected exactly.
- Updated stale attach-flow residue guard tests:
  - `tests/test_pr273_session_harness_final_residue_guard.py`
  - `tests/test_pr271_session_attach_flow_consolidation.py`
  - These now assert the old `_publish_attach_request_after_transaction` path is gone and the current `_record_attach_request_after_transaction` path is the single owner.

## Verification

Compile:

```bash
python3 -m py_compile \
  queue_service/session_rebuild.py \
  tests/test_pr279_session_rebuild_projector_boundary.py \
  tests/test_pr271_session_attach_flow_consolidation.py \
  tests/test_pr273_session_harness_final_residue_guard.py
```

Focused tests:

```bash
PYTHONPATH=.:../novaic-common pytest -q \
  tests/test_pr271_session_attach_flow_consolidation.py \
  tests/test_pr279_session_rebuild_projector_boundary.py \
  tests/test_pr318_projection_table_quarantine_guard.py \
  tests/test_pr272_session_active_state_ledger_boundary.py \
  tests/test_pr273_session_harness_final_residue_guard.py
```

Result: `23 passed in 0.23s`.

Aggregate recovery/finalize/rebuild tests:

```bash
PYTHONPATH=.:../novaic-common pytest -q \
  tests/test_pr311_saga_compensation_outbox_cutover.py \
  tests/test_pr266_session_recovery_boundary.py \
  tests/test_pr247_recovery_outbox_cutover.py \
  tests/test_pr245_suspected_dead_recovery.py \
  tests/test_pr233_active_inbox_dispatch.py \
  tests/test_pr254_finalize_ownership.py \
  tests/test_pr43_last_scope_wiring.py \
  tests/test_runtime_tool_path_contract.py \
  tests/test_scope_end_environment_notifications.py \
  tests/test_pr271_session_attach_flow_consolidation.py \
  tests/test_pr279_session_rebuild_projector_boundary.py \
  tests/test_pr318_projection_table_quarantine_guard.py \
  tests/test_pr272_session_active_state_ledger_boundary.py \
  tests/test_pr273_session_harness_final_residue_guard.py
```

Result: `96 passed in 0.71s`.

Residue search:

```bash
rg -n 'session_generation"\) or 1|session_generation.*or 1|_publish_attach_request_after_transaction' queue_service tests || true
```

Only negative assertions remain for `_publish_attach_request_after_transaction`; no production fallback remains.

## Gap

No gap found in the scoped startup rebuild generation default fix.
