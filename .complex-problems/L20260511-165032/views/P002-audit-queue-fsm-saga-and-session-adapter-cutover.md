# P002: Audit Queue FSM Saga and session adapter cutover

Status: done
Parent: P000
Root: P000
Package: problems/P000/children/P002
Body: problems/P000/children/P002/README.md
Ticket(s): T002

## Problem
Find any remaining live code paths in agent runtime where queue dispatch/session/saga/outbox still bypass the intended FSM/outbox/generation-checked model, use old active-session pointers as authority, or contain fallback/direct imperative branches that can keep old behavior live.

## Success Criteria
- Search and inspect queue service, session state/repo, dispatch subscriber/client, saga orchestrator/repo, outbox workers, and worker assembly.
- Identify confirmed live bypasses vs transitional views/caches.
- Check for hidden env/time/id dependencies in core decision paths where relevant.
- Record evidence and prioritized findings.

## Subproblems
- none

## Results
- R001

## Latest Check
C001

## Bodies
- Problem: problems/P000/children/P002/README.md
- Ticket T002: problems/P000/children/P002/tickets/T002.md
- Result R001: problems/P000/children/P002/results/R001.md
- Check C001: problems/P000/children/P002/checks/C001.md

## Follow-ups
- none
