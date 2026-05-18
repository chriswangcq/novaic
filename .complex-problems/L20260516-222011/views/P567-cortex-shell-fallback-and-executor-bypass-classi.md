# P567: Cortex Shell Fallback And Executor Bypass Classification

Status: done
Parent: P562
Root: P000
Source Ticket: T558 (split)
Source Check: none
Package: problems/P000/children/P005/children/P553/children/P562/children/P567
Body: problems/P000/children/P005/children/P553/children/P562/children/P567/README.md
Ticket(s): T560

## Problem
Classify Cortex occurrences of local shell fallback, process-runner bypass, direct subprocess execution, and sandbox executor compatibility that could bypass sandboxd. This belongs under P562 because shell must go through `MountNamespaceLogicalFS` and sandboxd.

## Success Criteria
- Records exact Cortex scan commands and outputs for fallback/process/subprocess/sandbox executor terms.
- Reads relevant code slices with line references.
- Confirms whether any production local execution fallback remains.
- Identifies any remediation candidate for P554.

## Subproblems
- none

## Results
- R556

## Latest Check
C590

## Bodies
- Problem: problems/P000/children/P005/children/P553/children/P562/children/P567/README.md
- Ticket T560: problems/P000/children/P005/children/P553/children/P562/children/P567/tickets/T560.md
- Result R556: problems/P000/children/P005/children/P553/children/P562/children/P567/results/R556.md
- Check C590: problems/P000/children/P005/children/P553/children/P562/children/P567/checks/C590.md

## Follow-ups
- none
