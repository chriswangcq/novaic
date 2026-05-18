# Explicit Cortex API URL for Shell LogicalFS Environment

## Problem

`Sandbox` and `MountNamespaceLogicalFS` still default `cortex_api_url` to `http://localhost:19996`, which is an implicit service URL fallback for generated shell capability commands. Even though it is not a local shell execution fallback, it can silently wire shell CLIs to the wrong API instead of requiring explicit runtime/service configuration.

## Success Criteria

- Removes `http://localhost:19996` as the default `cortex_api_url` in `Sandbox` and `MountNamespaceLogicalFS`.
- Passes the Cortex API URL explicitly from the runtime/API construction path and test helpers.
- Keeps shell capability commands fail-closed when `NOVAIC_API` is missing.
- Adds/updates regression tests proving no `/tmp/.novaic_env.json` or localhost fallback exists in CLI/shell capability paths.
