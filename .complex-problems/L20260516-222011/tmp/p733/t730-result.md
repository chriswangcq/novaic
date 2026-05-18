# Docs and test media-byte residue classification

## Summary

The docs/test/resource media-byte residue branch is classified. Current tests largely protect the desired Blob/tool-output contract. Generated VMuse app resources are synchronized copies and should not be edited directly. One stale/misleading documentation area remains: `docs/mcp-vmuse/mcp-protocol-mapping.md` still describes Runtime exposing VMuse MCP tools directly to the LLM, which conflicts with the current shell/device-proxy direction.

## Child Results Used

- `P740` / `R721`: documentation media-byte references classified.
- `P741` / `R722`: tests and generated/copied resource media-byte references classified.

## Documentation Classification

Current or acceptable docs:

- `docs/runtime/tool-chain-dispatch.md`
- `docs/cortex/sandbox-shell.md`
- Blob/runtime artifact contract docs surfaced in the scan

Stale/misleading doc remediation candidate:

- `docs/mcp-vmuse/mcp-protocol-mapping.md`
  - Problem: still says Runtime directly introduces VMuse MCP tools to the LLM.
  - Current direction: shell/device proxy emits bounded terminal text plus Blob/tool-output manifests; direct visual/media bytes must not become LLM text history.
  - Required fix: update or mark historical so future work does not reintroduce direct MCP media tool exposure as a live design.

## Test and Resource Classification

Legitimate tests:

- `novaic-cortex/tests/test_shell_capabilities_blob_contract.py`
  - Positive regression coverage for screenshot/file-pull Blob manifests and no raw base64/stdout leak.
- `novaic-agent-runtime/tests/unit/task_queue/test_shell_output_contract.py`
  - Positive regression coverage for bounded shell output and durable payload separation.
- `novaic-cortex/tests/test_tool_output_projection.py`
  - Positive projection coverage; `data:image/png;base64,abc` is an intentional compatibility fixture.
- `novaic-app/src/application/blobAttachmentPath.test.ts`
  - Positive guard against app-level base64 upload path regressions.
- `novaic-app/src/components/Visual/ActivityTimeline.guard.test.ts`
  - Positive guard against raw MCP/base64 display in user-facing activity UI.

Generated/copied resources:

- `novaic-app/src-tauri/resources/novaic-mcp-vmuse`
- `novaic-app/src-tauri/gen/apple/assets/novaic-mcp-vmuse`

These are generated/synchronized from `novaic-mcp-vmuse`. `scripts/ci/test_app_resource_hygiene.py` enforces copy hygiene, so source fixes must happen in `novaic-mcp-vmuse` first, followed by resource sync if needed.

## Remediation List

1. Update or mark historical `docs/mcp-vmuse/mcp-protocol-mapping.md`.
2. Carry source VMuse cleanup candidate forward: remove unused `base64` import in `novaic-mcp-vmuse/src/novaic_mcp_vmuse/tools/windows.py`.
3. If VMuse source changes, sync generated app resource copies rather than patching them manually.

## Result

`P733` classification is complete. It does not require broad test rewrites; it produces a small, concrete remediation list.
