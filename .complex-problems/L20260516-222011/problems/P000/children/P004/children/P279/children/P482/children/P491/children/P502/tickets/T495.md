# Recovery stack diagnostics hardening ticket

## Problem Definition

Suspected-dead recovery currently risks losing stack diagnostics: `_record_session_suspected_dead_event()` does not preserve `remaining_stack`, and `build_recovery_archive_effect()` can synthesize a known empty stack from missing legacy fields. This hides corruption by making an unknown failed wake look cleanly archived.

## Proposed Solution

Make recovery stack diagnostics explicit. Suspected-dead events should preserve `remaining_stack` from saga context when present, otherwise store an explicit unknown stack snapshot. Recovery archive shaping should preserve valid `remaining_stack`, reject malformed explicit `remaining_stack`, and use unknown stack only when diagnostics are absent. Remove reliance on `stack_known_at_finalize` / `stack_depth_at_finalize` compatibility fields.

## Acceptance Criteria

- Suspected-dead event payloads include explicit `remaining_stack`.
- Missing stack diagnostics become `{"known": false, "depth": 0, "frames": []}` instead of a known empty stack.
- Malformed explicit `remaining_stack` is rejected by recovery archive shaping.
- Focused recovery/session tests cover preserved and unknown stack cases.

## Verification Plan

Run focused recovery/finalize tests:

- `tests/test_pr245_suspected_dead_recovery.py`
- `tests/test_pr247_recovery_outbox_cutover.py`
- `tests/test_pr254_finalize_ownership.py`
- `tests/test_pr255_legacy_compat_cleanup.py`
- `tests/test_pr266_session_recovery_boundary.py`

Also run `rg` guards for `stack_known_at_finalize`, `stack_depth_at_finalize`, and recovery `remaining_stack` behavior.

## Risks

- Existing tests currently expect known-empty fallback and must be updated to explicit unknown-stack semantics.
- Some old compatibility strings may remain only in ledger artifacts; production/runtime code should not rely on them.

## Assumptions

- A wake finalize failure without stack diagnostics is genuinely unknown, not known empty.
