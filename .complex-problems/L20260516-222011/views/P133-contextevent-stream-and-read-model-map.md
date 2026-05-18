# P133: ContextEvent stream and read model map

Status: done
Parent: P126
Root: P000
Source Ticket: T122 (split)
Source Check: none
Package: problems/P000/children/P003/children/P126/children/P133
Body: problems/P000/children/P003/children/P126/children/P133/README.md
Ticket(s): T123

## Problem
The ContextEvent stream is intended to be the authoritative cross-wake source for LLM context, but the exact write/read/projection chain must be verified from code and tests.

## Success Criteria
- `context_event_store.py`, `context_event_projection.py`, and `context_event_read_model.py` are mapped with active entrypoints and output shapes.
- The relationship between event sequence, root scope, projected messages, folded summaries, and active stack snapshot is documented.
- Existing tests covering replay order, skill stack, notifications, and tool results are identified and run.
- Any discovered stale or duplicate event projection path is flagged for cleanup or split into a follow-up.

## Subproblems
- P138: ContextEvent append-only store map
- P139: ContextEvent pure projection map
- P140: ContextEvent read model and budget boundary map

## Results
- R123

## Latest Check
C137

## Bodies
- Problem: problems/P000/children/P003/children/P126/children/P133/README.md
- Ticket T123: problems/P000/children/P003/children/P126/children/P133/tickets/T123.md
- Result R123: problems/P000/children/P003/children/P126/children/P133/results/R123.md
- Check C137: problems/P000/children/P003/children/P126/children/P133/checks/C137.md

## Follow-ups
- none
