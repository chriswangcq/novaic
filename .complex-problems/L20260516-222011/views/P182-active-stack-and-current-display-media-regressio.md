# P182: Active stack and current display media regression coverage

Status: done
Parent: P137
Root: P000
Source Ticket: T169 (split)
Source Check: none
Package: problems/P000/children/P003/children/P126/children/P137/children/P182
Body: problems/P000/children/P003/children/P126/children/P137/children/P182/README.md
Ticket(s): T172

## Problem
Current-round display media must remain eligible for display perception even when active stack system messages are appended after tool results. The specific regression risk is that a late system message causes the display tool result to be treated as historical text-only output.

## Success Criteria
- Create or identify a focused test where a current display tool result is followed by active stack injection.
- Prove display/media projection still emits the correct current display perception content.
- Prove historical display results remain manifest/text-only and do not leak raw media.
- Fix any failure or split the failing layer into a smaller child problem.

## Subproblems
- none

## Results
- R168

## Latest Check
C182

## Bodies
- Problem: problems/P000/children/P003/children/P126/children/P137/children/P182/README.md
- Ticket T172: problems/P000/children/P003/children/P126/children/P137/children/P182/tickets/T172.md
- Result R168: problems/P000/children/P003/children/P126/children/P137/children/P182/results/R168.md
- Check C182: problems/P000/children/P003/children/P126/children/P137/children/P182/checks/C182.md

## Follow-ups
- none
