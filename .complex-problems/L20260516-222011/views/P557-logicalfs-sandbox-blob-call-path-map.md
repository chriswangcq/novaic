# P557: LogicalFS Sandbox Blob Call Path Map

Status: done
Parent: P552
Root: P000
Source Ticket: T550 (split)
Source Check: none
Package: problems/P000/children/P005/children/P552/children/P557
Body: problems/P000/children/P005/children/P552/children/P557/README.md
Ticket(s): T552

## Problem
Map imports and call paths between Cortex, LogicalFS, sandbox, and blob surfaces. This child belongs under P552 because boundaries are about who calls whom, not just file locations.

## Success Criteria
- Captures import/call scan commands and outputs.
- Explains the current layering direction with file references.
- Flags suspicious direct calls for the P553 residue inventory.
- Distinguishes intended blob artifact paths from real-time RO/RW file paths.

## Subproblems
- P559: Cortex Boundary Call Path Map
- P560: Sandbox LogicalFS Blob Service Call Path Map
- P561: Artifact And Display Blob Usage Map

## Results
- R552

## Latest Check
C586

## Bodies
- Problem: problems/P000/children/P005/children/P552/children/P557/README.md
- Ticket T552: problems/P000/children/P005/children/P552/children/P557/tickets/T552.md
- Result R552: problems/P000/children/P005/children/P552/children/P557/results/R552.md
- Check C586: problems/P000/children/P005/children/P552/children/P557/checks/C586.md

## Follow-ups
- none
