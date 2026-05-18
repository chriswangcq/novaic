# P568: Cortex Stable Path Compatibility Residue Classification

Status: done
Parent: P562
Root: P000
Source Ticket: T558 (split)
Source Check: none
Package: problems/P000/children/P005/children/P553/children/P562/children/P568
Body: problems/P000/children/P005/children/P553/children/P562/children/P568/README.md
Ticket(s): T561

## Problem
Classify Cortex occurrences of old temp backing paths, `/tmp/novaic-cortex-sandbox-*`, `/cortex/ro` `/cortex/rw` path compatibility, and path adapter residue. This belongs under P562 because path leakage previously caused runtime confusion and shell timeouts.

## Success Criteria
- Records exact Cortex scan commands and outputs for temp/stable path compatibility terms.
- Reads relevant code slices with line references.
- Separates intended guardrails from risky compatibility fallback.
- Identifies any remediation candidate for P554.

## Subproblems
- P569: P568 Reproducible Scan Command Manifest

## Results
- R557

## Latest Check
C593

## Bodies
- Problem: problems/P000/children/P005/children/P553/children/P562/children/P568/README.md
- Ticket T561: problems/P000/children/P005/children/P553/children/P562/children/P568/tickets/T561.md
- Result R557: problems/P000/children/P005/children/P553/children/P562/children/P568/results/R557.md
- Check C591: problems/P000/children/P005/children/P553/children/P562/children/P568/checks/C591.md
- Check C593: problems/P000/children/P005/children/P553/children/P562/children/P568/checks/C593.md

## Follow-ups
- P569: P568 Reproducible Scan Command Manifest
