# P372: Scope End Boundary Contract Propagation

Status: done
Parent: P368
Root: P000
Source Ticket: T359 (split)
Source Check: none
Package: problems/P000/children/P004/children/P278/children/P283/children/P328/children/P338/children/P368/children/P372
Body: problems/P000/children/P004/children/P278/children/P283/children/P328/children/P338/children/P368/children/P372/README.md
Ticket(s): T361

## Problem
The runtime `CORTEX_SCOPE_END` path must forward explicit finalize diagnostics through handler and bridge boundaries instead of dropping them before Cortex receives the request.

## Success Criteria
- `CORTEX_SCOPE_END` handler validates and forwards explicit finalize diagnostics where supplied.
- `CortexBridge.scope_end` and the Cortex API request contract accept explicit `session_generation`, `finalize_reason`, and remaining-stack diagnostics.
- Missing or non-positive generation is rejected for finalize diagnostic archive requests.
- Non-finalize or legacy-neutral callers remain explicit and deterministic without hidden active-generation inference.
- Focused runtime bridge/handler tests prove the propagated request payload.

## Subproblems
- none

## Results
- R354

## Latest Check
C377

## Bodies
- Problem: problems/P000/children/P004/children/P278/children/P283/children/P328/children/P338/children/P368/children/P372/README.md
- Ticket T361: problems/P000/children/P004/children/P278/children/P283/children/P328/children/P338/children/P368/children/P372/tickets/T361.md
- Result R354: problems/P000/children/P004/children/P278/children/P283/children/P328/children/P338/children/P368/children/P372/results/R354.md
- Check C377: problems/P000/children/P004/children/P278/children/P283/children/P328/children/P338/children/P368/children/P372/checks/C377.md

## Follow-ups
- none
