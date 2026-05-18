# Test and generated-resource media-byte residue classification

## Summary

Test residue is mostly healthy and actively guards the desired shell/display/blob contract. Generated resource residue is expected duplication from source packaging, not independent stale logic. No direct test/generated-resource code edit is needed from this ticket, but the audit carries forward cleanup candidates for source VMuse and stale docs.

## Scope

Ticket `T732` audited test and generated-resource hits for media-byte / base64 / screenshot / Blob contracts across:

- `novaic-cortex`
- `novaic-agent-runtime`
- `novaic-device`
- `novaic-mcp-vmuse`
- `novaic-app`
- `scripts`

The scan was read-only and focused on distinguishing good contract tests from stale residue and generated copies.

## Evidence Commands

```bash
rg -n "base64|data:image|screenshot|_mcp_content|tool-output\.v1|runtime-artifact|blob://|image_ref" \
  novaic-agent-runtime novaic-cortex novaic-device novaic-mcp-vmuse novaic-app scripts \
  -g '*test*.py' -g '*tests*' -g '*.py' -g '*.rs' -g '*.ts' -g '*.tsx' \
  -g '!**/.venv/**' | head -300

rg -n "base64|screenshot|file_pull|file_push" \
  novaic-app/src-tauri/resources/novaic-mcp-vmuse \
  novaic-app/src-tauri/gen/apple/assets/novaic-mcp-vmuse \
  -g '*.py' | head -120

sed -n '1,240p' novaic-cortex/tests/test_shell_capabilities_blob_contract.py
sed -n '1,260p' novaic-agent-runtime/tests/unit/task_queue/test_shell_output_contract.py
sed -n '1,220p' scripts/ci/test_app_resource_hygiene.py
```

## Findings

### Good Current Contract Tests

- `novaic-cortex/tests/test_shell_capabilities_blob_contract.py`
  - Uses a fake Device API response containing base64 media bytes as input.
  - Correctly asserts `devicectl hd screenshot` and `hd file-pull` stdout are `tool-output.v1` manifests.
  - Correctly asserts stdout contains `blob://runtime-artifact` and does not contain raw `screenshot`, `data`, or base64 media payload fields.
  - Correctly verifies `devicectl hd screenshot --help` tells agents not to paste base64 and to use `display` on Blob artifacts.
- `novaic-agent-runtime/tests/unit/task_queue/test_shell_output_contract.py`
  - Verifies shell output is terminal-like text with bounded projection.
  - Verifies raw large stdout is preserved only in durable payload storage, not injected as full context text.
  - Verifies media-like stdout stays bounded and does not leak full media payloads into live LLM context.
- `novaic-cortex/tests/test_tool_output_projection.py`
  - Verifies current `tool-output.v1` / `image_ref` projection behavior.
  - The `data:image/png;base64,abc` fixture is intentional legacy/compat input coverage, not stale production behavior.
- `novaic-app/src/application/blobAttachmentPath.test.ts`
  - Verifies app attachment path does not use `/api/blobs/from-base64` or `base64_data`.
- `novaic-app/src/components/Visual/ActivityTimeline.guard.test.ts` and `ActivityTimeline.tsx`
  - Guard user-facing activity rendering from raw `_mcp_content` and data-image base64 text.

### Generated Resource Copies

The duplicated VMuse files under:

- `novaic-app/src-tauri/resources/novaic-mcp-vmuse`
- `novaic-app/src-tauri/gen/apple/assets/novaic-mcp-vmuse`

are copied from the source `novaic-mcp-vmuse` repository. `scripts/ci/test_app_resource_hygiene.py` intentionally enforces byte-for-byte synchronization between the source package and these app resource directories, excluding caches/tests.

Conclusion: do not patch generated/copied app resources directly. Fix source `novaic-mcp-vmuse` first, then regenerate or sync app resources if needed.

### Lower-Level Protocol Hits

- `novaic-app/src-tauri/vmcontrol/src/webrtc/cursor.rs`
- `novaic-app/src/hooks/useWebRtc.ts`

These use `rgba_base64` cursor-shape payloads in the lower-level WebRTC cursor protocol. They are unrelated to shell output or LLM history injection. They can remain unless a later transport design decides to replace cursor media transport.

## Remediation Candidates Carried Forward

This ticket did not require code edits, but it confirms the following cleanup candidates discovered by parent branches:

1. Remove the unused `base64` import in `novaic-mcp-vmuse/src/novaic_mcp_vmuse/tools/windows.py`.
2. If source VMuse code changes, sync `novaic-app` VMuse resource copies rather than editing generated copies directly.
3. Update stale documentation in `docs/mcp-vmuse/mcp-protocol-mapping.md`, which still implies Runtime directly exposes VMuse MCP tools to LLM instead of the current shell/device-proxy contract.

## Result

Test residue is mostly healthy and actively guards the desired contract. Generated resource residue is expected duplication from source packaging, not independent stale logic. No direct test/generated-resource code edit is needed from this ticket.
