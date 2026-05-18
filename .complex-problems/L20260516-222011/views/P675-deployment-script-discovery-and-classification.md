# P675: Deployment script discovery and classification

Status: done
Parent: P672
Root: P000
Source Ticket: T669 (split)
Source Check: none
Package: problems/P000/children/P007/children/P668/children/P672/children/P675
Body: problems/P000/children/P007/children/P668/children/P672/children/P675/README.md
Ticket(s): T670

## Problem
Find repository scripts/configs related to deployment, startup, supervision, smoke, and health checks. Classify high-signal candidates as active, test-only, generated, or historical so later remediation does not edit the wrong surface.

## Success Criteria
- Reproducible search artifacts list candidate script/config files.
- High-signal active scripts are identified with evidence pointers.
- Historical/test-only/generated candidates are explicitly separated.
- No code changes are made except writing ledger evidence artifacts.

## Subproblems
- P677: Deployment script candidate scan artifacts
- P678: Deployment script candidate classification

## Results
- R668

## Latest Check
C710

## Bodies
- Problem: problems/P000/children/P007/children/P668/children/P672/children/P675/README.md
- Ticket T670: problems/P000/children/P007/children/P668/children/P672/children/P675/tickets/T670.md
- Result R668: problems/P000/children/P007/children/P668/children/P672/children/P675/results/R668.md
- Check C710: problems/P000/children/P007/children/P668/children/P672/children/P675/checks/C710.md

## Follow-ups
- none
