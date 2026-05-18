# P390 session FSM finalize generation validation check

## Summary

Success. The pure session FSM finalize reducer now has explicit generation validation and focused tests for malformed direct inputs.

## Evidence

- `_reduce_session_finalize` no longer uses raw `int(... or 0)` for `finalize_generation` or `state.generation`.
- Bool finalize generation is rejected as `missing_generation`, not accepted as generation `1`.
- Bool state generation raises a clear `ValueError`.
- Focused runtime tests passed: 21 tests.

## Criteria Map

- Explicit positive/non-negative validation in finalize path: satisfied.
- Tests reject malformed finalize generation and preserve valid behavior: satisfied.
- Widened session FSM finalize guard clean: satisfied by focused `rg` returning no matches.

## Execution Map

- R373 records code changes, focused tests, compile check, and focused guard.

## Stress Test

- The test covers Python's `bool` subclass-of-`int` trap for both event and state generation.

## Residual Risk

- Session repo/ledger adapter defaults and audit/generic FSM classifications remain in sibling problems, outside this pure FSM finalize boundary.

## Result IDs

- R373
