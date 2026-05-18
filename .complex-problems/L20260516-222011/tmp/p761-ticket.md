# Device test residue discovery ticket

## Problem Definition

Device tests may preserve stale inline screenshot/media routes, direct Gateway/Business ownership wording, base64/media residue, or fallback/compatibility assumptions.

## Proposed Solution

Discover Device test files, run focused residue searches, spot-read suspicious hits, and classify the result. Record exact remediation candidates if any; otherwise record explicit absence with evidence.

## Acceptance Criteria

- Device test files are discovered.
- Suspicious Device test hits are classified.
- Any stale remediation candidates are listed with file pointers.
- No product code is modified.

## Verification Plan

Use `rg --files novaic-device` to find test-like files, then run focused `rg` searches over those files for Gateway/Business ownership, legacy/fallback/compat/direct/bypass, screenshot/media/base64, VmControl, route, and hardware protocol terms. Spot-read matching slices.

## Risks

- Device tests may intentionally mention screenshot/base64/media protocol primitives that remain valid at lower layers.
- Hardware protocol tests may use direct wording that is unrelated to Gateway/Business bypass.

## Assumptions

- Device test files use conventional `tests/`, `test_*.py`, or `*_test.py` naming.
