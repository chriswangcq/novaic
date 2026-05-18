# Attach generation contract hardening check

## Summary

Success for P497. The hardening work removed the weak optional builder boundary, added focused tests, preserved attach-race behavior through focused verification, and left no P497-scoped no-generation attach path unresolved.

## Evidence

- R486 summarizes closed child results R484 and R485.
- C513 verified the builder-boundary implementation.
- C514 verified attach/session focused tests and guard output.
- P500 test artifact shows `33 passed in 0.15s`.
- P500 guard artifact shows no forbidden optional builder generation contract hits.

## Criteria Map

- Missing no-generation/stale-generation behavior is removed or converted to strict validation/buffering: satisfied by builder validation and existing runtime/outbox generation checks.
- Focused tests cover the hardened boundary: satisfied by new builder tests plus the 33-test focused suite.
- Existing attach-race buffering behavior remains intact: satisfied by passing `test_pr248_attach_outbox_cutover.py` in P500.

## Execution Map

- T489 was split into P499 and P500.
- P499 implemented the boundary hardening.
- P500 independently verified tests, guards, and diff evidence.
- R486 records the completed parent result after both children closed successfully.

## Stress Test

- Plausible failure mode: code compiles but still allows an attach effect to be built with missing generation.
- The guard and new tests cover this directly: `None`, bool, zero, and invalid text are rejected before effect construction.

## Residual Risk

- P498 still needs final P490-level verification that attach generation hardening fits the broader compatibility cleanup branch.
- No P497-specific blocker remains.

## Result IDs

- R486
