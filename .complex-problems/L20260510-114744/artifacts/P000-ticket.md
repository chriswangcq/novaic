# Split sandbox SDK boundary from sandbox core substrate

## Problem Definition

Cortex currently imports `sandbox_core` for the sandboxd client, process DTOs, filesystem helpers, and mount namespace checks. This leaves the architecture ambiguous: `sandbox_core` is both the daemon-internal execution substrate and the cross-service API contract.

## Proposed Solution

Create `novaic-sandbox-sdk/sandbox_sdk` for wire-level sandboxd DTOs and HTTP client. Move the current client/contract responsibilities out of `sandbox_core`, keep only process/mount/filesystem substrate in `sandbox_core`, update sandboxd service to translate SDK requests into core process specs, and update Cortex so it imports only `sandbox_sdk` plus its own LogicalFS helpers.

## Acceptance Criteria

- `novaic-sandbox-sdk` contains the sandboxd client and request/response/spec DTOs.
- `novaic-cortex` has zero imports from `sandbox_core`.
- `novaic-sandbox-service` imports both `sandbox_sdk` and `sandbox_core` with a clear translation boundary.
- `sandbox_core/client.py` and `sandbox_core/contracts.py` are removed.
- Deployment/start/test scripts include `novaic-sandbox-sdk` explicitly.
- Tests and residue scans prove the active path is the SDK/service path, not the old core path.

## Verification Plan

- Run sandbox-sdk tests.
- Run sandbox-core tests.
- Run sandbox-service tests with sdk+core.
- Run Cortex sandboxd wiring and mount namespace tests with sdk and without core dependency.
- Run common tests touched by deployment/config.
- Run shell syntax checks and deploy fresh-smoke lint.
- Scan `novaic-cortex` for `sandbox_core` imports and the full repo for old core client/contracts residue.

## Risks

- Cortex unit tests may have relied on the old local `AsyncProcessRunner` fallback.
- Splitting DTO types can create accidental duplicate conversion logic unless the service boundary is explicit.

## Assumptions

- Cortex may depend on a thin sandbox service SDK because that is a service contract, not process execution substrate.
- Sandbox service may depend on both SDK and core because it is the boundary adapter from HTTP contract to local execution substrate.
