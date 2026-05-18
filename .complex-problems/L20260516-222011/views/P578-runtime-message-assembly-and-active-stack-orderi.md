# P578: Runtime Message Assembly And Active Stack Ordering Inventory

Status: done
Parent: P574
Root: P000
Source Ticket: T569 (split)
Source Check: none
Package: problems/P000/children/P005/children/P553/children/P564/children/P574/children/P578
Body: problems/P000/children/P005/children/P553/children/P564/children/P574/children/P578/README.md
Ticket(s): T570

## Problem
Audit runtime context/message assembly before provider serialization, including tool-result messages, assistant tool calls, active stack/system injection, and history ordering. This belongs under P574 because raw media text or misplaced system messages can appear before provider adapters even see the request.

## Success Criteria
- Records exact scan commands and outputs for message assembly, context prepare/build functions, active stack insertion, and tool result message construction.
- Reads relevant runtime code/test slices with line references.
- Classifies tool-result/history/system-message projections as intended, risky, removable, or follow-up.
- Identifies whether active stack ordering can interfere with current-turn display/image delivery.
- Captures any high-confidence risky residue for P554 remediation.

## Subproblems
- none

## Results
- R565

## Latest Check
C601

## Bodies
- Problem: problems/P000/children/P005/children/P553/children/P564/children/P574/children/P578/README.md
- Ticket T570: problems/P000/children/P005/children/P553/children/P564/children/P574/children/P578/tickets/T570.md
- Result R565: problems/P000/children/P005/children/P553/children/P564/children/P574/children/P578/results/R565.md
- Check C601: problems/P000/children/P005/children/P553/children/P564/children/P574/children/P578/checks/C601.md

## Follow-ups
- none
