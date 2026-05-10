# P029: Phase 3.2.1: Emit root and wake lifecycle events

Status: done
Parent: P024
Root: P000
Package: problems/P000/children/P004/children/P024/children/P029
Body: problems/P000/children/P004/children/P024/children/P029/README.md
Ticket(s): T023

## Problem
Root and wake scope lifecycle writes must emit ContextEvents for initialization and archive/finalize facts. The current code still creates scope files directly as the only authoritative record.

## Success Criteria
- The root/wake creation path emits `RootInitialized` and `WakeStarted` events.
- Root/wake archive/finalize emits `WakeArchived` when a wake is archived.
- Tests verify event log contents for root/wake lifecycle operations.
- Idempotency keys are stable for retry paths.
- Existing scope file artifacts remain only as transitional debug/projection output.

## Subproblems
- none

## Results
- R020

## Latest Check
C022

## Bodies
- Problem: problems/P000/children/P004/children/P024/children/P029/README.md
- Ticket T023: problems/P000/children/P004/children/P024/children/P029/tickets/T023.md
- Result R020: problems/P000/children/P004/children/P024/children/P029/results/R020.md
- Check C022: problems/P000/children/P004/children/P024/children/P029/checks/C022.md

## Follow-ups
- none
