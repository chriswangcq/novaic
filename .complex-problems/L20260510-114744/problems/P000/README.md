# Make Cortex depend only on sandbox service SDK

## Problem

The current sandbox extraction still lets Cortex import `sandbox_core`, which mixes service client contracts with daemon-internal execution substrate. That violates the desired final architecture: Cortex should call sandboxd through a thin service boundary, while `sandbox_core` remains daemon/internal infrastructure for process execution and mount namespace handling.

## Success Criteria

- A new independent `novaic-sandbox-sdk` package owns sandboxd wire DTOs and HTTP client only.
- Cortex imports `sandbox_sdk`, not `sandbox_core`.
- Sandbox service imports `sandbox_sdk` for HTTP contracts and `sandbox_core` for internal execution substrate.
- `sandbox_core` no longer contains service client or wire-contract modules.
- Startup, deploy, and test scripts explicitly sync/include/test `novaic-sandbox-sdk`.
- Source scans show no `sandbox_core` import under `novaic-cortex`.
