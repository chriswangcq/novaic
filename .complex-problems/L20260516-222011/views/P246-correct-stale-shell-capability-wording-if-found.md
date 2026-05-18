# P246: Correct stale shell capability wording if found

Status: done
Parent: P240
Root: P000
Source Ticket: T237 (split)
Source Check: none
Package: problems/P000/children/P003/children/P129/children/P230/children/P240/children/P246
Body: problems/P000/children/P003/children/P129/children/P230/children/P240/children/P246/README.md
Ticket(s): T239

## Problem
Shell capability guidance may still contain stale wording that implies raw payload/base64 output belongs in normal context or replies. This belongs under P240 because misleading guidance is the practical contract bug users are seeing.

## Success Criteria
- Stale or misleading wording found by the mapping pass is corrected.
- If no correction is needed, the result cites the inspected wording and explains why it is already correct.
- No compatibility or fallback text encourages old direct-tool/raw-output behavior.

## Subproblems
- none

## Results
- R234

## Latest Check
C249

## Bodies
- Problem: problems/P000/children/P003/children/P129/children/P230/children/P240/children/P246/README.md
- Ticket T239: problems/P000/children/P003/children/P129/children/P230/children/P240/children/P246/tickets/T239.md
- Result R234: problems/P000/children/P003/children/P129/children/P230/children/P240/children/P246/results/R234.md
- Check C249: problems/P000/children/P003/children/P129/children/P230/children/P240/children/P246/checks/C249.md

## Follow-ups
- none
