# P355: Wake finalize mutation payload propagation

Status: done
Parent: P350
Root: P000
Source Ticket: T339 (split)
Source Check: none
Package: problems/P000/children/P004/children/P278/children/P283/children/P328/children/P337/children/P350/children/P355
Body: problems/P000/children/P004/children/P278/children/P283/children/P328/children/P337/children/P350/children/P355/README.md
Ticket(s): T346

## Problem
Even if downstream handlers validate identity, `wake_finalize` must propagate the required identity fields to every mutating task it emits. The finalize payloads must carry enough explicit scope/session information for Cortex and Business status handlers to reject stale or malformed requests.

This child belongs under P350 because identity guards are only effective if finalize task payloads carry the expected identity explicitly.

## Success Criteria
- Inspect `task_queue/sagas/wake_finalize.py` payload builders for Cortex scope-end, subagent sleeping/completed, and session-ended tasks.
- Ensure required positive `session_generation` and relevant wake/root scope identity are included wherever downstream mutating handlers need them.
- Add tests proving emitted mutation payloads include the required identity fields.
- Source guards show no finalize mutation payload is generated with missing or zero session generation.

## Subproblems
- none

## Results
- R339

## Latest Check
C360

## Bodies
- Problem: problems/P000/children/P004/children/P278/children/P283/children/P328/children/P337/children/P350/children/P355/README.md
- Ticket T346: problems/P000/children/P004/children/P278/children/P283/children/P328/children/P337/children/P350/children/P355/tickets/T346.md
- Result R339: problems/P000/children/P004/children/P278/children/P283/children/P328/children/P337/children/P350/children/P355/results/R339.md
- Check C360: problems/P000/children/P004/children/P278/children/P283/children/P328/children/P337/children/P350/children/P355/checks/C360.md

## Follow-ups
- none
