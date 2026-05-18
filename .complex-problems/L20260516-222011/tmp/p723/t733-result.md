# Device/artifact/display boundary remediation result

## Summary

Completed the Device/artifact/display remediation branch. Safe stale documentation and source residue were patched, generated VMuse resources were synchronized, and the ambiguous Device Service screenshot route returning inline MCP image content was removed after caller analysis.

## Child Results Used

- `P742` / `R726`: updated VMuse protocol mapping documentation.
- `P743` / `R727`: removed VMuse unused `base64` import and synced app resource bundles.
- `P744` / `R730`: analyzed and removed Device Service screenshot route.

## Changes

- `docs/mcp-vmuse/mcp-protocol-mapping.md`
  - Direct Runtime/VMuse MCP media exposure is now marked historical.
  - Current shell / Blob / display media boundary is documented.
- `novaic-mcp-vmuse/src/novaic_mcp_vmuse/tools/windows.py`
  - Removed unused `base64` import.
- `novaic-app/src-tauri/resources/novaic-mcp-vmuse/...`
  - Synced from source VMuse package.
- `novaic-app/src-tauri/gen/apple/assets/novaic-mcp-vmuse/...`
  - Synced from source VMuse package.
- `novaic-device/device/vmcontrol_routes.py`
  - Removed `POST /api/vmcontrol/vms/{vm_id}/screenshot` handler.
  - Removed unused `json` import.

## Verification

- Documentation grep/inspection completed in `R726`.
- VMuse resource hygiene: `2 passed in 0.03s`.
- Device focused tests: `6 passed in 0.13s`.
- Device router path check confirmed `/api/vmcontrol/vms/{vm_id}/screenshot` is absent and neighboring routes remain.

## Result

`P723` remediation is complete. The active media boundary is cleaner: Device/VmControl may still produce bytes at lower layers, but shell/history-facing paths use Blob manifests and explicit display projection.
