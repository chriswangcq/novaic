# P488 finalize/session residue classification

## Raw Evidence

- Raw guard output: `.complex-problems/L20260516-222011/tmp/p488/finalize-session-residue-raw-guards.txt` (`2549` lines)
- Production-focused output: `.complex-problems/L20260516-222011/tmp/p488/production-focused-hits.txt` (`203` lines)
- File list: `.complex-problems/L20260516-222011/tmp/p488/finalize-session-residue-files.txt`

## Active FSM Behavior

- `novaic-agent-runtime/queue_service/session_fsm.py:313-399`
  - `missing_generation`, `generation_mismatch`, and `scope_mismatch` are strict rejection outcomes in the pure finalize reducer. They are not fallback behavior; they preserve active state when a stale finalize arrives.
- `novaic-agent-runtime/queue_service/session_repo.py:142-326`
  - Occupied-state buffering and suspected-dead observation are explicit session FSM/ledger transitions. They do not directly create a new wake from a healthy active session.
- `novaic-agent-runtime/queue_service/session_repo.py:502-638`
  - `session_ended()` requires `finalize_reason`, `generation`, and `remaining_stack`, then records `session_finalized` before closing or restarting from pending inbox.
- `novaic-agent-runtime/queue_service/session_repo.py:862-979`
  - `active_session_changed_before_attach` is an attach-race guard that buffers the input instead of delivering it to a stale wake.
- `novaic-agent-runtime/queue_service/session_ledger.py:340-378`
  - Finalize rejection idempotency is explicit ledger behavior, not old session cleanup.

## Adapter Boundaries

- `novaic-agent-runtime/task_queue/handlers/session_handlers.py:31-88`
  - `session.ended` validates the explicit finalize contract and forwards it to `SessionRepository`.
- `novaic-agent-runtime/queue_service/routes.py:549-592`
  - Public `SessionEndedRequest` requires `generation` and `remaining_stack`.
- `novaic-agent-runtime/task_queue/client.py:484-499`
  - Worker-side client forwards the finalize contract to Queue Service.
- `novaic-agent-runtime/queue_service/session_outbox.py:198-224`
  - Recovery archive side effect is an outbox adapter boundary.

## Guard/Test Fixtures

- `novaic-agent-runtime/tests/test_pr254_finalize_ownership.py`
  - Guards explicit finalize contract and stale-generation/scope-mismatch rejection.
- `novaic-agent-runtime/tests/test_pr255_legacy_compat_cleanup.py`
  - Guards retired dispatch route, old active sessions table, generation-checked attach, and required finalize contract.
- `novaic-agent-runtime/tests/test_pr238_generation_checked_attach.py`
  - Guards expected wake scope and expected generation on active input attach.

## Cleanup Candidates for Child Problems

- `novaic-agent-runtime/task_queue/sagas/wake_finalize.py:97-112`
  - `_remaining_stack_snapshot()` still synthesizes an empty stack when `remaining_stack` is absent, using `stack_known_at_finalize` and `stack_depth_at_finalize`. This looks like a compatibility fallback. P489 should decide whether wake finalize must require explicit `remaining_stack` instead of fabricating one.
- `novaic-agent-runtime/queue_service/saga_repo.py:1340-1364`
  - `_record_session_suspected_dead_event()` receives `saga_context` but only copies selected fields into the suspected-dead payload. It does not copy `remaining_stack`, `stack_known_at_finalize`, or `stack_depth_at_finalize`, while `session_recovery.build_recovery_archive_effect()` later tries to read those fields. P491 should preserve or require stack diagnostics in recovery.
- `novaic-agent-runtime/queue_service/session_recovery.py:154-163`
  - `build_recovery_archive_effect()` falls back to an empty stack when recovery metadata lacks `remaining_stack`. This may be acceptable as a defensive guard, but paired with the `saga_repo.py` omission it can hide lost finalize diagnostics. P491 should tighten after the upstream payload is fixed.
- `novaic-agent-runtime/task_queue/__init__.py:29-41`
  - `try/except ImportError` assigns queue-service exports to `None`. This is broader module compatibility residue, not directly finalize/session. It is out of P482 scope but should be considered in a later general residue cleanup pass.

## No Actionable Residue Found Here

- No direct `SagaOrchestrator.create()` session-owned wake creation path was found in finalize/session code.
- No `tq_active_sessions` runtime reference was found in runtime sources; existing guard test covers this.
- No no-generation active attach production path was found; attach delivery uses `expected_session_generation`.
