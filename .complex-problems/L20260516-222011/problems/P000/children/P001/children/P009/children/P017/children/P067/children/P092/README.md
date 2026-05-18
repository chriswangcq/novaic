# Business Cortex Common test residue scan

## Problem

Business, Cortex, and Common tests may contain stale skip/TODO/FIXME/compat/fallback/legacy fixtures around service contracts, context projection, and blob/tool boundaries.

## Success Criteria

- Scan `novaic-business`, `novaic-cortex`, and `novaic-common` tests for residue markers.
- Classify hits and clean tiny stale fixture/comment residue when safe.
- Run focused service/library tests or explicit no-code-change verification.
