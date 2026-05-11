# Wrap devicectl artifact outputs with Blob-backed tool-output.v1

## Problem Definition

`devicectl hd screenshot` and `devicectl hd file-pull` can receive large base64 payloads from the device service and print them through shell stdout. That violates the CLI Blob contract: binary artifacts must be uploaded to Blob Service and represented in stdout as a small manifest.

## Proposed Solution

Update the generated `devicectl` CLI script in `novaic-cortex/novaic_cortex/shell_capabilities.py` so artifact-producing HD commands decode base64 payloads, upload bytes to Blob Service under the valid `runtime-artifact` namespace, and print a `tool-output.v1` artifact manifest. Keep non-artifact HD commands on their existing JSON/text path. Add focused tests with fake device and Blob services.

## Acceptance Criteria

- `devicectl hd screenshot` stdout contains `tool-output.v1` and a Blob URI, not raw screenshot base64.
- `devicectl hd file-pull` stdout contains `tool-output.v1` and a Blob URI, not raw file base64.
- Uploaded Blob namespace is `runtime-artifact`, matching the shared Blob contract.
- Non-artifact `devicectl hd` commands keep returning ordinary diagnostics.
- Tests verify uploaded bytes and absence of raw artifact fields in stdout.

## Verification Plan

- Compile generated `agentctl`, `cortex`, and `devicectl` scripts.
- Run the new `novaic-cortex` Blob contract tests.
- Run nearby tool-output and Blob contract tests to catch schema drift.
- Scan shell capability code for remaining raw artifact stdout paths.

## Risks

- Blob Service API assumptions may be slightly wrong; tests should model the current multipart contract.
- Existing callers may expect the old raw base64 JSON shape.
- Missing Blob environment configuration should fail clearly instead of silently falling back.

## Assumptions

- `runtime-artifact` is the correct contract namespace for runtime-generated CLI artifacts.
- Device service still returns screenshot/file-pull data as base64 JSON.
- Local fallback storage is intentionally not allowed.
