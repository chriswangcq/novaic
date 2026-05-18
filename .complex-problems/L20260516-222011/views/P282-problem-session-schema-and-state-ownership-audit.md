# P282: Problem: Session schema and state ownership audit

Status: done
Parent: P278
Root: P000
Source Ticket: T275 (split)
Source Check: none
Package: problems/P000/children/P004/children/P278/children/P282
Body: problems/P000/children/P004/children/P278/children/P282/README.md
Ticket(s): T276

## Problem
Audit the queue session persistence schema and repository roles to determine which table is the authority for session state, whether `tq_active_sessions` remains a live pointer/cache/view, and where input/inbox events and pending projections are stored.

## Success Criteria
- Map session-related tables and repository methods with file references.
- State clearly whether `tq_session_state` is the authoritative state source.
- Identify any duplicate active-session source that can drift or should be removed/demoted.

## Subproblems
- P286: Problem: Session schema table inventory
- P287: Problem: Session repository state mutation inventory
- P288: Problem: Session rebuild projection and state read inventory

## Results
- R313

## Latest Check
C334

## Bodies
- Problem: problems/P000/children/P004/children/P278/children/P282/README.md
- Ticket T276: problems/P000/children/P004/children/P278/children/P282/tickets/T276.md
- Result R313: problems/P000/children/P004/children/P278/children/P282/results/R313.md
- Check C334: problems/P000/children/P004/children/P278/children/P282/checks/C334.md

## Follow-ups
- none
