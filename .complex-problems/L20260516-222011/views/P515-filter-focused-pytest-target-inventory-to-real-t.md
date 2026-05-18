# P515: Filter Focused Pytest Target Inventory to Real Test Files

Status: done
Parent: P513
Root: P000
Source Ticket: none (none)
Source Check: C533
Package: problems/P000/children/P004/children/P281/children/P510/children/P513/children/P515
Body: problems/P000/children/P004/children/P281/children/P510/children/P513/children/P515/README.md
Ticket(s): T509

## Problem
The P513 focused pytest inventory included `novaic-agent-runtime/tests/unit/task_queue/__init__.py` in the selected focused test file list. This is not a real test file and should not count as a focused pytest target.

## Success Criteria
- Regenerate the selected focused test list so it includes only executable `test_*.py` files.
- Update the inventory artifact and counts.
- Record evidence that no non-test file remains in the selected list.

## Subproblems
- none

## Results
- R505

## Latest Check
C534

## Bodies
- Problem: problems/P000/children/P004/children/P281/children/P510/children/P513/children/P515/README.md
- Ticket T509: problems/P000/children/P004/children/P281/children/P510/children/P513/children/P515/tickets/T509.md
- Result R505: problems/P000/children/P004/children/P281/children/P510/children/P513/children/P515/results/R505.md
- Check C534: problems/P000/children/P004/children/P281/children/P510/children/P513/children/P515/checks/C534.md

## Follow-ups
- none
