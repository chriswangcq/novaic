# Switch release-controller to real execution by default

## Problem Definition

The release-controller currently keeps `dry_run_default=true`, which makes automatic or omitted-policy triggers conservative even after the real staging release path was proven. The platform should be clean: staging branch releases default to real execution, while production remains protected by explicit promotion-only rules.

## Proposed Solution

- Update release-controller sample configuration to `dry_run_default=false`.
- Update architecture/runbook documentation to describe non-conservative default execution and the remaining production guard.
- Update API-host runtime config to `dry_run_default=false`.
- Restart or redeploy the running release-controller so it uses the new policy.
- Verify a trigger that omits `dry_run` executes as non-dry-run and completes staging release health checks.
- Confirm branch rules still cannot target `prod`.

## Acceptance Criteria

- Code/config defaults are set to non-dry-run for release-controller.
- Runtime config on API host is non-dry-run by default.
- Running controller uses the new runtime config.
- Omitted `dry_run` trigger produces `dry_run=false` execution.
- Staging API and Factory health checks pass after execution.
- Prod remains promotion-only.

## Verification Plan

- Run release-controller tests and relevant CI guards.
- Inspect API-host `/opt/novaic/release-controller/config.json`.
- Restart/redeploy release-controller and inspect status.
- POST `/v1/triggers` without `dry_run` for `main`.
- Verify the run result, command plan, staging health endpoints, and branch rules.

## Risks

- The omitted-dry-run trigger performs a real staging deployment; this is intended.
- If automatic polling observes a newer main commit after the switch, it may also perform a real staging deployment; that is the requested non-conservative behavior.

## Assumptions

- Production safety is enforced by branch rules and promotion APIs, not by global dry-run default.
