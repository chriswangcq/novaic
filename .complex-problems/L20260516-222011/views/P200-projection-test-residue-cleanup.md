# P200: Projection test residue cleanup

Status: done
Parent: P187
Root: P000
Source Ticket: T188 (split)
Source Check: none
Package: problems/P000/children/P003/children/P127/children/P187/children/P200
Body: problems/P000/children/P003/children/P127/children/P187/children/P200/README.md
Ticket(s): T202

## Problem
Tests can preserve obsolete contracts even after production code is cleaned. Projection-related tests should assert the desired shell/display/artifact contracts, not accidental legacy payload shapes.

## Success Criteria
- Audit projection tests for obsolete legacy-shape assertions.
- Remove or rewrite tests that protect stale behavior.
- Preserve tests that intentionally guard against historical/persisted malformed inputs, but label them by behavior rather than legacy endorsement.
- Run focused test suites after cleanup.

## Subproblems
- P213: Delete stale `resolve_for_llm` tests
- P214: Audit projection guard test labels and assertions
- P215: Run projection test cleanup verification

## Results
- R201

## Latest Check
C215

## Bodies
- Problem: problems/P000/children/P003/children/P127/children/P187/children/P200/README.md
- Ticket T202: problems/P000/children/P003/children/P127/children/P187/children/P200/tickets/T202.md
- Result R201: problems/P000/children/P003/children/P127/children/P187/children/P200/results/R201.md
- Check C215: problems/P000/children/P003/children/P127/children/P187/children/P200/checks/C215.md

## Follow-ups
- none
