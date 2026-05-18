# P689: Queue service worker and FSM role map

Status: done
Parent: P683
Root: P000
Source Ticket: T682 (split)
Source Check: none
Package: problems/P000/children/P007/children/P668/children/P673/children/P683/children/P689
Body: problems/P000/children/P007/children/P668/children/P673/children/P683/children/P689/README.md
Ticket(s): T683

## Problem
Map queue-service entrypoints and worker roles from source evidence, including queue service API/process, task worker, saga worker, session outbox worker, saga outbox worker, scheduler, health, FSM substrate, and session coordination. Distinguish generic infrastructure from queue-service business/runtime decisions.

## Success Criteria
- Queue-service entrypoint files and launch commands are identified with evidence.
- Worker/FSM roles are summarized in a compact map.
- Any stale/misleading queue-service entrypoint issue discovered is either patched if low-risk or recorded.
- Relevant syntax/import/static checks are run if code changes occur.

## Subproblems
- P692: Queue service launch command evidence supplement

## Results
- R678

## Latest Check
C722

## Bodies
- Problem: problems/P000/children/P007/children/P668/children/P673/children/P683/children/P689/README.md
- Ticket T683: problems/P000/children/P007/children/P668/children/P673/children/P683/children/P689/tickets/T683.md
- Result R678: problems/P000/children/P007/children/P668/children/P673/children/P683/children/P689/results/R678.md
- Check C720: problems/P000/children/P007/children/P668/children/P673/children/P683/children/P689/checks/C720.md
- Check C722: problems/P000/children/P007/children/P668/children/P673/children/P683/children/P689/checks/C722.md

## Follow-ups
- P692: Queue service launch command evidence supplement
