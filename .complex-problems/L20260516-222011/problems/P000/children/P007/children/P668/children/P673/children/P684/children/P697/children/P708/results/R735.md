# Device/devicectl and artifact-display boundary classification result

## Summary

Closed the Device/devicectl and artifact-display boundary classification branch by auditing the active screenshot/media pipeline, removing stale direct media exposure, and verifying the current shell/display contract.

The active contract is now:
- Device/VmControl/VMuse lower layers may still produce raw media bytes as lower-level protocols.
- Shell-facing media commands must return terminal-friendly text plus `tool-output.v1` Blob artifact manifests, not inline base64 payloads.
- Historical Cortex/context projection must stay manifest-only for artifacts.
- `display` is the explicit current-round image projection path to the LLM, using provider-native structured image content instead of text base64.

Concrete remediation completed:
- Updated `docs/mcp-vmuse/mcp-protocol-mapping.md` to mark direct Runtime/VMuse MCP media exposure as historical and document the current shell/Blob/display boundary.
- Removed an unused `base64` import from `novaic-mcp-vmuse/src/novaic_mcp_vmuse/tools/windows.py`.
- Re-synchronized bundled VMuse resource copies under `novaic-app/src-tauri/resources/...` and `novaic-app/src-tauri/gen/apple/assets/...`.
- Removed the stale Device Service `POST /api/vmcontrol/vms/{vm_id}/screenshot` route from `novaic-device/device/vmcontrol_routes.py`; the active screenshot path remains the typed `pc_client.vm_screenshot` / CloudBridge / local VmControl route.

Verification completed:
- Shell/Cortex projection/runtime shell output tests: `62 passed in 1.52s`.
- Runtime display/history/factory tests: `17 passed in 0.14s`.
- Device route check: confirmed `/api/vmcontrol/vms/{vm_id}/screenshot` is no longer registered.
- Device focused tests: `6 passed in 0.10s`.
- App resource hygiene tests: `2 passed in 0.03s`.

Residual notes:
- Lower-level media byte protocols remain intentionally present in VmControl/VMuse transport implementations; they are not direct LLM-history exposure paths.
- The generated/bundled VMuse resource copies are synchronized outputs and must continue to be kept in sync when source VMuse code changes.
