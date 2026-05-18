# P623 SDK API/Wire Classification

## Package Boundary

`novaic-sandbox-sdk` is a thin HTTP client/DTO package. It imports stdlib `urllib`/`json` and package DTOs; it does not import `subprocess`, sandbox service/core, Cortex, LogicalFS, or Blob code.

## Intended Hits

- `sandbox_sdk/client.py` posts JSON to `base_url.rstrip("/") + "/v1/execute"` via `urllib.request.urlopen`; this is the intended sandboxd service boundary.
- `sandbox_sdk/contracts.py` encodes/decodes `stdout_b64` and `stderr_b64` as bytes for the private sandboxd wire contract. This package returns bytes, not LLM history text.
- `SandboxBindMount` and request `mount` fields are DTO fields only; SDK does not create mounts.

## Test/Fixture Hits

- `tests/test_sandbox_sdk.py` uses `/tmp/root`, `/cortex`, `/cortex/rw`, and `http://sandboxd.local` as fixtures.
- The test monkeypatches `urllib.request.urlopen` to assert request mapping and response decoding.

## Risky Residue

None found in active SDK source. No subprocess/process execution, no local fallback, no host capability inspection, and no sandbox core/Cortex imports were found.

## Coverage

- `novaic-sandbox-sdk/tests/test_sandbox_sdk.py`: 3 passed.
