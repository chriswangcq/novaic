# P042: Runtime finalizer legacy-negative fixtures

Status: done
Parent: P039
Root: P000
Source Ticket: T029 (split)
Source Check: none
Package: problems/P000/children/P001/children/P009/children/P015/children/P033/children/P035/children/P039/children/P042
Body: problems/P000/children/P001/children/P009/children/P015/children/P033/children/P035/children/P039/children/P042/README.md
Ticket(s): T030

## Problem
Finalizer tests use `im_reply` to prove old direct reply calls do not trigger shell-first finalization behavior. These are valid negative fixtures, but the naming and comments should consistently say legacy direct reply.

## Success Criteria
- All finalizer `im_reply` fixtures are explicitly legacy-negative cases.
- Current successful reply-finalize tests use shell `agentctl im reply`.
- Focused finalizer test passes.

## Subproblems
- none

## Results
- R024

## Latest Check
C033

## Bodies
- Problem: problems/P000/children/P001/children/P009/children/P015/children/P033/children/P035/children/P039/children/P042/README.md
- Ticket T030: problems/P000/children/P001/children/P009/children/P015/children/P033/children/P035/children/P039/children/P042/tickets/T030.md
- Result R024: problems/P000/children/P001/children/P009/children/P015/children/P033/children/P035/children/P039/children/P042/results/R024.md
- Check C033: problems/P000/children/P001/children/P009/children/P015/children/P033/children/P035/children/P039/children/P042/checks/C033.md

## Follow-ups
- none
