# Extract sandbox substrate out of common into sandbox-core final shape

## Problem

`common/sandbox` is still a halfway architecture: the sandbox substrate is generic infrastructure but lives under the broad `novaic-common` package. The desired final shape is an independent base package/server boundary where Cortex and sandboxd depend on `sandbox_core`, while `novaic-common` keeps configuration/shared app contracts only.

## Success Criteria

- A new independent `novaic-sandbox-core` package owns sandbox contracts, client, process runner, mount namespace, and filesystem helpers.
- `novaic-cortex` and `novaic-sandbox-service` import `sandbox_core`, not `common.sandbox`.
- `novaic-common/common/sandbox` is physically removed.
- Tests move with the new package and pass.
- Start/deploy/test scripts include `novaic-sandbox-core` explicitly in PYTHONPATH/sync/test matrix.
- Source scans show no `common.sandbox` import residue.
