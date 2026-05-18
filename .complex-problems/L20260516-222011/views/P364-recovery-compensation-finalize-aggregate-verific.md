# P364: Recovery compensation finalize aggregate verification

Status: done
Parent: P351
Root: P000
Source Ticket: T348 (split)
Source Check: none
Package: problems/P000/children/P004/children/P278/children/P283/children/P328/children/P337/children/P351/children/P364
Body: problems/P000/children/P004/children/P278/children/P283/children/P328/children/P337/children/P351/children/P364/README.md
Ticket(s): T352

## Problem
After source mapping and targeted fixes, P351 needs an aggregate verification pass proving recovery and compensation cannot synthesize ambiguous finalize mutation work. This belongs under P351 because individual fixes can pass while composition leaves a stale path.

## Success Criteria
- Run focused recovery and compensation tests covering generation preservation and missing-identity rejection/reroute.
- Run source/residue searches under `queue_service` for `wake_finalize`, `session_generation`, and generation defaulting patterns.
- Map each P351 success criterion to concrete code and test evidence.
- Record any remaining gap as a follow-up rather than marking P351 solved.

## Subproblems
- P365: Follow-Up: Remove Startup Rebuild Generation Default

## Results
- R345

## Latest Check
C368

## Bodies
- Problem: problems/P000/children/P004/children/P278/children/P283/children/P328/children/P337/children/P351/children/P364/README.md
- Ticket T352: problems/P000/children/P004/children/P278/children/P283/children/P328/children/P337/children/P351/children/P364/tickets/T352.md
- Result R345: problems/P000/children/P004/children/P278/children/P283/children/P328/children/P337/children/P351/children/P364/results/R345.md
- Check C366: problems/P000/children/P004/children/P278/children/P283/children/P328/children/P337/children/P351/children/P364/checks/C366.md
- Check C368: problems/P000/children/P004/children/P278/children/P283/children/P328/children/P337/children/P351/children/P364/checks/C368.md

## Follow-ups
- P365: Follow-Up: Remove Startup Rebuild Generation Default
