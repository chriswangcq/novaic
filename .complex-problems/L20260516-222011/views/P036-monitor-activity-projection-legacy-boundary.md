# P036: Monitor activity projection legacy boundary

Status: done
Parent: P033
Root: P000
Source Ticket: T025 (split)
Source Check: none
Package: problems/P000/children/P001/children/P009/children/P015/children/P033/children/P036
Body: problems/P000/children/P001/children/P009/children/P015/children/P033/children/P036/README.md
Ticket(s): T035

## Problem
Activity projection still maps direct-tool names for historical monitor readability. That is useful, but the implementation and tests should make it impossible to confuse those labels with active tool execution policy.

## Success Criteria
- Keep historical monitor rendering if needed.
- Move/rename legacy direct-tool labels behind explicit historical naming.
- Ensure shell-first `agentctl` activity is the primary current-path behavior.
- Run activity projection/UI focused tests.

## Subproblems
- P045: Backend activity projection legacy labels
- P046: Frontend ActivityTimeline legacy detection

## Results
- R033

## Latest Check
C042

## Bodies
- Problem: problems/P000/children/P001/children/P009/children/P015/children/P033/children/P036/README.md
- Ticket T035: problems/P000/children/P001/children/P009/children/P015/children/P033/children/P036/tickets/T035.md
- Result R033: problems/P000/children/P001/children/P009/children/P015/children/P033/children/P036/results/R033.md
- Check C042: problems/P000/children/P001/children/P009/children/P015/children/P033/children/P036/checks/C042.md

## Follow-ups
- none
