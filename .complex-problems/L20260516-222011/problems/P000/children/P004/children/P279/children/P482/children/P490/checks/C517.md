# Attach generation compatibility cleanup check

## Summary

Success for P490. The branch inspected attach/generation production paths, hardened the missing-generation builder boundary, preserved deterministic stale-generation buffering/validation, removed the optional builder compatibility contract, and passed focused attach/generation tests.

## Evidence

- R488 summarizes closed child results R483, R486, and R487.
- C512 verified attach generation inventory.
- C515 verified attach generation hardening.
- C516 verified final attach generation tests/guards/classification.
- Final focused suite passed with `33 passed`.
- Final classification found no unguarded no-generation `SESSION_ATTACH_INPUT` path.

## Criteria Map

- Attach/generation production paths are inspected against the P482 inventory: satisfied by P496 inventory and P498 final classification.
- Missing-generation and stale-generation handling is explicit and deterministic: satisfied by builder/outbox/runtime strict generation validation and session repo attach-race buffering.
- High-confidence legacy no-generation compatibility paths are removed or converted to strict guard behavior: satisfied by removing the optional builder contract and keeping runtime/outbox required-field guards.
- Focused attach/generation tests pass: satisfied by the P498 focused suite.

## Execution Map

- T487 was split into P496, P497, and P498.
- P496 inspected and classified paths.
- P497 hardened the builder boundary through P499/P500.
- P498 performed final verification and classification.
- R488 records the parent result after all children closed successfully.

## Stress Test

- Plausible failure mode: a new IM attaches to an old wake because missing generation is accepted somewhere in the attach path.
- The branch now blocks this at multiple points: builder validation, outbox validation, runtime validation, and repo attach-race buffering.

## Residual Risk

- None for attach generation compatibility cleanup. P491/P492 remain for recovery/session-ended and final P482-level verification.

## Result IDs

- R488
