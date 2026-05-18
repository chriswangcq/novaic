# P399: Session FSM event generation boundary

Status: done
Parent: P398
Root: P000
Source Ticket: T389 (split)
Source Check: none
Package: problems/P000/children/P004/children/P278/children/P283/children/P328/children/P339/children/P380/children/P385/children/P388/children/P389/children/P398/children/P399
Body: problems/P000/children/P004/children/P278/children/P283/children/P328/children/P339/children/P380/children/P385/children/P388/children/P389/children/P398/children/P399/README.md
Ticket(s): T390

## Problem
`novaic-agent-runtime/queue_service/session_fsm.py` still has `event_generation=int(decision.payload.get("event_generation") or 0)` in the session FSM decision boundary. This is a generation-like control-plane default inside the session FSM, so it must be patched or explicitly classified with evidence rather than left as an ambiguous fallback.

## Success Criteria
- Inspect the `event_generation` path in `session_fsm.py` and identify whether it is live authority, event sequencing metadata, or a dead/unused value.
- Remove any silent `or 0` fallback for live or event-sequencing generation-like data.
- Add focused regression tests if behavior changes.
- Rerun a targeted guard that no unclassified `event_generation` raw default remains.
- Document the classification in the result.

## Subproblems
- none

## Results
- R382

## Latest Check
C405

## Bodies
- Problem: problems/P000/children/P004/children/P278/children/P283/children/P328/children/P339/children/P380/children/P385/children/P388/children/P389/children/P398/children/P399/README.md
- Ticket T390: problems/P000/children/P004/children/P278/children/P283/children/P328/children/P339/children/P380/children/P385/children/P388/children/P389/children/P398/children/P399/tickets/T390.md
- Result R382: problems/P000/children/P004/children/P278/children/P283/children/P328/children/P339/children/P380/children/P385/children/P388/children/P389/children/P398/children/P399/results/R382.md
- Check C405: problems/P000/children/P004/children/P278/children/P283/children/P328/children/P339/children/P380/children/P385/children/P388/children/P389/children/P398/children/P399/checks/C405.md

## Follow-ups
- none
