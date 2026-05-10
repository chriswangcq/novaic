# Shell capability environment transport implemented

## Summary

Added an explicit Runtime-to-Cortex capability environment transport for shell commands. This gives sandbox commands the minimum context needed to call Runtime/Business-adjacent capabilities without relying on hidden globals.

## Done

- `CortexBridge.shell_exec()` now accepts `capability_env` and sends it in `/v1/internal/shell`.
- `_exec_shell()` builds explicit env values from handler dependencies and `ServiceConfig`.
- Cortex `InternalShellRequest` accepts `env`.
- `Cortex.tool_shell()` and `Sandbox.exec()` accept the env mapping.
- Sandbox filters env keys through a local allowlist before exposing them to the process.
- Added/updated tests for bridge payload and sandbox allowlist behavior.

## Verification

- Ran `python -m pytest tests/test_shell_capability_runtime.py tests/test_sandbox_sync.py -q` in `novaic-cortex`.
- Result: `5 passed, 1 skipped`.
- Ran `python -m pytest tests/unit/task_queue/test_shell_output_contract.py tests/test_runtime_explicit_contracts.py -q` in `novaic-agent-runtime`.
- Result: `12 passed`.

## Residual Risk

- This ticket only transports explicit context. It does not yet implement the `agentctl im ...` command behavior itself.
