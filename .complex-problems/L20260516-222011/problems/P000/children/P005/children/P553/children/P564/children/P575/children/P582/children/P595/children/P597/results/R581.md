# Result: Shell screenshot BlobRef manifest tests inventoried

## Summary

Shell-facing screenshot output has direct regression coverage. The tests prove `devicectl hd screenshot` uploads bytes to Blob Service, prints a `tool-output.v1` artifact manifest with a BlobRef/display access hint, and omits raw screenshot base64 from stdout.

## Done

- Recorded scan output in `.complex-problems/L20260516-222011/tmp/p597/shell-cli-manifest-scan.txt`.
- Scan command recorded:
  - `rg -n 'devicectl|hd screenshot|tool-output\\.v1|runtime-artifact|base64|screenshot|artifact' -S novaic-agent-runtime/tests novaic-sandbox-service/tests novaic-sandbox-sdk/tests novaic-business/tests`
  - `nl -ba novaic-cortex/tests/test_shell_capabilities_blob_contract.py | sed -n '1,260p'`
  - `nl -ba novaic-agent-runtime/tests/unit/task_queue/test_shell_output_contract.py | sed -n '1,220p'`
- Cited `novaic-cortex/tests/test_shell_capabilities_blob_contract.py:137-159`, which checks `devicectl hd screenshot` prints `tool-output.v1`, a `blob://runtime-artifact/` image artifact, display access args, and no raw base64 or `"screenshot":` field.
- Cited `novaic-cortex/tests/test_shell_capabilities_blob_contract.py:200-205`, which checks help text teaches artifact manifests and not raw base64.
- Cited `novaic-agent-runtime/tests/unit/task_queue/test_shell_output_contract.py:52-80`, which checks shell results are durable `tool-step-payload.v1` with `llm_content` following `tool-output.v1`.

## Verification

- Focused test command:
  - `PYTHONPATH="/Users/wangchaoqun/new-build-novaic/novaic-logicalfs:/Users/wangchaoqun/new-build-novaic/novaic-sandbox-sdk:/Users/wangchaoqun/new-build-novaic/novaic-cortex:/Users/wangchaoqun/new-build-novaic/novaic-agent-runtime:${PYTHONPATH:-}" python -m pytest novaic-cortex/tests/test_shell_capabilities_blob_contract.py::test_devicectl_hd_screenshot_uploads_image_and_prints_tool_output_artifact novaic-cortex/tests/test_shell_capabilities_blob_contract.py::test_devicectl_help_teaches_artifact_manifest_not_base64 novaic-agent-runtime/tests/unit/task_queue/test_shell_output_contract.py::test_shell_success_uses_explicit_tool_output_contract -q`
- Result artifact: `.complex-problems/L20260516-222011/tmp/p597/shell-cli-manifest-tests.txt`.
- Outcome: `3 passed in 0.69s`.

## Known Gaps

- None for shell screenshot CLI BlobRef manifest coverage.

## Artifacts

- `.complex-problems/L20260516-222011/tmp/p597/shell-cli-manifest-scan.txt`
- `.complex-problems/L20260516-222011/tmp/p597/shell-cli-manifest-tests.txt`
