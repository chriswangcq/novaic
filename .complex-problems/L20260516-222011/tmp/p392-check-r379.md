# P392 audit and generic FSM generation classification check

## Summary

Success. Audit/projection generation handling is explicit, and generic task/saga/lease generation hits are classified as non-session FSM counters.

## Evidence

- R377 patched audit parsing and passed tests.
- R378 classified generic FSM counters with file evidence.

## Criteria Map

- Audit/projection hits classified or patched: satisfied.
- Generic FSM hits classified separately from session generation authority: satisfied.
- Focused tests pass for changed modules: satisfied for audit changes.

## Execution Map

- Split children P396 and P397 both checked success before this parent result.

## Stress Test

- Classification avoids the broad-guard trap of treating every `generation` word as Queue session generation.

## Residual Risk

- Round/stack-depth defaults remain in P393.

## Result IDs

- R379
