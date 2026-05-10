# Result: Sandbox SDK Boundary Split

## Summary

Implemented the final sandbox dependency boundary: Cortex now depends only on the thin `sandbox_sdk` service contract/client, while `sandbox_core` is daemon-internal execution substrate used by sandboxd.

## Done

- Created `novaic-sandbox-sdk/sandbox_sdk` with:
  - `SandboxExecSpec`, `SandboxExecResult`, `SandboxBindMount`
  - `SandboxdExecuteRequest`, `SandboxdExecuteResponse`
  - `SandboxdClient`
- Removed `sandbox_core/client.py` and `sandbox_core/contracts.py`.
- Updated `sandbox_core` exports and tests so core contains only process/mount/filesystem substrate.
- Updated sandboxd service to translate SDK request DTOs into core `ProcessSpec` at the HTTP boundary.
- Updated Cortex to import `sandbox_sdk` only, not `sandbox_core`.
- Removed Cortex local process fallback; unconfigured shell execution now fails explicitly with a sandboxd-required error.
- Changed Cortex LogicalFS capability semantics so execution capability belongs to sandboxd, not local Cortex host inspection.
- Updated `deploy`, `scripts/start.sh`, and `scripts/run_all_tests.sh` to sync/include/test `novaic-sandbox-sdk`.

## Verification

- `PYTHONPATH=novaic-sandbox-sdk pytest -q novaic-sandbox-sdk/tests`: 3 passed.
- `PYTHONPATH=novaic-sandbox-core pytest -q novaic-sandbox-core/tests`: 6 passed.
- `PYTHONPATH=novaic-sandbox-sdk:novaic-sandbox-core:novaic-common:novaic-sandbox-service pytest -q novaic-sandbox-service/tests`: 5 passed.
- `PYTHONPATH=novaic-sandbox-sdk:novaic-common:novaic-cortex pytest -q novaic-cortex/tests/test_sandboxd_wiring.py novaic-cortex/tests/test_sandbox_requires_mount_namespace.py`: 3 passed.
- `PYTHONPATH=novaic-sandbox-sdk:novaic-common:novaic-cortex pytest -q novaic-cortex/tests`: 344 passed, 41 skipped.
- `PYTHONPATH=novaic-common:novaic-sandbox-sdk pytest -q novaic-common/tests`: 139 passed.
- Local sandboxd live smoke passed through SDK-shaped `/v1/execute` request.
- `./scripts/run_all_tests.sh`: 15/15 checks passed, 0 failed.
- Residue scans showed no `sandbox_core` imports under `novaic-cortex` and no old `SandboxdProcessRunner` / core client-contract conversion APIs.

## Gaps

- None found in the executed checks.
