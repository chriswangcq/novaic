# Delete stale `test_resolve_for_llm.py`

## Problem Definition

The `resolve_for_llm` helper was removed from production. Its dedicated test file now preserves an obsolete API and inline-image/base64 behavior.

## Proposed Solution

Delete `novaic-cortex/tests/test_resolve_for_llm.py`, then run `rg` to confirm no test or production references remain outside ledger/docs notes.

## Acceptance Criteria

- Stale test file is removed.
- No active test imports `resolve_for_llm`.
- Focused Cortex projection tests still pass.

## Verification Plan

Run `rg "resolve_for_llm"` after deletion and run focused Cortex projection tests.

## Risks

- None beyond intentionally removing obsolete API coverage.

## Assumptions

- New projection tests cover the desired replacement contracts.
