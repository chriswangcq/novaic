# P390: Session FSM finalize generation validation

Status: done
Parent: P389
Root: P000
Source Ticket: T380 (split)
Source Check: none
Package: problems/P000/children/P004/children/P278/children/P283/children/P328/children/P339/children/P380/children/P385/children/P388/children/P389/children/P390
Body: problems/P000/children/P004/children/P278/children/P283/children/P328/children/P339/children/P380/children/P385/children/P388/children/P389/children/P390/README.md
Ticket(s): T381

## Problem
`queue_service/session_fsm.py` still reduces finalize events with raw `int(event.payload.get("finalize_generation") or 0)` and `int(state.generation or 0)`. The pure FSM should not silently accept bool or malformed finalize generation when called directly.

## Success Criteria
- Session finalize decision path uses explicit positive/non-negative generation validation appropriate to input/state semantics.
- Focused session FSM tests reject bool/malformed finalize generation and preserve valid accept/reject behavior.
- Widened guard no longer reports unclassified live session FSM generation coercion.

## Subproblems
- none

## Results
- R373

## Latest Check
C396

## Bodies
- Problem: problems/P000/children/P004/children/P278/children/P283/children/P328/children/P339/children/P380/children/P385/children/P388/children/P389/children/P390/README.md
- Ticket T381: problems/P000/children/P004/children/P278/children/P283/children/P328/children/P339/children/P380/children/P385/children/P388/children/P389/children/P390/tickets/T381.md
- Result R373: problems/P000/children/P004/children/P278/children/P283/children/P328/children/P339/children/P380/children/P385/children/P388/children/P389/children/P390/results/R373.md
- Check C396: problems/P000/children/P004/children/P278/children/P283/children/P328/children/P339/children/P380/children/P385/children/P388/children/P389/children/P390/checks/C396.md

## Follow-ups
- none
