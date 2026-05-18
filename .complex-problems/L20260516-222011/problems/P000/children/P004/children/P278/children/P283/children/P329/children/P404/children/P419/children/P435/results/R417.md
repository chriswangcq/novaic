# T424 Result: Cortex CLI and shell capability cleanup

## Summary

Verified the Cortex shell CLI surfaces that should carry large or binary observations. No source change was needed for this ticket: the current implementation already keeps shell stdout terminal-like and routes binary device outputs through `tool-output.v1` artifact manifests instead of raw base64.

## Done

- Audited the CLI/capability inventory for `agentctl`, `devicectl`, and `cortex payload`.
- Confirmed `devicectl hd screenshot` and `devicectl hd file-pull` wrap base64-bearing device responses into blob-backed `tool-output.v1` artifact manifests.
- Confirmed `agentctl media audio-qa` accepts `blob://...` input and only base64-encodes audio at the LLM provider transport boundary, not in shell stdout.
- Confirmed `cortex payload` provides bounded read/search/summarize/qa operations by explicit `payload_ref`.
- Ran focused shell/tool-output/payload tests.

## Verification

Command:

```bash
cd novaic-cortex
PYTHONPATH=.:../novaic-common:../novaic-logicalfs:../novaic-sandbox-sdk pytest -q \
  tests/test_shell_capabilities_blob_contract.py \
  tests/test_tool_output_projection.py \
  tests/test_step_result_projection.py \
  tests/test_payload_inspection_api.py
```

Result:

```text
28 passed in 1.55s
```

## Known Gaps

Runtime bridge and context endpoint compatibility are intentionally left to P436 because they decide whether legacy context projection endpoints are still live in the LLM prepare path.

## Artifacts

- Inventory: `.complex-problems/L20260516-222011/tmp/p435/cli-capability-inventory.txt`
- Device wrapper slice: `.complex-problems/L20260516-222011/tmp/p435/device-artifact-wrapper-slice.txt`
- Agent media slice: `.complex-problems/L20260516-222011/tmp/p435/agentctl-media-audio-slice.txt`
- Cortex payload CLI slice: `.complex-problems/L20260516-222011/tmp/p435/cortex-payload-cli-slice.txt`
- Focused verification: `.complex-problems/L20260516-222011/tmp/p435/focused-pytest.with-status.txt`

## Contract checks

1. `devicectl hd screenshot`
   - The raw device response can contain a base64 `screenshot` field at the device boundary.
   - `_wrap_hd_screenshot()` decodes that field, uploads bytes with `_put_blob()`, and returns `tool-output.v1` with an `artifacts[]` manifest and `access.display.args.file_url`.
   - The manifest sets `projection.history = manifest_only`, so shell history should retain the blob pointer, not inline image bytes.

2. `devicectl hd file-pull`
   - The raw device response can contain a base64 `data` field at the device boundary.
   - `_wrap_hd_file_pull()` decodes that field, uploads bytes with `_put_blob()`, and returns a binary artifact manifest.
   - Focused tests assert the raw base64 payload and original `"data":`/`"screenshot":` keys do not appear in shell stdout.

3. `agentctl media audio-qa`
   - The shell command accepts a `blob://...` file URL.
   - It fetches audio bytes from blob and sends base64 only at the LLM provider API boundary as `input_audio`, not as terminal output.
   - This remains a provider-transport concern, not a shell stdout contract leak.

4. `cortex payload`
   - The CLI exposes bounded `payload read/search/summarize/qa` commands using explicit `payload_ref`.
   - Help text warns not to dump raw large payloads or base64 into normal shell output.

## Residual risk

This ticket only covers shell CLI capability surfaces. Runtime bridge and context endpoint compatibility are intentionally left to P436 because they decide whether legacy context projection endpoints are still live in the LLM prepare path.
