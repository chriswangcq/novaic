# Gateway test residue discovery

## Problem

Scan `novaic-gateway` tests and test-like files for stale Gateway ownership, direct business path, fallback/compatibility, and media/control residue. This belongs under P758 because Gateway test fixtures may preserve old route or ownership assumptions even when production Gateway code is clean.

## Success Criteria

- Gateway test files are discovered with bounded commands.
- Suspicious Gateway test hits are classified as current guard fixture, intentional HTTP edge behavior, stale residue, or unrelated vocabulary.
- Exact stale remediation candidates are listed, or absence is explicitly recorded.
- No product code is modified in this discovery child.
