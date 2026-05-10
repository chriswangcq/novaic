# P053: Phase 5B3.2 Step Projection Explicit API Cutover

Status: done
Parent: P051
Root: P000
Package: problems/P000/children/P006/children/P046/children/P051/children/P053
Body: problems/P000/children/P006/children/P046/children/P051/children/P053/README.md
Ticket(s): T051

## Problem
`novaic_cortex.step_result_projection` still exposes `format_for_llm` as a compatibility wrapper with an `include_display` boolean. This preserves an old implicit API shape and weakens the explicit projection boundary.

## Success Criteria
- Remove the `format_for_llm` compatibility wrapper or replace it with a current-contract name if the audit proves a public adapter is still necessary.
- Update `novaic_cortex.__init__`, `api.py`, and all Cortex tests to call explicit projection functions.
- Ensure current tool result, historical context, display perception, and monitor previews each use explicit projection APIs.
- Add or update tests proving artifact images are manifest text unless an explicit display-perception projection is used.
- Targeted step-result and tool-output projection tests pass.

## Subproblems
- none

## Results
- R047

## Latest Check
C050

## Bodies
- Problem: problems/P000/children/P006/children/P046/children/P051/children/P053/README.md
- Ticket T051: problems/P000/children/P006/children/P046/children/P051/children/P053/tickets/T051.md
- Result R047: problems/P000/children/P006/children/P046/children/P051/children/P053/results/R047.md
- Check C050: problems/P000/children/P006/children/P046/children/P051/children/P053/checks/C050.md

## Follow-ups
- none
