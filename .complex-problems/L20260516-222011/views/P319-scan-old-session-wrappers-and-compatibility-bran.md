# P319: Scan old session wrappers and compatibility branches

Status: done
Parent: P293
Root: P000
Source Ticket: T307 (split)
Source Check: none
Package: problems/P000/children/P004/children/P278/children/P282/children/P287/children/P293/children/P319
Body: problems/P000/children/P004/children/P278/children/P282/children/P287/children/P293/children/P319/README.md
Ticket(s): T309

## Problem
Find old repository wrappers, direct publish helpers, compatibility branches, and mutation shortcuts around session dispatch/finalize/outbox that may survive outside the new FSM/outbox ownership boundary.

## Success Criteria
- Search patterns include old wrapper/helper names, legacy active-session concepts, generation compatibility, and attach/wake publish surfaces.
- Matches are classified as production active path, test guard, documentation, or no-match.
- Risky/removable production residue becomes a cleanup follow-up.

## Subproblems
- P321: Rename stale attach publish helper

## Results
- R303

## Latest Check
C324

## Bodies
- Problem: problems/P000/children/P004/children/P278/children/P282/children/P287/children/P293/children/P319/README.md
- Ticket T309: problems/P000/children/P004/children/P278/children/P282/children/P287/children/P293/children/P319/tickets/T309.md
- Result R303: problems/P000/children/P004/children/P278/children/P282/children/P287/children/P293/children/P319/results/R303.md
- Check C322: problems/P000/children/P004/children/P278/children/P282/children/P287/children/P293/children/P319/checks/C322.md
- Check C324: problems/P000/children/P004/children/P278/children/P282/children/P287/children/P293/children/P319/checks/C324.md

## Follow-ups
- P321: Rename stale attach publish helper
