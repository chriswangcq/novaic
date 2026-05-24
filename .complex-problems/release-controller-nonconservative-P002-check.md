# P002 Check: Success

## Summary

P002 is solved: the live API-host release-controller is operating with `dry_run_default=false`, and omitted-`dry_run` triggers plus autonomous polling perform real staging releases.

## Evidence

- API-host runtime config reports `dry_run_default=false` and `polling_enabled=true`.
- Running release-controller image is deployed from the latest non-conservative source path.
- Manual trigger without `dry_run` produced run `20260524-071356-main-312494256d5a` with execution `dry_run=false` and status `succeeded`.
- Autonomous polling produced real successful staging release runs after the switch:
  - `20260524-071042-main-dad56939ae39`
  - `20260524-071515-main-312494256d5a`
- Final branch head is `312494256d5ae0d3d5642b430a3cb231230464c8`.
- Final staging API, staging Factory, staging HTTPS, and controller health checks all returned 200.

## Criteria Map

- Runtime config false -> `/opt/novaic/release-controller/config.json` inspection.
- Running controller restarted/redeployed -> digest `sha256:078ab06205b3bdc51d61d32b8e3dc8752d94fb41c516dbf90fe0229e7ce1b2dc` deployed and healthy.
- Omitted `dry_run` executes non-dry-run -> manual run `20260524-071356-main-312494256d5a`, `dry_run=false`.
- Staging health passes -> API, Factory, public HTTPS, and controller health checks 200.
- Prod remains promotion-only -> branch rules still have no prod auto-deploy rule.

## Execution Map

- T002 -> R001 updated remote runtime config, committed/pushed source changes, deployed latest controller image, ran omitted-`dry_run` trigger, observed autonomous polling, and verified health.

## Stress Test

- Failure mode: runtime config stays conservative despite source default. Rejected by direct API-host config inspection.
- Failure mode: omitted `dry_run` still defaults to dry-run. Rejected by trigger execution reporting `dry_run=false`.
- Failure mode: autonomous polling still only observes. Rejected by successful poll-triggered staging release and updated release pointer.
- Failure mode: prod accidentally becomes branch-triggered. Rejected by branch rules inspection.
- Failure mode: deploy script reports false negative during controller startup. Fixed by bounded release-controller health wait.

## Residual Risk

Autonomous polling now really deploys staging for matching branch head changes. That is the intended non-conservative operating state, not a blocking risk.

## Result IDs

- R001

## Blocking Gaps

- none
