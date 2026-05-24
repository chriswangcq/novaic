# Activate non-conservative runtime policy on API host

## Problem

Even if repository defaults are corrected, the running API-host release-controller must use `dry_run_default=false` and prove that omitted `dry_run` means real execution.

## Success Criteria

- `/opt/novaic/release-controller/config.json` on the API host has `dry_run_default=false`.
- The running release-controller has been restarted or redeployed after the config change.
- A `main` trigger without a `dry_run` field executes with `dry_run=false`.
- The omitted-policy trigger succeeds through staging deploy and smoke, or records a precise blocker that is then closed by follow-up.
- Staging API and Factory health checks return 200 after the run.
- Branch rules still do not auto-deploy to `prod`.
