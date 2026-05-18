# Recovery stack diagnostics hardening check

## Summary

Success for P502. The implementation preserves explicit stack diagnostics, makes absent diagnostics explicitly unknown, rejects malformed explicit stack metadata, and removes legacy stack fallback fields from guarded runtime/test scope.

## Evidence

- R490 records implementation and verification artifacts.
- `saga_repo.py` now writes `remaining_stack` into suspected-dead event payloads through `_explicit_or_unknown_remaining_stack()`.
- `session_recovery.py` now preserves dict `remaining_stack`, rejects non-dict explicit `remaining_stack`, and uses `_unknown_remaining_stack()` for absent diagnostics.
- Test artifact shows `37 passed`.
- Guard artifact has an empty legacy `stack_known_at_finalize` / `stack_depth_at_finalize` section.

## Criteria Map

- Suspected-dead event payloads include explicit `remaining_stack`: satisfied by the `saga_repo.py` payload change and updated suspected-dead test assertion.
- Missing stack diagnostics become unknown stack instead of known empty: satisfied by updated recovery archive expectations in suspected-dead and recovery outbox tests.
- Malformed explicit `remaining_stack` is rejected: satisfied by the updated `test_build_recovery_archive_effect_rejects_bool_round_and_bad_remaining_stack`.
- Focused recovery/session tests cover preserved and unknown stack cases: satisfied by `test_build_recovery_archive_effect_preserves_explicit_remaining_stack` and updated flow tests.

## Execution Map

- T495 was a bounded one-go implementation ticket after P501 inventory.
- R490 records code changes, focused tests, guard output, and remaining P503 verification gap.

## Stress Test

- Plausible failure mode: a failed wake without stack diagnostics is archived as known empty, hiding corruption.
- The new path emits `{"known": false, "depth": 0, "frames": []}` for absent diagnostics, making the unknown state explicit.

## Residual Risk

- P503 must still run final recovery/session-ended branch verification.

## Result IDs

- R490
