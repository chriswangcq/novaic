# Gateway Business Device test residue discovery ticket

## Problem Definition

The P756 source-code discovery result did not cover relevant tests. Test fixtures and comments can preserve stale Gateway/Business/Device ownership assumptions, direct-route expectations, screenshot/base64 media assumptions, or fallback/compatibility behavior even when production code is clean.

## Proposed Solution

Run bounded read-only searches over test directories and test-like files in `novaic-gateway`, `novaic-business`, and `novaic-device`. Classify hits into current guard fixture, intentional protocol/media test, stale misleading residue, or unrelated domain vocabulary. Record exact remediation candidates without changing production code in this discovery follow-up.

## Acceptance Criteria

- Relevant tests in `novaic-gateway`, `novaic-business`, and `novaic-device` are scanned.
- Every suspicious hit family is classified with file pointers.
- Stale or misleading test fixture/comment candidates are listed separately from production candidates.
- No product code is modified in this discovery follow-up.

## Verification Plan

Use `rg --files` and focused `rg` searches over test paths for gateway/business/device ownership terms, legacy/fallback/compat/direct terms, screenshot/media/base64 route terms, and queue/device boundary terms. Spot-read suspicious hits and record the classification.

## Risks

- Many test hits may intentionally preserve legacy negative fixtures; do not delete or mark them stale without context.
- Some repos may have no dedicated tests for the searched term family; absence should be recorded rather than inferred.

## Assumptions

- Test files live under conventional `tests/` directories or use `test_*.py` naming inside the relevant service repos.
