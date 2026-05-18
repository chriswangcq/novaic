# P766: App resource copy residue discovery

Status: done
Parent: P757
Root: P000
Source Ticket: T752 (split)
Source Check: none
Package: problems/P000/children/P007/children/P668/children/P673/children/P684/children/P697/children/P709/children/P749/children/P753/children/P757/children/P766
Body: problems/P000/children/P007/children/P668/children/P673/children/P684/children/P697/children/P709/children/P749/children/P753/children/P757/children/P766/README.md
Ticket(s): T757

## Problem
Scan app-bundled resource/generated copies that mirror Sandbox or VMuse code for stale residue that could ship even if source repos are clean. This belongs under P757 because generated/resource copies have previously duplicated active VMuse code and can preserve removed imports or media behavior.

## Success Criteria
- Relevant app resource/generated copies are discovered and scanned with bounded commands.
- Suspicious hits are classified as generated mirror, stale copied residue, or unrelated app resource vocabulary.
- Exact remediation candidates are listed, or absence is explicitly recorded.
- No product code is modified in this discovery child.

## Subproblems
- none

## Results
- R747

## Latest Check
C793

## Bodies
- Problem: problems/P000/children/P007/children/P668/children/P673/children/P684/children/P697/children/P709/children/P749/children/P753/children/P757/children/P766/README.md
- Ticket T757: problems/P000/children/P007/children/P668/children/P673/children/P684/children/P697/children/P709/children/P749/children/P753/children/P757/children/P766/tickets/T757.md
- Result R747: problems/P000/children/P007/children/P668/children/P673/children/P684/children/P697/children/P709/children/P749/children/P753/children/P757/children/P766/results/R747.md
- Check C793: problems/P000/children/P007/children/P668/children/P673/children/P684/children/P697/children/P709/children/P749/children/P753/children/P757/children/P766/checks/C793.md

## Follow-ups
- none
