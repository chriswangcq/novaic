# P012: Add release-controller branch head polling

Status: done
Parent: P002
Root: P000
Source Ticket: none (none)
Source Check: C006
Package: problems/P000/children/P002/children/P012
Body: problems/P000/children/P002/children/P012/README.md
Ticket(s): T008

## Problem
The release-controller core service needs a polling component that reads configured branch rules, checks branch heads, records changed heads, skips unchanged heads, and triggers the existing planner/runner path for eligible non-prod branch releases.

## Success Criteria
- A poller module can list configured branch patterns and resolve concrete branch heads from git.
- Branch head state is persisted in `branch-heads.json`.
- Unchanged branch heads are skipped without creating duplicate release runs.
- Changed `main` and `preview/*` heads can create release plans through the existing planner.
- `release/*` heads can create candidate-only plans through the existing planner.
- Poll-triggered execution cannot target prod.
- Unit tests cover changed head, unchanged head, and unmatched branch behavior without network access.

## Subproblems
- none

## Results
- R007

## Latest Check
C007

## Bodies
- Problem: problems/P000/children/P002/children/P012/README.md
- Ticket T008: problems/P000/children/P002/children/P012/tickets/T008.md
- Result R007: problems/P000/children/P002/children/P012/results/R007.md
- Check C007: problems/P000/children/P002/children/P012/checks/C007.md

## Follow-ups
- none
