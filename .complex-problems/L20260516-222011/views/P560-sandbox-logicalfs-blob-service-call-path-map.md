# P560: Sandbox LogicalFS Blob Service Call Path Map

Status: done
Parent: P557
Root: P000
Source Ticket: T552 (split)
Source Check: none
Package: problems/P000/children/P005/children/P552/children/P557/children/P560
Body: problems/P000/children/P005/children/P552/children/P557/children/P560/README.md
Ticket(s): T554

## Problem
Map how sandbox service/core and LogicalFS interact with each other and with blob service. This child belongs under P557 because sandbox/logicalfs are the intended real-time RO/RW file authority boundary.

## Success Criteria
- Scans sandbox service, sandbox SDK, and LogicalFS imports/calls.
- Reads high-signal service/core files in bounded slices.
- Explains whether sandbox uses LogicalFS for filesystem authority and where blob is used.
- Records suspicious direct fallback paths for P553.

## Subproblems
- none

## Results
- R550

## Latest Check
C584

## Bodies
- Problem: problems/P000/children/P005/children/P552/children/P557/children/P560/README.md
- Ticket T554: problems/P000/children/P005/children/P552/children/P557/children/P560/tickets/T554.md
- Result R550: problems/P000/children/P005/children/P552/children/P557/children/P560/results/R550.md
- Check C584: problems/P000/children/P005/children/P552/children/P557/children/P560/checks/C584.md

## Follow-ups
- none
