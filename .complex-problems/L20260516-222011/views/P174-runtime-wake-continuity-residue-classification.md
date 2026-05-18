# P174: Runtime wake continuity residue classification

Status: done
Parent: P162
Root: P000
Source Ticket: T159 (split)
Source Check: none
Package: problems/P000/children/P003/children/P126/children/P135/children/P162/children/P174
Body: problems/P000/children/P003/children/P126/children/P135/children/P162/children/P174/README.md
Ticket(s): T161

## Problem
`runtime_handlers.py` and related wake/session logic can contain cross-wake, idempotency, or notification replay paths. These must be classified so they do not act as hidden LLM context fallbacks.

## Success Criteria
- `runtime_handlers.py` and relevant runtime wake/session call sites are mapped.
- Cross-wake, idempotency, and notification replay residues are classified as active-safe, stale, or risky.
- Tests such as no-wake-replay and child-scope guardrails are identified and run.
- Any active stale path that affects LLM provider input is fixed or split.

## Subproblems
- none

## Results
- R156

## Latest Check
C170

## Bodies
- Problem: problems/P000/children/P003/children/P126/children/P135/children/P162/children/P174/README.md
- Ticket T161: problems/P000/children/P003/children/P126/children/P135/children/P162/children/P174/tickets/T161.md
- Result R156: problems/P000/children/P003/children/P126/children/P135/children/P162/children/P174/results/R156.md
- Check C170: problems/P000/children/P003/children/P126/children/P135/children/P162/children/P174/checks/C170.md

## Follow-ups
- none
