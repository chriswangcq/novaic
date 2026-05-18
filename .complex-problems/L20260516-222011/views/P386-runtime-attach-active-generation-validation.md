# P386: Runtime attach active generation validation

Status: done
Parent: P385
Root: P000
Source Ticket: T376 (split)
Source Check: none
Package: problems/P000/children/P004/children/P278/children/P283/children/P328/children/P339/children/P380/children/P385/children/P386
Body: problems/P000/children/P004/children/P278/children/P283/children/P328/children/P339/children/P380/children/P385/children/P386/README.md
Ticket(s): T377

## Problem
`novaic-agent-runtime/queue_service/session_repo.py` still coerces active session generation with `int(current_active.get("generation") or 0)` in the attach path. That can silently turn malformed or missing active state into generation `0`.

## Success Criteria
- Runtime attach active session generation uses the existing positive generation validator.
- Focused runtime tests still pass for attach/finalize/session state behavior.
- Source guard no longer reports this raw attach-path coercion.
- This belongs under P385 because it closes the runtime half of the residual live generation coercion list.

## Subproblems
- none

## Results
- R370

## Latest Check
C393

## Bodies
- Problem: problems/P000/children/P004/children/P278/children/P283/children/P328/children/P339/children/P380/children/P385/children/P386/README.md
- Ticket T377: problems/P000/children/P004/children/P278/children/P283/children/P328/children/P339/children/P380/children/P385/children/P386/tickets/T377.md
- Result R370: problems/P000/children/P004/children/P278/children/P283/children/P328/children/P339/children/P380/children/P385/children/P386/results/R370.md
- Check C393: problems/P000/children/P004/children/P278/children/P283/children/P328/children/P339/children/P380/children/P385/children/P386/checks/C393.md

## Follow-ups
- none
