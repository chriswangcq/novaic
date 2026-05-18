# Remove Implicit Cortex API URL Defaults

## Problem Definition

Generated shell capability commands should receive an explicit `NOVAIC_API` from the runtime/service path. `Sandbox` and `MountNamespaceLogicalFS` still default the Cortex API URL to `http://localhost:19996`, which can hide missing service configuration.

## Proposed Solution

Make `cortex_api_url` an explicit constructor input for `MountNamespaceLogicalFS`, `Sandbox`, and `Cortex`. Pass it from the Cortex API/runtime construction boundary, with tests using explicit fake URLs. Preserve fail-closed behavior in generated shell commands when `NOVAIC_API` is missing.

## Acceptance Criteria

- No default `http://localhost:19996` remains in shell LogicalFS environment construction.
- Runtime/API construction passes the Cortex API URL explicitly.
- Tests and helpers pass explicit URLs.
- Focused tests for CLI config, shell capabilities, sandbox wiring, and mount namespace behavior pass.

## Verification Plan

Run `rg` for `localhost:19996`, `cortex_api_url`, `/tmp/.novaic_env`, and `NOVAIC_API is not configured`; run focused Cortex tests covering proxy boundary, shell capabilities, sandboxd wiring, and no-local-fallback guards.

## Risks

- Some tests instantiate `Sandbox`/`Cortex` directly and need explicit test URLs.
- The service entrypoint may need a clear explicit self-URL construction from host/port.

## Assumptions

- The Cortex server can construct its own explicit internal API URL from startup host/port.
