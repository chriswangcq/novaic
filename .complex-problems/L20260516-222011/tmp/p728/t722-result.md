# Legacy and standalone media-byte surface classification

## Summary

Remaining media-byte and image-content surfaces are classified. The active shell/devicectl path now returns bounded terminal text plus Blob/tool-output manifests rather than raw base64 history. Remaining raw media surfaces are lower-level Device/VMuse protocols, standalone MCP transport, test fixtures, docs, or cleanup residue. Concrete remediation candidates are listed for the next implementation phase.

## Child Results Used

- `P732` / `R714` / `R720`: active non-test production media-byte surfaces classified.
- `P733` / `R723`: docs, tests, and generated/copied resources classified.

## Classification Map

### Current LLM-Facing Shell/Runtime Contract

- `novaic-cortex/novaic_cortex/shell_capabilities.py`
  - `devicectl hd screenshot` decodes Device base64, uploads bytes to Blob, and prints `tool-output.v1` manifest text.
  - Raw screenshot/device data is removed from shell diagnostics.
- `novaic-cortex/novaic_cortex/step_result_projection.py`
  - History/current non-display projections stay text/manifest-only.
  - Display perception is the explicit visual path.
- `novaic-agent-runtime/task_queue/handlers/tool_handlers.py`
  - Public display output is placeholder text.
  - Durable payload may retain visual refs.
- `novaic-agent-runtime/task_queue/utils/multimodal.py`
  - Provider-native image construction is scoped to current-round display perception, not shell history text.

Classification: acceptable current contract.

### Standalone MCP / VMuse Media Transport

- `novaic-mcp-vmuse/src/novaic_mcp_vmuse/main.py`
- `novaic-mcp-vmuse/src/novaic_mcp_vmuse/tools/desktop.py`
- `novaic-mcp-vmuse/src/novaic_mcp_vmuse/tools/browser.py`
- `novaic-mcp-vmuse/src/novaic_mcp_vmuse/tools/files.py`

Classification: standalone VMuse/MCP media transport, not current shell/history leak.

### Lower-Level Device / VMuse Raw-Byte Protocol

- `novaic-mcp-vmuse/src/novaic_mcp_vmuse/http_server.py`
- Tauri/VmControl proxy routes inspected by child branches

Classification: active lower-level raw-byte protocol currently normalized by Cortex shell wrappers before LLM-facing context. Future architecture may migrate this to Blob/LogicalFS, but that is broader than the current shell-output bug.

### Legacy / Debug Compatibility Surface

- `novaic-device/device/vmcontrol_routes.py`
  - `/api/vmcontrol/vms/{vm_id}/screenshot` still returns inline MCP image-content shape.
  - It is mounted and should be treated as a cleanup/remediation candidate unless proven intentionally product-facing.

Classification: remediation candidate.

### Tests / Generated Resources / Docs

- Contract tests are legitimate regression guards.
- Generated `novaic-app` VMuse resources are source-package copies; do not patch directly.
- `docs/mcp-vmuse/mcp-protocol-mapping.md` is stale/misleading relative to current shell/device-proxy design.

Classification: tests are healthy; generated copies follow source-of-truth; stale doc needs remediation.

## Remediation Candidates

1. Retire or convert `novaic-device/device/vmcontrol_routes.py` screenshot endpoint so no mounted product route returns inline MCP image bytes unless explicitly marked as legacy/debug.
2. Remove unused `base64` import in `novaic-mcp-vmuse/src/novaic_mcp_vmuse/tools/windows.py`.
3. Update or mark historical `docs/mcp-vmuse/mcp-protocol-mapping.md`.
4. If VMuse source changes require it, sync generated app resource copies via the established resource-hygiene path.

## Result

`P728` classification is complete. It found no active shell/history base64 leak in the current devicectl path, but it did identify exact cleanup work needed to reduce misleading legacy surface area.
