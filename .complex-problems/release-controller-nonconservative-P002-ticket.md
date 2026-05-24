# Activate API-host non-dry-run runtime default

## Problem Definition

The source default is non-conservative, but the live API-host release-controller must be switched to `dry_run_default=false`, restarted/redeployed, and verified with an omitted-`dry_run` release trigger.

## Proposed Solution

- Update `/opt/novaic/release-controller/config.json` to `dry_run_default=false`.
- Commit and push the source default/doc changes from P001.
- Build and deploy a new release-controller image from the latest main commit.
- Verify runtime config and controller health.
- Trigger `main` without a `dry_run` field and confirm the resulting execution reports `dry_run=false`.
- Verify staging API and Factory health.
- Confirm branch rules still do not target `prod`.

## Acceptance Criteria

- API-host runtime config is explicitly false.
- Running controller has been restarted or redeployed after the policy change.
- Omitted-`dry_run` trigger executes non-dry-run and succeeds.
- Staging API and Factory return 200.
- Prod remains promotion-only.

## Verification Plan

- Inspect remote config JSON.
- Inspect running controller health/status.
- Inspect trigger execution result.
- Run staging health checks.
- Review branch rules.

## Risks

- A main branch change may be picked up by autonomous polling and deploy staging automatically; that is expected under the requested non-conservative policy.

## Assumptions

- The current staging release path remains healthy from the previous closure work.
