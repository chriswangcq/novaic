# Check: Sandbox SDK Boundary Split

## Criteria Map

- New independent `novaic-sandbox-sdk` package owns sandboxd DTOs and HTTP client only: success.
- Cortex imports `sandbox_sdk`, not `sandbox_core`: success.
- Sandbox service imports `sandbox_sdk` for HTTP contracts and `sandbox_core` for internal substrate: success.
- `sandbox_core/client.py` and `sandbox_core/contracts.py` removed: success.
- Startup/deploy/test scripts include `novaic-sandbox-sdk`: success.
- Source scans show no `sandbox_core` import under `novaic-cortex`: success.

## Evidence

- `novaic-sandbox-sdk/sandbox_sdk` contains `types.py`, `contracts.py`, and `client.py`.
- `novaic-sandbox-core/sandbox_core` contains only `filesystem.py`, `mount_namespace.py`, and `process.py` plus package exports.
- `rg -n "from sandbox_core|import sandbox_core|sandbox_core\\." novaic-cortex` returned no matches.
- `rg -n "SandboxdProcessRunner|from_process_spec|to_process_spec|from_process_result|to_process_result|sandbox_core\\.client|sandbox_core\\.contracts"` returned no matches.
- `./scripts/run_all_tests.sh` passed all 15 checks.
- Local sandboxd live smoke returned `exit_code=0`.

## Execution Map

- Cross-service SDK is the only dependency visible to Cortex.
- Sandboxd service is the only layer that bridges SDK DTOs into core execution substrate.
- Core execution substrate is no longer a client/contract package.

## Stress Test

- Full repository test runner passed after adding the SDK test lane.
- Cortex full test lane passed with `novaic-sandbox-core` absent from `PYTHONPATH`.
- Local sandboxd live smoke passed with `novaic-sandbox-sdk` and `novaic-sandbox-core` both explicit on `PYTHONPATH`.

## Residual Risk

No known active-path residue. Real shell integration tests are skipped unless explicit sandboxd integration is enabled, which matches the no-local-fallback architecture.

## Verdict

Success. The final dependency direction is now Cortex -> sandbox SDK -> sandboxd service -> sandbox core.
