# Common sandboxd contract completed

## Summary

Implemented the shared sandboxd execution contract and client runner in `novaic-common`. `ProcessSpec` now carries an optional `BindMountPlan`, and `AsyncProcessRunner` applies that plan through the common mount namespace helper instead of requiring upstream command pre-wrapping.

## Done

- Added `common.sandbox.contracts` with `SandboxdExecuteRequest` and `SandboxdExecuteResponse`.
- Added byte-safe base64 response serialization for stdout/stderr.
- Added `common.sandbox.client.SandboxdProcessRunner` using the same `ProcessSpec` runner port.
- Exported the new contract/client types from `common.sandbox`.
- Added focused tests for process execution, timeout, bind mount command shape, request/response roundtrip, byte roundtrip, and client response mapping.

## Evidence

- `PYTHONPATH=novaic-common pytest -q novaic-common/tests/test_sandbox_infra.py` -> `9 passed in 1.08s`.
- `rg -n "novaic_cortex|novaic-business|business" novaic-common/common/sandbox novaic-common/tests/test_sandbox_infra.py || true` -> no matches.

## Residual Risk

- Cortex has not yet been migrated to pass mount plans instead of pre-wrapped commands; that is covered by the Cortex active-path child problem.
