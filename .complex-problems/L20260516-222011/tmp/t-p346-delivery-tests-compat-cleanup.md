# Session-ended delivery tests compatibility cleanup

## Problem Definition

Tests can keep old behavior alive by blessing zero-generation finalize/session-ended payloads. P346 must inspect test residue and ensure no P336 delivery-boundary test treats zero generation as valid.

## Proposed Solution

1. Search tests for `session_generation=0`, `"session_generation": 0`, `generation=0`, and finalize/session-ended assertions.
2. Classify matches:
   - P336 delivery-boundary tests that must assert failure.
   - upstream react contract tests to delegate to P347/P337/P339.
   - unrelated attach/session-state tests.
3. Rewrite any P336 delivery-boundary tests that still accept zero generation.
4. Record exact guard commands for P344.

## Acceptance Criteria

- No P336 delivery test validates zero-generation session-ended/finalize delivery.
- Any remaining test with zero session generation is classified as upstream/delegated or unrelated.
- Focused finalize tests pass.

## Verification Plan

- Run targeted `rg` over tests.
- Inspect all matches before deciding.
- Run `PYTHONPATH=.:../novaic-common pytest -q tests/test_pr254_finalize_ownership.py tests/test_runtime_explicit_contracts.py` if react contract tests are involved.

## Risks

- `generation=0` can appear in expected rejection tests; do not remove those.

## Assumptions

- Zero-generation rejection tests are desirable and should remain.
