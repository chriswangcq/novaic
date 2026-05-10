# Cortex active path wired to sandboxd runner port

## Summary

Refactored Cortex shell execution to use an explicit process-runner dependency and pass a declarative mount plan through `ProcessSpec`. The Cortex server entrypoint now requires `--sandboxd-url` and installs `SandboxdProcessRunner` for API-created Cortex instances.

## Done

- Added `MountNamespaceLogicalFS.process_mount_plan`.
- Updated `ShellExecutionOrchestrator` to pass raw command + `BindMountPlan` instead of a pre-wrapped command.
- Updated `Sandbox` and `Cortex` to accept explicit process-runner dependencies.
- Added an API-level sandbox runner factory and used it in API-created Cortex instances.
- Updated `main_cortex` to require `--sandboxd-url` and install a `SandboxdProcessRunner`.
- Added tests proving raw-command/mount-plan separation and API internal shell runner injection.

## Evidence

- `PYTHONPATH=novaic-common:novaic-cortex pytest -q novaic-cortex/tests/test_sandboxd_wiring.py novaic-cortex/tests/test_sandbox_requires_mount_namespace.py` -> `3 passed in 0.30s`.
- `PYTHONPATH=novaic-common:novaic-cortex pytest -q novaic-cortex/tests/test_sandboxd_wiring.py novaic-cortex/tests/test_sandbox_requires_mount_namespace.py novaic-cortex/tests/test_incremental_sync.py` -> `3 passed, 7 skipped in 0.23s`.
- `PYTHONPATH=novaic-common:novaic-cortex python -m novaic_cortex.main_cortex --help | rg -n "sandboxd-url|blob-service-url|redis-url"` shows `--sandboxd-url`.
- `rg -n "process_command\\(|build_bind_mount_command|unshare --mount" novaic-cortex/novaic_cortex/sandbox.py novaic-cortex/novaic_cortex/api.py novaic-cortex/novaic_cortex/main_cortex.py || true` -> no matches.

## Residual Risk

- `logical_fs.py` still contains the old `process_command` wrapper for now; it is no longer used by `sandbox.py` and is scheduled for explicit cleanup in P005.
