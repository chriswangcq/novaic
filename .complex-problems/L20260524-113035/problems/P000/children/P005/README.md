# Deploy release-controller to API host and verify

## Problem

After implementation, deploy the controller to the API host and verify it can observe the configured branch and report status without disrupting prod/staging runtime.

## Success Criteria

- Release-controller container runs on the API host.
- `/health` and `/v1/status` return healthy JSON.
- Controller can see the configured git branch head.
- A dry-run trigger produces a recorded run plan without changing prod/staging service containers.
- Existing prod/staging backend health remains green after deployment.
