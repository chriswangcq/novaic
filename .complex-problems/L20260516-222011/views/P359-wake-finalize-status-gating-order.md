# P359: Wake finalize status gating order

Status: done
Parent: P354
Root: P000
Source Ticket: T341 (split)
Source Check: none
Package: problems/P000/children/P004/children/P278/children/P283/children/P328/children/P337/children/P350/children/P354/children/P359
Body: problems/P000/children/P004/children/P278/children/P283/children/P328/children/P337/children/P350/children/P354/children/P359/README.md
Ticket(s): T344

## Problem
The wake-finalize saga currently mutates Business subagent status before the session-generation-owned `session_ended` transition. If a finalize DAG is stale, Business status can be changed before the authoritative session state rejects the generation.

## Success Criteria
- Inspect the wake-finalize DAG definition and DAG executor dependency/failure behavior.
- Reorder or otherwise gate terminal subagent status tasks so `session_ended` acceptance happens before Business status mutation.
- Add tests proving the generated DAG order has `session_ended` before `set_subagent_sleeping` and `set_subagent_completed`.
- If executor semantics do not preserve the intended gate, split or fix that executor issue rather than relying on ordering by hope.
- Preserve Cortex scope_end ordering intentionally; document whether it remains before or moves after `session_ended`.

## Subproblems
- none

## Results
- R336

## Latest Check
C357

## Bodies
- Problem: problems/P000/children/P004/children/P278/children/P283/children/P328/children/P337/children/P350/children/P354/children/P359/README.md
- Ticket T344: problems/P000/children/P004/children/P278/children/P283/children/P328/children/P337/children/P350/children/P354/children/P359/tickets/T344.md
- Result R336: problems/P000/children/P004/children/P278/children/P283/children/P328/children/P337/children/P350/children/P354/children/P359/results/R336.md
- Check C357: problems/P000/children/P004/children/P278/children/P283/children/P328/children/P337/children/P350/children/P354/children/P359/checks/C357.md

## Follow-ups
- none
