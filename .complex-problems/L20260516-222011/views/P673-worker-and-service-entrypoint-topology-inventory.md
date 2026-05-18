# P673: Worker and service entrypoint topology inventory

Status: done
Parent: P668
Root: P000
Source Ticket: T668 (split)
Source Check: none
Package: problems/P000/children/P007/children/P668/children/P673
Body: problems/P000/children/P007/children/P668/children/P673/README.md
Ticket(s): T677

## Problem
Inventory backend worker/service entrypoints from source code and package/config metadata. Build a code-evidence-based map of task, saga, outbox, scheduler, health, queue, Cortex, sandbox, LogicalFS, and Blob service roles without relying on memory.

## Success Criteria
- Worker/service entrypoint files and launch commands are located from source/config.
- Current roles are summarized with file evidence.
- Stale or duplicate entrypoint code that is safe to remove/update is handled or recorded.
- Relevant import/syntax or focused tests are run where changes occur.

## Subproblems
- P682: Entrypoint discovery scan artifacts
- P683: Queue and runtime worker role classification
- P684: Extracted service entrypoint classification
- P685: Entrypoint topology docs and guard alignment

## Results
- R819

## Latest Check
C868

## Bodies
- Problem: problems/P000/children/P007/children/P668/children/P673/README.md
- Ticket T677: problems/P000/children/P007/children/P668/children/P673/tickets/T677.md
- Result R819: problems/P000/children/P007/children/P668/children/P673/results/R819.md
- Check C868: problems/P000/children/P007/children/P668/children/P673/checks/C868.md

## Follow-ups
- none
