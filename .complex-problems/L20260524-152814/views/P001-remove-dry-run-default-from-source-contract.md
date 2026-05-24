# P001: Remove dry_run_default from source contract

Status: done
Parent: P000
Root: P000
Source Ticket: T000 (split)
Source Check: none
Package: problems/P000/children/P001
Body: problems/P000/children/P001/README.md
Ticket(s): T001

## Problem
Active release-controller code, tests, sample config, and docs still expose `dry_run_default`. Remove this global switch so the only dry-run behavior is an explicit request field.

## Success Criteria
- `ControllerConfig` has no `dry_run_default` field, parsing, validation, or serialized output.
- `ReleasePlanner` resolves omitted `dry_run` to execution and explicit `dry_run=true` to simulation.
- Sample config and docs describe the clean contract without global dry-run defaults.
- Tests cover omitted `dry_run` executing by default and explicit dry-run still skipping command execution.
- `rg dry_run_default` returns no matches in active release-controller/docs/deploy/CI paths after this child is complete.

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
