# Cortex uses sandboxd on the active server path

## Problem

Writing sandboxd is not enough; the running Cortex API path must use the sandboxd client for shell execution. Direct in-process execution may remain as an explicit unit-test adapter, but production server startup must wire sandboxd.

## Success Criteria

- Cortex `Sandbox` accepts an explicit process-runner dependency.
- Runtime/API construction uses an injected sandboxd client on the server path.
- `main_cortex` or equivalent startup requires/configures the sandboxd URL.
- Tests prove the API/runtime active path can use an injected runner and that shell commands are no longer pre-wrapped in Cortex when a mount plan is available.
