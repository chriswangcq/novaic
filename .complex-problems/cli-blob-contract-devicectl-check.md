# devicectl artifact Blob contract check

## Summary

P002 is solved by R001. The two artifact-producing `devicectl` commands have direct code coverage and now produce Blob-backed `tool-output.v1` manifests instead of raw base64 stdout.

## Evidence

- Generated capability scripts compiled successfully, proving the format-string-generated CLI remains syntactically valid.
- `tests/test_shell_capabilities_blob_contract.py` exercises `devicectl hd screenshot` and `devicectl hd file-pull` against fake device and Blob services.
- The test run completed with `21 passed`, including adjacent tool-output projection, tool schema, and Blob payload client tests.

## Criteria Map

- Screenshot stdout contains manifest and Blob URI: covered by `test_devicectl_hd_screenshot_uploads_image_and_prints_tool_output_artifact`.
- File-pull stdout contains manifest and Blob URI: covered by `test_devicectl_hd_file_pull_uploads_file_and_prints_tool_output_artifact`.
- Namespace is contract-valid `runtime-artifact`: both tests assert recorded upload namespace.
- Non-artifact HD commands preserved: wrapper dispatch only intercepts `screenshot` and `file-pull`; all other subcommands return original result.
- Raw artifact fields absent: tests assert stdout lacks `"screenshot":` and `"data":`.

## Execution Map

- R001 changed `novaic-cortex/novaic_cortex/shell_capabilities.py`.
- R001 added `novaic-cortex/tests/test_shell_capabilities_blob_contract.py`.
- Verification command: `PYTHONPATH=../novaic-common:../novaic-logicalfs:../novaic-sandbox-sdk:. pytest -q tests/test_shell_capabilities_blob_contract.py tests/test_tool_output_projection.py tests/test_tool_schemas_limits.py tests/test_blob_payload_client.py`.

## Stress Test

- Fake service tests verify actual uploaded bytes match decoded upstream base64 bytes, not just the presence of a URI.
- Tests reject the concrete previously observed failure mode: a huge base64 `screenshot` field appearing in shell tool stdout.

## Residual Risk

- Existing callers that depended on raw JSON screenshot/file-pull fields will need to consume the manifest shape. This is intentional contract enforcement, not a blocker.
- Full CLI residual cleanup is handled by P003/P004 and does not block P002.

## Result IDs

- R001
