# P559: Cortex Boundary Call Path Map

Status: done
Parent: P557
Root: P000
Source Ticket: T552 (split)
Source Check: none
Package: problems/P000/children/P005/children/P552/children/P557/children/P559
Body: problems/P000/children/P005/children/P552/children/P557/children/P559/README.md
Ticket(s): T553

## Problem
Map how Cortex calls or references LogicalFS, sandbox, and blob-related surfaces. This child belongs under P557 because Cortex is the top semantic layer and should not own low-level real-time filesystem mechanics directly.

## Success Criteria
- Scans Cortex imports/calls for LogicalFS, sandbox, blob, RO/RW, materialization, and artifact terms.
- Reads high-signal Cortex files in bounded slices.
- Classifies current call direction and suspicious direct paths.
- Records exact commands and artifacts.

## Subproblems
- none

## Results
- R549

## Latest Check
C583

## Bodies
- Problem: problems/P000/children/P005/children/P552/children/P557/children/P559/README.md
- Ticket T553: problems/P000/children/P005/children/P552/children/P557/children/P559/tickets/T553.md
- Result R549: problems/P000/children/P005/children/P552/children/P557/children/P559/results/R549.md
- Check C583: problems/P000/children/P005/children/P552/children/P557/children/P559/checks/C583.md

## Follow-ups
- none
