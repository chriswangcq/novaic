# P001: Make source defaults and docs non-conservative

Status: done
Parent: P000
Root: P000
Source Ticket: T000 (split)
Source Check: none
Package: problems/P000/children/P001
Body: problems/P000/children/P001/README.md
Ticket(s): T001

## Problem
The repository still presents the release-controller as dry-run by default in sample config or documentation. This creates drift from the desired clean operating model where staging branch releases execute for real unless explicitly requested as dry-run.

## Success Criteria
- `novaic-release-controller/config.sample.json` has `dry_run_default=false`.
- Tests expecting the sample config are updated.
- Documentation describes non-dry-run default staging execution and keeps prod promotion-only.
- Relevant tests and guards pass.

## Subproblems
- none

## Results
- R000

## Latest Check
C000

## Bodies
- Problem: problems/P000/children/P001/README.md
- Ticket T001: problems/P000/children/P001/tickets/T001.md
- Result R000: problems/P000/children/P001/results/R000.md
- Check C000: problems/P000/children/P001/checks/C000.md

## Follow-ups
- none
