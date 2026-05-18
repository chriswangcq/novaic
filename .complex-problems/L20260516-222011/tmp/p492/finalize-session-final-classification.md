# P492 finalize/session final guard classification

## Raw Evidence

- Test log: `.complex-problems/L20260516-222011/tmp/p492/finalize-session-final-tests.log`
- Raw guard output: `.complex-problems/L20260516-222011/tmp/p492/finalize-session-final-guards-raw.txt`
- Initial inventory: `.complex-problems/L20260516-222011/tmp/p488/finalize-session-residue-classification.md`

## Initial Inventory Candidate Closure

- `wake_finalize.py` stack fabrication: closed by P489. Wake finalize now requires explicit `remaining_stack`.
- Attach no-generation ambiguity: closed by P490. Attach effect builder, outbox, and runtime handler are generation-checked.
- Suspected-dead recovery stack diagnostics gap: closed by P491. Suspected-dead events preserve explicit/unknown `remaining_stack`, and legacy `stack_*_at_finalize` fields are gone from guarded runtime/test scope.

## Forbidden Compatibility Hits

The final forbidden sweep contains only test guard assertions:

- `tests/test_pr273_session_harness_final_residue_guard.py` asserts `tq_active_sessions` is absent.
- `tests/test_pr255_legacy_compat_cleanup.py` asserts `tq_active_sessions` is absent.
- `tests/test_pr315_queue_fsm_final_residue_guard.py` lists `tq_active_sessions` as a forbidden string.
- `tests/test_pr257_remove_active_sessions_table.py` asserts the table/source string is absent.
- `tests/test_pr245_suspected_dead_recovery.py` asserts old recovery table queries/inserts are absent.
- `tests/test_pr247_recovery_outbox_cutover.py` asserts direct `queue_recovery_scope_end_task` was removed.

No production source hit appears in the forbidden section.

## Production Strict Paths

- `task_queue/sagas/wake_finalize.py`
  - Requires positive generation and explicit `remaining_stack`.
- `task_queue/handlers/session_handlers.py`
  - Requires finalize reason, generation, and object `remaining_stack`.
- `task_queue/handlers/runtime_handlers.py`
  - Requires expected wake scope and expected session generation before attaching input.
- `task_queue/handlers/cortex_handlers.py`
  - Requires archive `remaining_stack` for scope-end.
- `queue_service/session_repo.py`
  - Uses FSM decisions for finalize rejection/finalization, attach race buffering, and suspected-dead recovery.
- `queue_service/session_outbox.py`
  - Validates recovery archive stack and attach expected generation before publishing.
- `queue_service/session_recovery.py`
  - Converts absent recovery stack diagnostics to explicit unknown stack, preserves explicit stack, and rejects malformed explicit stack.
- `queue_service/saga_repo.py`
  - Produces explicit `remaining_stack` for compensation and suspected-dead events.

## Guarded Test Fixtures

The remaining test hits intentionally cover:

- explicit finalize/session-ended contracts
- stale finalize rejection
- attach generation validation
- attach-race buffering
- suspected-dead recovery and pending inbox preservation
- recovery archive retry behavior
- recovery stack preservation/unknown semantics
- absence of old active-session and recovery table paths

## Conclusion

No unclassified production finalize/session compatibility residue remains in the checked scope. Remaining hits are strict production contracts, explicit recovery semantics, or guard tests.
