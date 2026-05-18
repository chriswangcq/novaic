# Check: Shell screenshot BlobRef manifest coverage is direct

## Summary

Success. `R581` directly covers the shell-facing screenshot contract: screenshot bytes are uploaded to Blob Service, shell stdout contains a BlobRef artifact manifest, and raw screenshot base64 is absent.

## Evidence

- `R581` records scan and test artifacts:
  - `.complex-problems/L20260516-222011/tmp/p597/shell-cli-manifest-scan.txt`
  - `.complex-problems/L20260516-222011/tmp/p597/shell-cli-manifest-tests.txt`
- `novaic-cortex/tests/test_shell_capabilities_blob_contract.py:137-159` asserts `tool-output.v1`, `blob://runtime-artifact/`, display access, uploaded image bytes, and no raw base64/screenshot field in stdout.
- `novaic-cortex/tests/test_shell_capabilities_blob_contract.py:200-205` asserts help teaches BlobRef artifacts and not raw base64.
- `novaic-agent-runtime/tests/unit/task_queue/test_shell_output_contract.py:52-80` asserts runtime persists shell `llm_content` as `tool-output.v1` inside `tool-step-payload.v1`.

## Criteria Map

- Exact scans recorded: satisfied.
- BlobRef artifact manifest test cited: satisfied by the devicectl screenshot test.
- Raw base64 absence test cited: satisfied by lines 158-159 and help text assertions.
- Follow-up if missing: not needed.

## Execution Map

- `T588` executed read-only inventory plus focused pytest.
- Focused command passed: `3 passed in 0.69s`.
- No code changes were needed.

## Stress Test

- Plausible failure mode: device screenshot command prints the raw `"screenshot"` base64 returned by device service.
- Covered by `test_devicectl_hd_screenshot_uploads_image_and_prints_tool_output_artifact`, which feeds fake base64-capable device output and asserts the encoded image and `"screenshot":` field are absent from stdout.

## Residual Risk

- This child covers shell CLI only. Display handler and Cortex projection contracts remain in sibling children.

## Result IDs

- R581
