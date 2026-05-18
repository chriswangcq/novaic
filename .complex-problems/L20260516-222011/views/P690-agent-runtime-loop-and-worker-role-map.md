# P690: Agent runtime loop and worker role map

Status: done
Parent: P683
Root: P000
Source Ticket: T682 (split)
Source Check: none
Package: problems/P000/children/P007/children/P668/children/P673/children/P683/children/P690
Body: problems/P000/children/P007/children/P668/children/P673/children/P683/children/P690/README.md
Ticket(s): T685

## Problem
Map agent-runtime entrypoints from source evidence, including runtime loop, shell/tool execution boundaries, queue worker integration, and any runtime process wrappers. Explain how runtime processes relate to queue-service workers without conflating CPU/process with ledger/outbox state.

## Success Criteria
- Agent-runtime entrypoint files and launch commands are identified with evidence.
- Runtime loop/tool execution roles are summarized in a compact map.
- Misleading or stale runtime entrypoint naming is patched if low-risk or recorded.
- Relevant syntax/import/static checks are run if code changes occur.

## Subproblems
- none

## Results
- R680

## Latest Check
C723

## Bodies
- Problem: problems/P000/children/P007/children/P668/children/P673/children/P683/children/P690/README.md
- Ticket T685: problems/P000/children/P007/children/P668/children/P673/children/P683/children/P690/tickets/T685.md
- Result R680: problems/P000/children/P007/children/P668/children/P673/children/P683/children/P690/results/R680.md
- Check C723: problems/P000/children/P007/children/P668/children/P673/children/P683/children/P690/checks/C723.md

## Follow-ups
- none
