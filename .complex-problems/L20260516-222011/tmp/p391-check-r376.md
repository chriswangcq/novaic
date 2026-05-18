# P391 session repo and ledger generation adapters check

## Summary

Success. The repo reconstruction and ledger helper generation boundaries are now explicit and tested.

## Evidence

- R374: session repo reconstruction validates generation by runtime status.
- R375: session ledger generation helpers validate current state generation.
- Both child problems passed focused tests and targeted guards.

## Criteria Map

- Runtime state reconstruction rejects malformed active/session state generation where it affects authority decisions: satisfied.
- Ledger helpers validate DB generation or classify it with tests: satisfied via direct malformed-state test.
- Focused session repo/ledger tests pass: satisfied.
- Guard matrix classifies/removes repo/ledger generation hits: satisfied for targeted repo/ledger hits.

## Execution Map

- P394 and P395 were split children, both checked success before this parent result.

## Stress Test

- Tests cover bool active-state generation, no-active bool generation, and monkeypatched bool ledger generation.

## Residual Risk

- Audit/generic FSM and round/stack-depth classifications remain outside this problem.

## Result IDs

- R376
