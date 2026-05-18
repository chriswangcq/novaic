# P162: Runtime continuity and context.read residue classification

Status: done
Parent: P135
Root: P000
Source Ticket: T146 (split)
Source Check: none
Package: problems/P000/children/P003/children/P126/children/P135/children/P162
Body: problems/P000/children/P003/children/P126/children/P135/children/P162/README.md
Ticket(s): T159

## Problem
Runtime still has context read, notification-hint, idempotency, or continuity-looking paths. These must be classified so safe side paths are not confused with provider-message authority, and stale paths do not survive as hidden fallback logic.

## Success Criteria
- `novaic-agent-runtime/task_queue/handlers/context_handlers.py`, `runtime_handlers.py`, and relevant bridge/context-read callers are mapped.
- Remaining `read_context`, `context.read`, continuity, cross-wake, or historical context paths are classified as active-safe, dead, or stale.
- Any active stale path that can influence LLM provider input is fixed or split.
- Focused tests or static guards covering the classification are identified and run.

## Subproblems
- P173: Context read handler residue classification
- P174: Runtime wake continuity residue classification
- P175: Runtime read_context caller inventory and guard coverage

## Results
- R158

## Latest Check
C172

## Bodies
- Problem: problems/P000/children/P003/children/P126/children/P135/children/P162/README.md
- Ticket T159: problems/P000/children/P003/children/P126/children/P135/children/P162/tickets/T159.md
- Result R158: problems/P000/children/P003/children/P126/children/P135/children/P162/results/R158.md
- Check C172: problems/P000/children/P003/children/P126/children/P135/children/P162/checks/C172.md

## Follow-ups
- none
