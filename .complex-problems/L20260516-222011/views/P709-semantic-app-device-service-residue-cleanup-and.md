# P709: Semantic/app/device service residue cleanup and verification

Status: done
Parent: P697
Root: P000
Source Ticket: T698 (split)
Source Check: none
Package: problems/P000/children/P007/children/P668/children/P673/children/P684/children/P697/children/P709
Body: problems/P000/children/P007/children/P668/children/P673/children/P684/children/P697/children/P709/README.md
Ticket(s): T742

## Problem
Scan cross-service docs/scripts/code for stale or misleading claims that collapse Cortex, Gateway, Business, Device, Queue, Runtime, Blob, LogicalFS, Sandboxd, or display responsibilities. Patch safe active-surface residue and record follow-ups for unsafe broad changes.

## Success Criteria
- Active vs stale/generated/historical references are classified.
- Safe active-surface misleading claims are patched.
- Broad or risky cleanup is split into follow-up problems instead of overreaching.
- Verification includes focused scans and relevant lint/tests for touched files.

## Subproblems
- P749: Cross-service semantic residue discovery and classification
- P750: Safe active-surface semantic residue remediation
- P751: Cross-service semantic residue verification

## Results
- R807

## Latest Check
C856

## Bodies
- Problem: problems/P000/children/P007/children/P668/children/P673/children/P684/children/P697/children/P709/README.md
- Ticket T742: problems/P000/children/P007/children/P668/children/P673/children/P684/children/P697/children/P709/tickets/T742.md
- Result R807: problems/P000/children/P007/children/P668/children/P673/children/P684/children/P697/children/P709/results/R807.md
- Check C856: problems/P000/children/P007/children/P668/children/P673/children/P684/children/P697/children/P709/checks/C856.md

## Follow-ups
- none
