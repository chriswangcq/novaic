# P805: App backend startup graph remediation

Status: done
Parent: P802
Root: P000
Source Ticket: T794 (split)
Source Check: none
Package: problems/P000/children/P007/children/P668/children/P673/children/P684/children/P697/children/P709/children/P750/children/P785/children/P802/children/P805
Body: problems/P000/children/P007/children/P668/children/P673/children/P684/children/P697/children/P709/children/P750/children/P785/children/P802/children/P805/README.md
Ticket(s): T796

## Problem
Apply the concrete backend startup graph fixes identified by the audit without creating source/generated divergence.

## Success Criteria
- Startup script variants and generated copies are synchronized or clearly marked dev-only.
- Port naming conflict is removed or clarified in code/config.
- Script expectations match committed resources.
- `bash -n` and targeted config scans pass.

## Subproblems
- P806: Packaged Blob Binary Contract Remediation
- P807: Dev Startup Port And Service URL Contract Remediation
- P808: VMuse Runtime URL Config Contract Remediation
- P809: Backend Startup Resource And Generated Copy Synchronization

## Results
- R791

## Latest Check
C839

## Bodies
- Problem: problems/P000/children/P007/children/P668/children/P673/children/P684/children/P697/children/P709/children/P750/children/P785/children/P802/children/P805/README.md
- Ticket T796: problems/P000/children/P007/children/P668/children/P673/children/P684/children/P697/children/P709/children/P750/children/P785/children/P802/children/P805/tickets/T796.md
- Result R791: problems/P000/children/P007/children/P668/children/P673/children/P684/children/P697/children/P709/children/P750/children/P785/children/P802/children/P805/results/R791.md
- Check C839: problems/P000/children/P007/children/P668/children/P673/children/P684/children/P697/children/P709/children/P750/children/P785/children/P802/children/P805/checks/C839.md

## Follow-ups
- none
