# P017: Phase 2.4: Projection verification and non-cutover audit

Status: done
Parent: P003
Root: P000
Package: problems/P000/children/P003/children/P017
Body: problems/P000/children/P003/children/P017/README.md
Ticket(s): T018

## Problem
Verify the projection implementation and ensure Phase 2 does not silently replace existing read paths. This belongs under Phase 2 because the projector must be proven independently before Phase 4 read-path cutover.

## Success Criteria
- Focused projection tests pass.
- Existing ContextEngine tests still pass.
- Static search confirms the pure projector does not read Workspace, IM history, payload files, `context.jsonl`, `summary.md`, or `steps/_index`.
- Static search confirms current endpoints are not yet cut over to the projector.
- Residual integration gaps are recorded for P004/P005/P006.

## Subproblems
- none

## Results
- R016

## Latest Check
C017

## Bodies
- Problem: problems/P000/children/P003/children/P017/README.md
- Ticket T018: problems/P000/children/P003/children/P017/tickets/T018.md
- Result R016: problems/P000/children/P003/children/P017/results/R016.md
- Check C017: problems/P000/children/P003/children/P017/checks/C017.md

## Follow-ups
- none
