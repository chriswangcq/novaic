# P397 generic FSM generation counter classification check

## Summary

Success for the scoped classification. The inspected task/saga/lease generation hits are generic FSM machine-version counters, not Queue session-generation authority paths.

## Evidence

- Reducer increments (`int(state.generation) + 1`) occur inside task/saga/lease pure FSM reducers as internal state-version updates.
- DTO conversions (`int(decision.next_state.generation)`, `int(decision.generation)`) map generic FSM decisions into persistence calls.
- Repository adapters reconstruct task/saga/lease runtime state from their own FSM ledgers, not from wake/session user input.

## Criteria Map

- Generic hits classified with file evidence: satisfied by R378.
- No hidden session-generation authority bug found in generic counters: satisfied by inspection.
- Focused tests only required if code changed: no code changed in this ticket.

## Execution Map

- R378 records the targeted guard and inspected representative code.

## Stress Test

- Classification intentionally separated generic machine-version counters from session-generation authority to avoid both over-patching and hidden session risk.

## Residual Risk

- Source-level broad guards will still see these generic counters. This is accepted as classified safe, not a live session-generation defect.

## Result IDs

- R378
