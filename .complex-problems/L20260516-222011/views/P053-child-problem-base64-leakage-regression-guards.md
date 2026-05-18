# P053: Child Problem: base64 leakage regression guards

Status: done
Parent: P048
Root: P000
Source Ticket: T041 (split)
Source Check: none
Package: problems/P000/children/P001/children/P009/children/P016/children/P048/children/P053
Body: problems/P000/children/P001/children/P009/children/P016/children/P048/children/P053/README.md
Ticket(s): T053

## Problem
Once CLI, shell, and display projection contracts are fixed, the repo needs regression guards so future media tools cannot accidentally reintroduce raw base64 into shell text, Cortex context, or LLM request messages.

## Success Criteria
- A focused scan or test catches obvious image-base64 leakage patterns in active media/display/shell output paths.
- Legitimate tiny fixtures or historical examples are explicitly named/classified so the guard does not become noisy.
- The guard is included in a relevant existing test or CI path rather than existing only as an ad hoc manual command.

## Subproblems
- P062: Child Problem: classify active base64 leakage surfaces
- P063: Child Problem: implement active base64 leakage regression guard

## Results
- R050

## Latest Check
C062

## Bodies
- Problem: problems/P000/children/P001/children/P009/children/P016/children/P048/children/P053/README.md
- Ticket T053: problems/P000/children/P001/children/P009/children/P016/children/P048/children/P053/tickets/T053.md
- Result R050: problems/P000/children/P001/children/P009/children/P016/children/P048/children/P053/results/R050.md
- Check C062: problems/P000/children/P001/children/P009/children/P016/children/P048/children/P053/checks/C062.md

## Follow-ups
- none
