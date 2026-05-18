# T352 Result: Recovery Compensation Finalize Aggregate Verification

## Execution

Ran compile verification from `novaic-agent-runtime`:

```bash
python3 -m py_compile \
  queue_service/saga_repo.py \
  queue_service/session_recovery.py \
  queue_service/session_outbox.py \
  queue_service/session_repo.py \
  queue_service/session_wake_plan.py \
  task_queue/sagas/wake_finalize.py \
  task_queue/handlers/cortex_handlers.py \
  task_queue/handlers/session_handlers.py \
  tests/test_pr311_saga_compensation_outbox_cutover.py \
  tests/test_pr266_session_recovery_boundary.py \
  tests/test_pr247_recovery_outbox_cutover.py
```

Ran focused aggregate tests:

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
  tests/test_scope_end_environment_notifications.py
```

Result: `73 passed in 0.53s`.

## Positive Evidence

- Wake saga failure compensation now requires a positive explicit `session_generation` before creating a `wake_finalize` compensation saga.
- Recovery archive shaping now propagates positive generation from `SESSION_SUSPECTED_DEAD` event to `CORTEX_SCOPE_END`.
- Recovery archive publisher rejects missing, non-numeric, boolean, zero, and negative generation values before publishing scope-end work.
- Focused tests cover the targeted compensation and recovery paths.

## Residue Search

Searches were run for:

- `wake_finalize`, `create_wake_finalize_saga`, `RECOVERY_ARCHIVE_SCOPE`, `CORTEX_SCOPE_END`, `session_generation`, `finalize_generation`
- `session_generation.*or 0`, `generation.*or 0`, `finalize_generation.*or 0`
- positive generation helper and rejection text

Most `generation or 0` hits were runtime state reads or FSM no-active sentinel conversions. However, one related startup projector residue was found:

```text
queue_service/session_rebuild.py:35:
generation=int(context.get("session_generation") or 1)
```

This default can reconstruct an active session with generation `1` even if the running saga context is missing explicit `session_generation`. That is not a direct recovery archive publish path, but it violates the same identity principle: missing identity should not be silently normalized into a valid generation.

## Gap

Aggregate verification is not fully clean. `session_rebuild.py` still has a compatibility/default-generation path that can mask missing session identity during startup rebuild.

## Recommendation

Open a follow-up child problem under P364 to remove the startup rebuild generation default, require positive explicit `session_generation`, and add focused tests proving invalid/missing generation contexts are skipped rather than reconstructed as active sessions.
