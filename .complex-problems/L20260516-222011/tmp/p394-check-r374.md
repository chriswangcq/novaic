# P394 session repo state reconstruction validation check

## Summary

Success. Session repo reconstruction now validates generation explicitly according to session status, and focused tests cover active/no-active edge cases.

## Evidence

- `_decide_live_dispatch` and `_runtime_state_from_session_state` now use `_runtime_generation_for_status`.
- Active state rejects bool and generation `0`.
- No-active state permits generation `0` but rejects bool.
- Focused runtime tests passed: 32 tests.

## Criteria Map

- Runtime reconstruction validates active-like generation explicitly: satisfied.
- No-active generation `0` still works: satisfied.
- Guard no longer reports old repo reconstruction defaults: satisfied.

## Execution Map

- R374 records code patch, tests, compile check, and source guard.

## Stress Test

- Tests cover both active and no-active paths, including Python bool coercion traps.

## Residual Risk

- Session ledger generation helpers remain for P395.

## Result IDs

- R374
