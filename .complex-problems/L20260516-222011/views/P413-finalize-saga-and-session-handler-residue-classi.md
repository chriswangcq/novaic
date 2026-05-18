# P413: Finalize saga and session handler residue classification

Status: done
Parent: P409
Root: P000
Source Ticket: T398 (split)
Source Check: none
Package: problems/P000/children/P004/children/P278/children/P283/children/P329/children/P403/children/P409/children/P413
Body: problems/P000/children/P004/children/P278/children/P283/children/P329/children/P403/children/P409/children/P413/README.md
Ticket(s): T400

## Problem
`wake_finalize.py`, `subagent_wake.py`, and `session_handlers.py` carry finalize/session-ended identity to the Queue session boundary. They must fail closed for missing/stale session generation and preserve finalize reason/remaining stack explicitly.

## Success Criteria
- Inspect finalize saga and session handler guard hits.
- Confirm session generation is validated with explicit positive-generation contracts.
- Confirm finalize reason and remaining stack are required before session-ended mutation.
- Patch and test any dangerous fallback.
- Run focused finalize/session handler tests.

## Subproblems
- none

## Results
- R393

## Latest Check
C419

## Bodies
- Problem: problems/P000/children/P004/children/P278/children/P283/children/P329/children/P403/children/P409/children/P413/README.md
- Ticket T400: problems/P000/children/P004/children/P278/children/P283/children/P329/children/P403/children/P409/children/P413/tickets/T400.md
- Result R393: problems/P000/children/P004/children/P278/children/P283/children/P329/children/P403/children/P409/children/P413/results/R393.md
- Check C419: problems/P000/children/P004/children/P278/children/P283/children/P329/children/P403/children/P409/children/P413/checks/C419.md

## Follow-ups
- none
