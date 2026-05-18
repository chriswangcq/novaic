# Projection test residue cleanup

## Problem

Tests can preserve obsolete contracts even after production code is cleaned. Projection-related tests should assert the desired shell/display/artifact contracts, not accidental legacy payload shapes.

## Success Criteria

- Audit projection tests for obsolete legacy-shape assertions.
- Remove or rewrite tests that protect stale behavior.
- Preserve tests that intentionally guard against historical/persisted malformed inputs, but label them by behavior rather than legacy endorsement.
- Run focused test suites after cleanup.
