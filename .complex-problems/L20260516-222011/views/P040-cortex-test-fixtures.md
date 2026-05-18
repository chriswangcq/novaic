# P040: Cortex test fixtures

Status: done
Parent: P035
Root: P000
Source Ticket: T027 (split)
Source Check: none
Package: problems/P000/children/P001/children/P009/children/P015/children/P033/children/P035/children/P040
Body: problems/P000/children/P001/children/P009/children/P015/children/P033/children/P035/children/P040/README.md
Ticket(s): T033

## Problem
Cortex tests still include direct-tool vocabulary in payload, wake child, and tool-schema tests. After policy/API cleanup, these tests need to reflect endpoint and migration naming.

## Success Criteria
- Payload tests use endpoint naming and shell/API vocabulary.
- Wake counter tests use `reply_action` rather than `im_reply`.
- Tool schema limit tests still guard removed direct tools without presenting them as active paths.
- Focused Cortex tests pass.

## Subproblems
- none

## Results
- R028

## Latest Check
C037

## Bodies
- Problem: problems/P000/children/P001/children/P009/children/P015/children/P033/children/P035/children/P040/README.md
- Ticket T033: problems/P000/children/P001/children/P009/children/P015/children/P033/children/P035/children/P040/tickets/T033.md
- Result R028: problems/P000/children/P001/children/P009/children/P015/children/P033/children/P035/children/P040/results/R028.md
- Check C037: problems/P000/children/P001/children/P009/children/P015/children/P033/children/P035/children/P040/checks/C037.md

## Follow-ups
- none
