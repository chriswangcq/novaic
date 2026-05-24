# Deploy and verify cleaned release-controller runtime

## Problem

After the source contract is cleaned, the API host must run the cleaned controller and runtime config must not preserve the removed `dry_run_default` key.

## Success Criteria

- API-host `/opt/novaic/release-controller/config.json` has no `dry_run_default` key.
- A release-controller image from the cleaned source is built, pushed, deployed, and reported healthy.
- A trigger without `dry_run` performs real staging execution and records `dry_run=false`.
- A trigger with explicit `dry_run=true` remains simulation-only and does not update release pointers.
- Staging gateway, staging factory, and controller health checks pass after deployment.
