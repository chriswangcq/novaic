# P596: Active Stack and System Message Display Ordering Test Coverage

Status: done
Parent: P582
Root: P000
Source Ticket: T584 (split)
Source Check: none
Package: problems/P000/children/P005/children/P553/children/P564/children/P575/children/P582/children/P596
Body: problems/P000/children/P005/children/P553/children/P564/children/P575/children/P582/children/P596/README.md
Ticket(s): T591

## Problem
Verify that tests protect the ordering contract where active-stack/system messages do not prevent the immediately preceding current-round `display` tool result from being projected as `display_perception`.

## Success Criteria
- Records exact scans for active-stack, system-message, latest tool-call, and current-round projection tests.
- Cites tests proving current display perception still works when active-stack/system messages are appended after tool output.
- Cites tests proving non-current display messages fall back to history projection.
- Creates a concrete follow-up if ordering coverage is missing or indirect.
- Explains why this belongs under the display regression inventory split.

## Subproblems
- none

## Results
- R585

## Latest Check
C623

## Bodies
- Problem: problems/P000/children/P005/children/P553/children/P564/children/P575/children/P582/children/P596/README.md
- Ticket T591: problems/P000/children/P005/children/P553/children/P564/children/P575/children/P582/children/P596/tickets/T591.md
- Result R585: problems/P000/children/P005/children/P553/children/P564/children/P575/children/P582/children/P596/results/R585.md
- Check C623: problems/P000/children/P005/children/P553/children/P564/children/P575/children/P582/children/P596/checks/C623.md

## Follow-ups
- none
