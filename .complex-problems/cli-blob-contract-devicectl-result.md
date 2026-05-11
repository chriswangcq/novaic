# devicectl artifact commands now emit Blob manifests

## Summary

Implemented Blob-backed artifact output for `devicectl hd screenshot` and `devicectl hd file-pull` in the generated shell capability CLI. Both commands now decode upstream base64 data, upload bytes to Blob Service using the `runtime-artifact` namespace, and print a compact `tool-output.v1` manifest instead of raw base64 JSON.

## Done

- Added Blob multipart upload helper logic to the generated CLI script in `novaic-cortex/novaic_cortex/shell_capabilities.py`.
- Wrapped `devicectl hd screenshot` output into an image artifact manifest with display access metadata.
- Wrapped `devicectl hd file-pull` output into a binary artifact manifest with file metadata.
- Kept non-artifact `devicectl hd` subcommands on the ordinary JSON diagnostics path.
- Added fake device and Blob service tests in `novaic-cortex/tests/test_shell_capabilities_blob_contract.py`.

## Verification

- Generated `agentctl`, `cortex`, and `devicectl` scripts compiled successfully with `py_compile`.
- Ran `PYTHONPATH=../novaic-common:../novaic-logicalfs:../novaic-sandbox-sdk:. pytest -q tests/test_shell_capabilities_blob_contract.py tests/test_tool_output_projection.py tests/test_tool_schemas_limits.py tests/test_blob_payload_client.py`.
- Result: `21 passed in 1.27s`.
- Tests assert stdout does not contain raw `"screenshot":` or `"data":` fields for the artifact commands.

## Known Gaps

- This ticket only covers `devicectl` artifact-producing commands. Agentctl/cortex CLI audit and global residual cleanup are tracked in sibling problems P003/P004.
- Deployment was not performed in this ticket.

## Artifacts

- `novaic-cortex/novaic_cortex/shell_capabilities.py`
- `novaic-cortex/tests/test_shell_capabilities_blob_contract.py`
