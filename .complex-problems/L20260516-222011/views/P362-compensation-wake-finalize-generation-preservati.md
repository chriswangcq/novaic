# P362: Compensation wake_finalize generation preservation

Status: done
Parent: P351
Root: P000
Source Ticket: T348 (split)
Source Check: none
Package: problems/P000/children/P004/children/P278/children/P283/children/P328/children/P337/children/P351/children/P362
Body: problems/P000/children/P004/children/P278/children/P283/children/P328/children/P337/children/P351/children/P362/README.md
Ticket(s): T350

## Problem
Saga compensation-created `wake_finalize` contexts must preserve explicit positive session generation and wake scope identity when the failed saga/task had them. This belongs under P351 because compensation can otherwise bypass the normal wake-finalize identity contract.

## Success Criteria
- Implement preservation of `scope_id`, wake/root scope identity, subagent identity, and positive session generation in compensation-created `wake_finalize` contexts.
- Remove any compatibility fallback that silently defaults missing generation to `0` or omits generation.
- Add focused tests proving a failed saga with generation produces compensation finalize work with the same positive generation.
- Add focused tests proving missing or invalid generation does not create an ambiguous mutating finalize task.

## Subproblems
- none

## Results
- R343

## Latest Check
C364

## Bodies
- Problem: problems/P000/children/P004/children/P278/children/P283/children/P328/children/P337/children/P351/children/P362/README.md
- Ticket T350: problems/P000/children/P004/children/P278/children/P283/children/P328/children/P337/children/P351/children/P362/tickets/T350.md
- Result R343: problems/P000/children/P004/children/P278/children/P283/children/P328/children/P337/children/P351/children/P362/results/R343.md
- Check C364: problems/P000/children/P004/children/P278/children/P283/children/P328/children/P337/children/P351/children/P362/checks/C364.md

## Follow-ups
- none
