# Finalize producer stack contract audit result

## Summary

Completed the read-only producer audit. The natural React finalize producer already provides explicit `remaining_stack`, but saga compensation can create `wake_finalize` without one when the failed wake saga context lacks stack diagnostics. That means P494 must fix the compensation producer and then make `wake_finalize.py` strict.

## Done

- Saved raw producer search output and file list.
- Classified production producers, adapter boundaries, recovery archive producer, and test fixtures.
- Identified one concrete missing provider: `SagaRepository._build_wake_finalize_compensation_effect()`.
- Made no source changes.

## Verification

- Raw search artifact exists at `.complex-problems/L20260516-222011/tmp/p493/wake-finalize-producer-raw.txt` with `258` lines.
- Classification artifact exists at `.complex-problems/L20260516-222011/tmp/p493/wake-finalize-producer-classification.md`.
- Inspected `react_actions.py`, `saga_repo.py`, `session_outbox.py`, and `session_recovery.py` producer paths.

## Known Gaps

- P494 must implement strict finalizer behavior and fix compensation context.
- P491 still owns recovery archive fallback tightening.

## Artifacts

- `.complex-problems/L20260516-222011/tmp/p493/wake-finalize-producer-raw.txt`
- `.complex-problems/L20260516-222011/tmp/p493/wake-finalize-producer-files.txt`
- `.complex-problems/L20260516-222011/tmp/p493/wake-finalize-producer-classification.md`
