# P000: Remove release-controller transitional dry-run paths and stale work-package residue

Status: done
Parent: none
Root: P000
Source Ticket: none (none)
Source Check: none
Package: problems/P000
Body: problems/P000/README.md
Ticket(s): T000

## Problem
The release controller still contains a transitional global `dry_run_default` configuration path. That path makes runtime behavior depend on a hidden controller-wide switch instead of the explicit request contract. It also leaves misleading docs and examples that future humans or agents may copy.

The workspace also contains visible stale problem-package residue from earlier implementation phases. This cleanup must preserve useful committed history and current ledgers, but remove or quarantine files that are no longer part of the current product path.

## Success Criteria
- `dry_run_default` no longer exists in release-controller source, sample config, tests, CI guards, deploy docs, or architecture docs.
- Omitted `dry_run` means real execution for branch release, poll, promotion, and rollback planning; explicit `dry_run=true` remains the only dry-run behavior.
- Tests prove omitted `dry_run` executes by default and explicit `dry_run=true` remains a simulation path.
- Runtime config on the API host no longer contains `dry_run_default`.
- A cleaned release-controller image is built, pushed, deployed, and verified healthy.
- A trigger without `dry_run` performs a real staging release, while an explicit `dry_run=true` trigger does not update release pointers.
- Stale local work-package/path residue is inventoried and only safe-to-remove residue is deleted or left with an explicit reason.
- Relevant tests, CI guards, ledger validation/rendering, and runtime smoke checks pass.

## Subproblems
- P001: Remove dry_run_default from source contract
- P002: Deploy and verify cleaned release-controller runtime
- P003: Clean stale workspace path residue safely

## Results
- R003

## Latest Check
C003

## Bodies
- Problem: problems/P000/README.md
- Ticket T000: problems/P000/tickets/T000.md
- Result R003: problems/P000/results/R003.md
- Check C003: problems/P000/checks/C003.md

## Follow-ups
- none
