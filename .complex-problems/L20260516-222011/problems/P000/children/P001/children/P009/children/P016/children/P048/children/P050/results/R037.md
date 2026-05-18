# Result: Media CLI Stdout Contract Audit

## Summary

The active Cortex shell `devicectl hd screenshot` and `devicectl hd file-pull` CLI paths already comply with the manifest contract. They decode lower-level device base64 internally, upload bytes to Blob Service, and print concise `tool-output.v1` JSON containing blob/artifact metadata instead of raw media bytes.

## Done

- Inspected `novaic-cortex/novaic_cortex/shell_capabilities.py`:
  - `_wrap_hd_screenshot` removes the device `screenshot` field from diagnostics and emits an image artifact with `blob://runtime-artifact/...`.
  - `_wrap_hd_file_pull` removes the lower-level `data` field from diagnostics and emits a binary artifact with `blob://runtime-artifact/...`.
  - `_devicectl_hd` routes `screenshot` and `file-pull` through `_wrap_hd_result` before printing JSON.
- Inspected `novaic-cortex/tests/test_shell_capabilities_blob_contract.py`:
  - screenshot test asserts `tool-output.v1`, image artifact URI, blob upload, no encoded image bytes in stdout, and no `"screenshot":` field in stdout.
  - file-pull test asserts `tool-output.v1`, binary artifact URI, blob upload, no encoded file bytes in stdout, and no `"data":` field in stdout.
- Ran focused Cortex tests for the CLI/blob contract.

## Verification

- `cd novaic-cortex && PYTHONPATH=.:../novaic-logicalfs:../novaic-sandbox-sdk pytest -q tests/test_shell_capabilities_blob_contract.py tests/test_tool_output_projection.py`
- Result: `8 passed in 1.24s`.

## Known Gaps

- None for the active Cortex shell CLI screenshot/file-pull contract.
- Display/LLM image projection and broader base64 regression guards remain intentionally scoped to sibling problems `P051` and `P053`.
- Lower-level device services may still use base64 as an internal transport shape; this ticket only requires the shell-facing CLI projection to prevent stdout/context leakage.

## Artifacts

- `novaic-cortex/novaic_cortex/shell_capabilities.py`
- `novaic-cortex/tests/test_shell_capabilities_blob_contract.py`
- `novaic-cortex/tests/test_tool_output_projection.py`
