# Business test residue discovery

## Problem

Scan `novaic-business` tests and test-like files for stale direct Queue/Gateway/Device wording, hidden fallback/compatibility residue, and misleading ownership assumptions. This belongs under P758 because Business tests may encode old dispatch or dependency-boundary expectations.

## Success Criteria

- Business test files are discovered with bounded commands.
- Suspicious Business test hits are classified as current guard fixture, intentional dispatch behavior, stale residue, or unrelated vocabulary.
- Exact stale remediation candidates are listed, or absence is explicitly recorded.
- No product code is modified in this discovery child.
