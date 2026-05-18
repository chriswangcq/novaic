# P503 recovery/session-ended final guard classification

## Raw Evidence

- Test log: `.complex-problems/L20260516-222011/tmp/p503/recovery-session-final-tests.log`
- Raw guard output: `.complex-problems/L20260516-222011/tmp/p503/recovery-session-final-guards-raw.txt`

## Legacy Stack Fallback Fields

The `legacy stack fallback fields` section is empty.

No guarded runtime/test scope hits remain for:

- `stack_known_at_finalize`
- `stack_depth_at_finalize`

## Production Strict / Explicit Paths

- `task_queue/handlers/session_handlers.py`
  - Requires `finalize_reason`, positive `generation`, and object `remaining_stack` for `SESSION_ENDED`.
- `task_queue/sagas/wake_finalize.py`
  - Requires explicit `remaining_stack` and raises when missing.
- `queue_service/session_repo.py`
  - `session_ended()` requires `finalize_reason`, positive generation, and non-`None` `remaining_stack`.
  - Recovery dispatch builds archive effect through `build_recovery_archive_effect()`.
- `queue_service/saga_repo.py`
  - Suspected-dead events include `_explicit_or_unknown_remaining_stack()` so diagnostics are preserved or explicitly unknown.
- `queue_service/session_recovery.py`
  - `build_recovery_archive_effect()` preserves explicit `remaining_stack`.
  - Missing stack diagnostics become `_unknown_remaining_stack()` with `known: false`.
  - Malformed explicit `remaining_stack` raises `ValueError`.
- `queue_service/session_outbox.py`
  - Recovery archive publisher rejects non-dict `remaining_stack` before publishing `CORTEX_SCOPE_END`.
- `task_queue/handlers/cortex_handlers.py`
  - Cortex scope-end handler requires `remaining_stack` in archive payload.

## Guarded Test Fixtures

- `tests/test_pr245_suspected_dead_recovery.py`
  - Covers suspected-dead event recording, explicit stack preservation, unknown-stack recovery archive, and no direct session mutation from failed finalize branch.
- `tests/test_pr247_recovery_outbox_cutover.py`
  - Covers recovery archive outbox publish/retry and required archive publisher payload fields.
- `tests/test_pr254_finalize_ownership.py`
  - Covers explicit finalize/session-ended contract, stale finalize rejection, handler forwarding, route/client validation.
- `tests/test_pr255_legacy_compat_cleanup.py`
  - Guards required finalize contract strings.
- `tests/test_pr266_session_recovery_boundary.py`
  - Covers recovery marker/archive helper shape, unknown-stack default, explicit stack preservation, and malformed stack rejection.

## Conclusion

No unclassified recovery/session-ended compatibility fallback remains in the checked active paths. Remaining hits are strict production contracts, explicit unknown-stack handling, archive publication guards, or intentional test assertions.
