# Phase 3B2 Follow-up Nested And Restart Projection Verification

## Problem

Phase 3B2 writes active-stack projections on successful skill_begin and skill_end, but the check found insufficient direct verification for two original criteria: nested begin/end stack state and restart-like store reuse. Close this by adding focused tests that prove nested API lifecycle projection behavior and persisted SQLite projection readability after constructing a fresh operational store on the same database path.

## Success Criteria

- API lifecycle test opens two nested child skills and verifies the SQLite active-stack frames are top-first after each begin.
- API lifecycle test closes the inner child and verifies the SQLite active-stack projection pops only that child while retaining the outer child and wake.
- A restart-like test reads the same active-stack projection from a new operational store instance using the same SQLite database path.
- Targeted tests and full `novaic-cortex/tests` pass.
