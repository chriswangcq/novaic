# Session-ended delivery tests compatibility cleanup check

## Summary

Success. The test residue review is sufficient for P346: zero-generation tests in the P336 delivery boundary now assert rejection, and remaining zero-generation test cases are either unrelated state baselines or upstream react contract defaults delegated to P347/P337/P339.

## Evidence

- R326 includes the zero-generation search command and classifications.
- `tests/test_pr254_finalize_ownership.py` now has rejection coverage for:
  - repository `generation=0`.
  - wake-finalize `session_generation=0`.
  - handler `generation=0`.
  - SagaClient `generation=0`.
  - route request `generation=0`.
- `tests/test_runtime_explicit_contracts.py` still asserts react contract `session_generation=0`; R326 correctly classifies this as upstream default residue rather than P336 delivery-boundary acceptance.
- Verification passed: `22 passed in 0.27s`.

## Criteria Map

- Search tests for zero-generation finalize/session-ended residue: satisfied.
- Rewrite P336 delivery test that treats zero generation as valid: satisfied; none remained after P341/P342, and direct delivery zero cases assert failure.
- Classify unrelated/upstream tests: satisfied.

## Execution Map

- Read-only search and inspection over tests.
- No code change in P346.
- P346 feeds P347 with upstream react contract default ownership.

## Stress Test

- Checked the main subtle failure: a test could still assert `generation=0` as an accepted session-ended payload. The direct delivery tests do the opposite: they assert rejection.

## Residual Risk

- Non-blocking for P346: upstream react contract defaults remain open until P347/P337/P339 decide or fix them.

## Result IDs

- R326
