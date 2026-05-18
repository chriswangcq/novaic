# Finalize saga and session handler residue classification check

## Summary

`P413` is successful. The finalize saga/session handler pass proves session generation is explicit and positive, and finalize reason plus remaining stack are required before session-ended mutation.

## Evidence

- `R393` records the targeted guard and classification.
- Focused tests passed: `48 passed in 0.38s`.
- Guard output shows `wake_finalize` and `subagent_wake` use shared positive-generation contracts, and `session_handlers.py` rejects missing/invalid generation.

## Criteria Map

- Inspect finalize saga and session handler hits: satisfied.
- Confirm explicit positive session generation: satisfied.
- Confirm finalize reason and remaining stack are required: satisfied at `session_handlers.py`.
- Patch dangerous fallback: no dangerous fallback found.
- Run focused tests: satisfied.

## Execution Map

- `T400` executed as a three-file one-go classification.
- Initial subdirectory command had wrong ledger/guard paths; execution reran the guard from the repo root before recording `R393`.

## Stress Test

- The result relies on corrected root guard output plus focused tests, not on the initial empty guard caused by path mistakes.

## Residual Risk

- None for P413.

## Result IDs

- `R393`
