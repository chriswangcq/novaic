# P484: Production side-effect callsite classification

Status: done
Parent: P481
Root: P000
Source Ticket: T476 (split)
Source Check: none
Package: problems/P000/children/P004/children/P279/children/P481/children/P484
Body: problems/P000/children/P004/children/P279/children/P481/children/P484/README.md
Ticket(s): T477

## Problem
P481 needs production direct side-effect call sites classified before cleanup. The inventory has raw hits, but downstream changes need a concise table of which calls are service assembly, generic adapter, durable outbox dispatcher, session-owned effect writer, or suspicious bypass.

## Success Criteria
- Production `SagaOrchestrator.create`, `queue.publish`, task client publish, and session outbox effect call sites are listed with file references.
- Each call site is classified into an explicit category.
- Suspicious or ambiguous call sites are identified for downstream child problems.
- No source code is changed in this classification child.

## Subproblems
- none

## Results
- R473

## Latest Check
C502

## Bodies
- Problem: problems/P000/children/P004/children/P279/children/P481/children/P484/README.md
- Ticket T477: problems/P000/children/P004/children/P279/children/P481/children/P484/tickets/T477.md
- Result R473: problems/P000/children/P004/children/P279/children/P481/children/P484/results/R473.md
- Check C502: problems/P000/children/P004/children/P279/children/P481/children/P484/checks/C502.md

## Follow-ups
- none
