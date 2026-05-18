# Audit and generic FSM generation classification result

## Summary

Closed the audit/generic FSM generation classification by splitting audit/projection hardening from generic FSM counter classification.

## Done

- P396/R377 tightened session and queue audit generation parsing and added focused bool-rejection tests.
- P397/R378 classified task/saga/lease generic FSM generation hits as non-session machine-version counters.

## Verification

- P396 passed compile and 8 focused audit tests.
- P397 inspected targeted guard hits and representative generic FSM/repository code; no code changes were needed.

## Known Gaps

- Round/stack-depth defaults remain in sibling P393.
- Generic FSM counter hits remain visible to broad text guards but are classified safe relative to session-generation authority.

## Artifacts

- Child results: R377, R378.
