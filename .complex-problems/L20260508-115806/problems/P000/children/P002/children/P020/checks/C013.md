# P020 Check - Assembly DSL Shrink Verification

## Summary

P020 is solved. The assembly shrink is not only implemented but verified: old lifecycle constructor residue is absent from `worker_assemblies.py`, tests now guard the helper-backed shape, and focused behavior/boundary checks pass.

## Evidence

- Residue search over `worker_assemblies.py` has no matches for direct worker lifecycle construction primitives.
- Focused test suite passes with 51 tests.
- Compile checks pass.
- Line count evidence is recorded.

## Criteria Map

- `worker_assemblies.py` has no direct worker lifecycle primitive construction -> satisfied.
- Helper-backed assembly tests pass -> satisfied.
- Outbox assembly tests pass -> satisfied.
- Effect boundary tests pass -> satisfied.
- Compile checks pass -> satisfied.
- Evidence recorded in ledger -> satisfied.

## Execution Map

- T015 -> R013: verification-only closure.

## Stress Test

- Reintroducing raw constructors into `worker_assemblies.py` would fail the residue command and updated tests.
- Breaking helper-backed construction would fail focused worker tests.

## Residual Risk

- none for P020.

## Result IDs

- R013

## Blocking Gaps

- none
