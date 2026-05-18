# P061: Child Problem: large media-like shell stdout regression coverage

Status: done
Parent: P052
Root: P000
Source Ticket: T049 (split)
Source Check: none
Package: problems/P000/children/P001/children/P009/children/P016/children/P048/children/P052/children/P061
Body: problems/P000/children/P001/children/P009/children/P016/children/P048/children/P052/children/P061/README.md
Ticket(s): T052

## Problem
The project needs a regression test that simulates a shell command emitting large media/base64-like stdout and proves the LLM-facing context receives only bounded terminal text. Without this, future shell/CLI changes can accidentally reintroduce base64-as-context behavior.

## Success Criteria
- A focused test simulates large base64-like stdout from shell.
- The test asserts the model-visible shell observation is truncated/bounded and not interpreted as image/display content.
- The test is run together with adjacent shell/context projection tests.

## Subproblems
- none

## Results
- R046

## Latest Check
C058

## Bodies
- Problem: problems/P000/children/P001/children/P009/children/P016/children/P048/children/P052/children/P061/README.md
- Ticket T052: problems/P000/children/P001/children/P009/children/P016/children/P048/children/P052/children/P061/tickets/T052.md
- Result R046: problems/P000/children/P001/children/P009/children/P016/children/P048/children/P052/children/P061/results/R046.md
- Check C058: problems/P000/children/P001/children/P009/children/P016/children/P048/children/P052/children/P061/checks/C058.md

## Follow-ups
- none
