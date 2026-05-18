# P571: Cortex BlobObjectStore Adapter Boundary Classification

Status: done
Parent: P563
Root: P000
Source Ticket: T564 (split)
Source Check: none
Package: problems/P000/children/P005/children/P553/children/P563/children/P571
Body: problems/P000/children/P005/children/P553/children/P563/children/P571/README.md
Ticket(s): T565

## Problem
Classify `BlobObjectStore` and Cortex registry/store adapter usage to determine whether it is strictly a LogicalFS object-store adapter below Workspace semantics or whether it gives Cortex a direct blob-as-workspace authority bypass.

## Success Criteria
- Records exact scan commands and outputs for `BlobObjectStore`, `ObjectStore`, object adapter, registry, and Cortex store terms.
- Reads relevant Cortex/LogicalFS adapter slices with line references.
- Classifies each hit bucket as intended, risky, removable, or follow-up.
- Identifies any remediation candidate for P554.

## Subproblems
- none

## Results
- R561

## Latest Check
C597

## Bodies
- Problem: problems/P000/children/P005/children/P553/children/P563/children/P571/README.md
- Ticket T565: problems/P000/children/P005/children/P553/children/P563/children/P571/tickets/T565.md
- Result R561: problems/P000/children/P005/children/P553/children/P563/children/P571/results/R561.md
- Check C597: problems/P000/children/P005/children/P553/children/P563/children/P571/checks/C597.md

## Follow-ups
- none
