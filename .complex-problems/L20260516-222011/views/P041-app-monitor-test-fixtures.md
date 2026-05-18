# P041: App monitor test fixtures

Status: done
Parent: P035
Root: P000
Source Ticket: T027 (split)
Source Check: none
Package: problems/P000/children/P001/children/P009/children/P015/children/P033/children/P035/children/P041
Body: problems/P000/children/P001/children/P009/children/P015/children/P033/children/P035/children/P041/README.md
Ticket(s): T034

## Problem
Frontend monitor tests still include direct-tool historical records. These should be explicit legacy-history examples, while current-path monitor tests should prefer shell/agentctl examples.

## Success Criteria
- ActivityTimeline tests distinguish shell-first current behavior from legacy archived direct-tool behavior.
- Visible assertions avoid normalizing direct-tool names as active behavior.
- Focused frontend tests pass.

## Subproblems
- none

## Results
- R029

## Latest Check
C038

## Bodies
- Problem: problems/P000/children/P001/children/P009/children/P015/children/P033/children/P035/children/P041/README.md
- Ticket T034: problems/P000/children/P001/children/P009/children/P015/children/P033/children/P035/children/P041/tickets/T034.md
- Result R029: problems/P000/children/P001/children/P009/children/P015/children/P033/children/P035/children/P041/results/R029.md
- Check C038: problems/P000/children/P001/children/P009/children/P015/children/P033/children/P035/children/P041/checks/C038.md

## Follow-ups
- none
