# Make release-controller non-conservative by default

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
