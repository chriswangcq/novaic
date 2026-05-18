# Remove Device Service screenshot route

## Summary

Remove the unused Device Service `/api/vmcontrol/vms/{vm_id}/screenshot` route that returns inline MCP image content, while preserving the typed CloudBridge/VmControl screenshot path.

## Problem Definition

P745 found no in-repo callers for the Device Service screenshot HTTP route. It is mounted and returns inline media bytes, which leaves misleading residue against the shell/Blob/display boundary.

## Proposed Solution

Delete only the screenshot handler from `novaic-device/device/vmcontrol_routes.py`. Do not change `pc_client.vm_screenshot`, CloudBridge `VmScreenshot`, or local VmControl `/api/vms/{id}/screenshot`.

## Acceptance Criteria

- `novaic-device/device/vmcontrol_routes.py` no longer exposes `@router.post("/vms/{vm_id}/screenshot")`.
- Typed CloudBridge screenshot code remains untouched.
- Focused Python import/route checks pass.
- A targeted search confirms no Device Service `/api/vmcontrol/.../screenshot` handler remains.

## Verification Plan

- Run targeted `rg` for the removed route.
- Import `device.vmcontrol_routes` with local `PYTHONPATH`.
- Run relevant `novaic-device` tests if they do not require unavailable external services.
