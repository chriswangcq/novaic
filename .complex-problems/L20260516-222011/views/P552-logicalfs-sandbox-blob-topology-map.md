# P552: LogicalFS Sandbox Blob Topology Map

Status: done
Parent: P005
Root: P000
Source Ticket: T549 (split)
Source Check: none
Package: problems/P000/children/P005/children/P552
Body: problems/P000/children/P005/children/P552/README.md
Ticket(s): T550

## Problem
Map the current files, imports, and runtime call paths among Cortex, LogicalFS, sandbox service/core, and blob service. This child belongs under P005 because cleanup decisions require a precise layer map before removing any path.

## Success Criteria
- Lists relevant local repositories/modules with file references.
- Explains intended ownership of RO/RW real-time file semantics versus blob artifact storage.
- Identifies main CLI/service entrypoints and tests covering the layer.
- Records exact discovery commands.

## Subproblems
- P556: LogicalFS Sandbox Blob Module Inventory
- P557: LogicalFS Sandbox Blob Call Path Map
- P558: LogicalFS Sandbox Blob Entry Points And Tests Map

## Results
- R554

## Latest Check
C588

## Bodies
- Problem: problems/P000/children/P005/children/P552/README.md
- Ticket T550: problems/P000/children/P005/children/P552/tickets/T550.md
- Result R554: problems/P000/children/P005/children/P552/results/R554.md
- Check C588: problems/P000/children/P005/children/P552/checks/C588.md

## Follow-ups
- none
