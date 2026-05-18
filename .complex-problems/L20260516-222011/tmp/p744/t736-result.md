# Device VmControl screenshot route disposition result

## Summary

The Device Service screenshot route has been dispositioned and removed. Analysis found no in-repo callers of `POST /api/vmcontrol/vms/{vm_id}/screenshot`; active screenshot execution remains the typed CloudBridge path to local VmControl. Implementation removed only the ambiguous Device Service route and preserved neighboring VM control routes.

## Child Results Used

- `P745` / `R728`: route usage and ownership analysis.
- `P746` / `R729`: route removal implementation.

## Disposition

Decision: remove the Device Service screenshot HTTP route.

Reason:

- No in-repo client calls the Device Service `/api/vmcontrol/.../screenshot` path.
- The active VM screenshot command remains `pc_client.vm_screenshot` → CloudBridge `VmScreenshot` → local VmControl `/api/vms/{id}/screenshot`.
- The removed route was a mounted northbound residue that wrapped screenshot bytes as inline MCP image content, contrary to the shell/Blob/display boundary.

## Verification

- Caller/mount analysis completed in `R728`.
- Route removed in `R729`.
- Router path check confirms `/api/vmcontrol/vms/{vm_id}/screenshot` is absent and neighboring routes remain.
- Focused Device tests passed: `6 passed in 0.13s`.

## Result

`P744` is complete.
