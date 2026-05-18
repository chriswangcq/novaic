# Gateway test residue discovery ticket

## Problem Definition

Gateway tests may contain stale direct-business, ownership, fallback/compatibility, or media/control route assumptions that production code no longer uses.

## Proposed Solution

Discover Gateway test files, run focused residue searches, spot-read suspicious hits, and classify the result. Record exact remediation candidates if any; otherwise record explicit absence with evidence.

## Acceptance Criteria

- Gateway test files are discovered.
- Suspicious Gateway test hits are classified.
- Any stale remediation candidates are listed with file pointers.
- No product code is modified.

## Verification Plan

Use `rg --files novaic-gateway` to find test-like files, then run focused `rg` searches over those files for ownership/direct/fallback/compat/media/screenshot/base64 terms. Spot-read matching slices.

## Risks

- Gateway may have no conventional tests; that absence must be recorded instead of assumed.
- HTTP edge tests may legitimately mention route or gateway vocabulary.

## Assumptions

- Gateway test files use conventional `tests/`, `test_*.py`, or `*_test.py` naming.
