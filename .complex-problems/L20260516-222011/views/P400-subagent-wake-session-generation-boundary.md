# P400: Subagent wake session generation boundary

Status: done
Parent: P398
Root: P000
Source Ticket: T389 (split)
Source Check: none
Package: problems/P000/children/P004/children/P278/children/P283/children/P328/children/P339/children/P380/children/P385/children/P388/children/P389/children/P398/children/P400
Body: problems/P000/children/P004/children/P278/children/P283/children/P328/children/P339/children/P380/children/P385/children/P388/children/P389/children/P398/children/P400/README.md
Ticket(s): T391

## Problem
`novaic-agent-runtime/task_queue/sagas/subagent_wake.py` coerces `ctx["session_generation"]` through `int(...)`. Because this value is passed into subagent wake/session creation logic, it may be live session authority and needs an explicit boundary rather than an inline coercion.

## Success Criteria
- Inspect the subagent wake saga context contract for `session_generation`.
- Replace inline coercion with an explicit validator or prove with code evidence that the value is already typed and non-authority.
- Add focused regression tests for malformed/bool/missing generation if the path is live.
- Rerun targeted tests for subagent wake or related saga behavior.
- Document the final classification in the result.

## Subproblems
- none

## Results
- R383

## Latest Check
C406

## Bodies
- Problem: problems/P000/children/P004/children/P278/children/P283/children/P328/children/P339/children/P380/children/P385/children/P388/children/P389/children/P398/children/P400/README.md
- Ticket T391: problems/P000/children/P004/children/P278/children/P283/children/P328/children/P339/children/P380/children/P385/children/P388/children/P389/children/P398/children/P400/tickets/T391.md
- Result R383: problems/P000/children/P004/children/P278/children/P283/children/P328/children/P339/children/P380/children/P385/children/P388/children/P389/children/P398/children/P400/results/R383.md
- Check C406: problems/P000/children/P004/children/P278/children/P283/children/P328/children/P339/children/P380/children/P385/children/P388/children/P389/children/P398/children/P400/checks/C406.md

## Follow-ups
- none
