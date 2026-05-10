# P028: Phase 3B3B Scope Archive Finalize Wiring

Status: done
Parent: P024
Root: P000
Package: problems/P000/children/P004/children/P018/children/P024/children/P028
Body: problems/P000/children/P004/children/P018/children/P024/children/P028/README.md
Ticket(s): T022

## Problem
The scope archive/finalize path currently emits wake archived context data with a hard-coded empty remaining stack and does not route through a durable operational finalize helper. This means archive semantics can still lose live child-stack information or clear state without an explicit finalize event.

## Success Criteria
- Wire root/wake archive or finalize call sites through the Phase 3B3A active-stack finalize helper.
- Archive captures the actual current stack snapshot before clearing projection.
- Archive records explicit finalize reason and deterministic generation/idempotency key.
- Context wake archived event receives the same remaining stack snapshot where semantically relevant.
- Existing archive response behavior stays compatible.

## Subproblems
- none

## Results
- R018

## Latest Check
C020

## Bodies
- Problem: problems/P000/children/P004/children/P018/children/P024/children/P028/README.md
- Ticket T022: problems/P000/children/P004/children/P018/children/P024/children/P028/tickets/T022.md
- Result R018: problems/P000/children/P004/children/P018/children/P024/children/P028/results/R018.md
- Check C020: problems/P000/children/P004/children/P018/children/P024/children/P028/checks/C020.md

## Follow-ups
- none
