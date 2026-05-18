# P398: Close remaining unclassified generation-like guard hits

Status: done
Parent: P389
Root: P000
Source Ticket: none (none)
Source Check: C404
Package: problems/P000/children/P004/children/P278/children/P283/children/P328/children/P339/children/P380/children/P385/children/P388/children/P389/children/P398
Body: problems/P000/children/P004/children/P278/children/P283/children/P328/children/P339/children/P380/children/P385/children/P388/children/P389/children/P398/README.md
Ticket(s): T389

## Problem
P389 still has widened-guard residue after R381. Two hits are too close to live control-plane semantics to leave as "probably safe": the session FSM `event_generation` default and the subagent wake saga `session_generation` coercion. Broader round/counter hits also need a final explicit matrix so the project does not keep ambiguous stale/default code.

## Success Criteria
- Inspect and either patch or explicitly classify `novaic-agent-runtime/queue_service/session_fsm.py` `event_generation=int(decision.payload.get("event_generation") or 0)`.
- Inspect and either patch or explicitly classify `novaic-agent-runtime/task_queue/sagas/subagent_wake.py` `session_generation` coercion.
- Produce a widened guard matrix that separates live session-generation authority, event-generation sequencing, round numbers, retry/health counters, and persistence/audit adapters.
- Patch any remaining live authority/default hit with explicit validators or typed inputs.
- Add focused regression tests for every patched live boundary.
- Rerun the narrow generation guard, the widened guard, and focused tests; no unclassified residue may remain.

## Subproblems
- P399: Session FSM event generation boundary
- P400: Subagent wake session generation boundary
- P401: Widened guard residue matrix

## Results
- R385

## Latest Check
C408

## Bodies
- Problem: problems/P000/children/P004/children/P278/children/P283/children/P328/children/P339/children/P380/children/P385/children/P388/children/P389/children/P398/README.md
- Ticket T389: problems/P000/children/P004/children/P278/children/P283/children/P328/children/P339/children/P380/children/P385/children/P388/children/P389/children/P398/tickets/T389.md
- Result R385: problems/P000/children/P004/children/P278/children/P283/children/P328/children/P339/children/P380/children/P385/children/P388/children/P389/children/P398/results/R385.md
- Check C408: problems/P000/children/P004/children/P278/children/P283/children/P328/children/P339/children/P380/children/P385/children/P388/children/P389/children/P398/checks/C408.md

## Follow-ups
- none
