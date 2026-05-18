# P519: Unit Tool Output and Task Queue Focused Tests

Status: done
Parent: P511
Root: P000
Source Ticket: T512 (split)
Source Check: none
Package: problems/P000/children/P004/children/P281/children/P511/children/P519
Body: problems/P000/children/P004/children/P281/children/P511/children/P519/README.md
Ticket(s): T523

## Problem
Run the focused selected unit tests under `tests/unit/task_queue` and other focused boundary tests that guard shell/tool output, retry/replay, saga worker boundary, and explicit dependencies.

## Success Criteria
- The selected unit/boundary pytest subset exits successfully.
- Exact command, file count, and pytest pass count are recorded.
- Failures are captured for follow-up instead of hidden.

## Subproblems
- P528: Build Unit Tool Output Test Subset
- P529: Run Unit Tool Output Focused Pytest
- P530: Audit Unit Tool Output Focused Result

## Results
- R522

## Latest Check
C555

## Bodies
- Problem: problems/P000/children/P004/children/P281/children/P511/children/P519/README.md
- Ticket T523: problems/P000/children/P004/children/P281/children/P511/children/P519/tickets/T523.md
- Result R522: problems/P000/children/P004/children/P281/children/P511/children/P519/results/R522.md
- Check C555: problems/P000/children/P004/children/P281/children/P511/children/P519/checks/C555.md

## Follow-ups
- none
