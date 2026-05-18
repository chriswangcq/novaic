# P247: Verify shell payload and output boundary tests

Status: done
Parent: P240
Root: P000
Source Ticket: T237 (split)
Source Check: none
Package: problems/P000/children/P003/children/P129/children/P230/children/P240/children/P247
Body: problems/P000/children/P003/children/P129/children/P230/children/P240/children/P247/README.md
Ticket(s): T240

## Problem
After mapping and any wording corrections, focused tests must prove shell output stays bounded and full payload inspection is explicit. This belongs under P240 because the audit is not closed by source reading alone.

## Success Criteria
- Focused runtime shell output contract tests pass.
- Focused Cortex schema/payload inspection tests pass.
- Residue scans show no guidance that encourages raw base64 or full payload injection in normal context.

## Subproblems
- none

## Results
- R235

## Latest Check
C250

## Bodies
- Problem: problems/P000/children/P003/children/P129/children/P230/children/P240/children/P247/README.md
- Ticket T240: problems/P000/children/P003/children/P129/children/P230/children/P240/children/P247/tickets/T240.md
- Result R235: problems/P000/children/P003/children/P129/children/P230/children/P240/children/P247/results/R235.md
- Check C250: problems/P000/children/P003/children/P129/children/P230/children/P240/children/P247/checks/C250.md

## Follow-ups
- none
