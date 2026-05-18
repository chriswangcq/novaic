# P288: Problem: Session rebuild projection and state read inventory

Status: done
Parent: P282
Root: P000
Source Ticket: T276 (split)
Source Check: none
Package: problems/P000/children/P004/children/P278/children/P282/children/P288
Body: problems/P000/children/P004/children/P278/children/P282/children/P288/README.md
Ticket(s): T312

## Problem
Inspect rebuild, projection, and read helpers to understand how active session state is reconstructed/read, and whether any cache/view can drift from authoritative state.

## Success Criteria
- Map read/rebuild/projection methods and their source tables with file references.
- Explain whether active session reads derive from `tq_session_state` or another pointer.
- Identify test coverage for rebuild/projection/state ownership.

## Subproblems
- P322: Audit active session read paths
- P323: Audit rebuild and pending projection writers
- P324: Audit rebuild projection coverage and guards

## Results
- R312

## Latest Check
C333

## Bodies
- Problem: problems/P000/children/P004/children/P278/children/P282/children/P288/README.md
- Ticket T312: problems/P000/children/P004/children/P278/children/P282/children/P288/tickets/T312.md
- Result R312: problems/P000/children/P004/children/P278/children/P282/children/P288/results/R312.md
- Check C333: problems/P000/children/P004/children/P278/children/P282/children/P288/checks/C333.md

## Follow-ups
- none
