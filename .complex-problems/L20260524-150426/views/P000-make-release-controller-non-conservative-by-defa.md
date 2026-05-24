# P000: Make release-controller non-conservative by default

Status: done
Parent: none
Root: P000
Source Ticket: none (none)
Source Check: none
Package: problems/P000
Body: problems/P000/README.md
Ticket(s): T000

## Problem
The centered release-controller is deployed and proven, but it is still configured conservatively with `dry_run_default=true`. The desired operating state is clean and non-conservative: branch-triggered releases should default to real execution, not observation-only dry runs, while production remains protected by promotion-only rules.

## Success Criteria
- Repository defaults and documentation no longer describe the controller as dry-run by default for normal operation.
- Release-controller sample config uses `dry_run_default=false`.
- API-host runtime config uses `dry_run_default=false`.
- The running release-controller is restarted or redeployed so the runtime policy is active.
- A trigger without an explicit `dry_run` field plans and executes with `dry_run=false`.
- Staging release health checks pass after the default non-dry-run execution.
- Production remains protected: branch rules still do not auto-deploy to `prod`.
- The ledger closes with validation/render/status.

## Subproblems
- P001: Make source defaults and docs non-conservative
- P002: Activate non-conservative runtime policy on API host

## Results
- R002

## Latest Check
C002

## Bodies
- Problem: problems/P000/README.md
- Ticket T000: problems/P000/tickets/T000.md
- Result R002: problems/P000/results/R002.md
- Check C002: problems/P000/checks/C002.md

## Follow-ups
- none
