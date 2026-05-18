# Business test residue discovery ticket

## Problem Definition

Business tests may preserve stale direct Queue/Gateway/Device wording, hidden fallback/compatibility residue, or misleading ownership assumptions around dispatch and IM aggregation.

## Proposed Solution

Discover Business test files, run focused residue searches, spot-read suspicious hits, and classify the result. Record exact remediation candidates if any; otherwise record explicit absence with evidence.

## Acceptance Criteria

- Business test files are discovered.
- Suspicious Business test hits are classified.
- Any stale remediation candidates are listed with file pointers.
- No product code is modified.

## Verification Plan

Use `rg --files novaic-business` to find test-like files, then run focused `rg` searches over those files for Gateway/Device/Queue ownership, legacy/fallback/compat/direct/bypass, screenshot/media/base64, aggregation, and dispatch terms. Spot-read matching slices.

## Risks

- Business tests may intentionally include direct Queue wording as current boundary assertions.
- Aggregation tests may include fallback-like terms for product behavior, not architecture residue.

## Assumptions

- Business test files use conventional `tests/`, `test_*.py`, or `*_test.py` naming.
