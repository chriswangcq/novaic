# Device test residue discovery

## Problem

Scan `novaic-device` tests and test-like files for stale inline screenshot/media routes, direct Gateway/Business ownership wording, base64/media residue, and fallback/compatibility assumptions. This belongs under P758 because Device tests can preserve removed media/control route expectations.

## Success Criteria

- Device test files are discovered with bounded commands.
- Suspicious Device test hits are classified as current hardware/protocol guard, intentional media fixture, stale residue, or unrelated vocabulary.
- Exact stale remediation candidates are listed, or absence is explicitly recorded.
- No product code is modified in this discovery child.
