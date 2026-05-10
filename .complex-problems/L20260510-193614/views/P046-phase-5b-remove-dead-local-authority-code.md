# P046: Phase 5B Remove Dead Local Authority Code

Status: done
Parent: P006
Root: P000
Package: problems/P000/children/P006/children/P046
Body: problems/P000/children/P006/children/P046/README.md
Ticket(s): T046

## Problem
Live source and tests must not keep old local authority paths after SQLite/LogicalFS/manifest cutovers. Any remaining local NDJSON transition authority, active-stack file walking, temp-path authority, or compatibility fallback code should be physically removed rather than left as confusing residue.

## Success Criteria
- Remove or prove absent live local transition-log authority code.
- Remove or prove absent live active-stack file walking authority code.
- Delete compatibility branches that only support pre-cutover behavior and are not required by current tests.
- Adjust tests to assert current authority paths instead of legacy helpers.
- Run targeted tests covering scope lifecycle, active stack projection, operational store, workspace, and context event APIs.

## Subproblems
- P049: Phase 5B1 Scope Lookup And Uniqueness SQLite Cutover
- P050: Phase 5B2 Archive Tree Projection Quarantine
- P051: Phase 5B3 Compatibility Wrapper Review And Removal

## Results
- R052

## Latest Check
C056

## Bodies
- Problem: problems/P000/children/P006/children/P046/README.md
- Ticket T046: problems/P000/children/P006/children/P046/tickets/T046.md
- Result R052: problems/P000/children/P006/children/P046/results/R052.md
- Check C056: problems/P000/children/P006/children/P046/checks/C056.md

## Follow-ups
- none
