# P683: Queue and runtime worker role classification

Status: done
Parent: P673
Root: P000
Source Ticket: T677 (split)
Source Check: none
Package: problems/P000/children/P007/children/P668/children/P673/children/P683
Body: problems/P000/children/P007/children/P668/children/P673/children/P683/README.md
Ticket(s): T682

## Problem
Classify queue-service and agent-runtime worker entrypoints from source evidence: task worker, saga worker, session outbox worker, saga outbox worker, scheduler, health, queue service, and runtime loop entrypoints. Explain which are generic worker infrastructure versus business/runtime-specific computation.

## Success Criteria
- Queue/runtime entrypoint files and launch commands are identified with file evidence.
- Worker roles are summarized clearly without relying on old mental models.
- Misleading duplicate or stale queue/runtime entrypoint code is patched if low-risk, otherwise recorded as residual risk.
- Relevant syntax/import/static checks are run if code changes occur.

## Subproblems
- P689: Queue service worker and FSM role map
- P690: Agent runtime loop and worker role map
- P691: Queue/runtime stale entrypoint cleanup and verification

## Results
- R684

## Latest Check
C727

## Bodies
- Problem: problems/P000/children/P007/children/P668/children/P673/children/P683/README.md
- Ticket T682: problems/P000/children/P007/children/P668/children/P673/children/P683/tickets/T682.md
- Result R684: problems/P000/children/P007/children/P668/children/P673/children/P683/results/R684.md
- Check C727: problems/P000/children/P007/children/P668/children/P673/children/P683/checks/C727.md

## Follow-ups
- none
