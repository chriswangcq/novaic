# Device screenshot route usage analysis result

## Summary

Analyzed the Device `/api/vmcontrol/vms/{vm_id}/screenshot` route. It is mounted by `main_device.py`, but no in-repo client calls that Device-Service HTTP path. Active VM screenshot execution uses typed CloudBridge commands from Device to VmControl and maps to VmControl's local `/api/vms/{id}/screenshot`, not the Device Service `/api/vmcontrol/...` route. Recommendation: remove the Device screenshot HTTP route in the implementation child, unless an external compatibility blocker is discovered.

## Evidence

Implementation and mount:

- `novaic-device/device/vmcontrol_routes.py`
  - `router = APIRouter(prefix="/api/vmcontrol", tags=["vmcontrol"])`
  - `@router.post("/vms/{vm_id}/screenshot")`
  - handler calls `broker.vm_screenshot(vm_id)` and wraps result as inline MCP image content.
- `novaic-device/main_device.py`
  - imports `vmcontrol_router`
  - mounts it with `app.include_router(vmcontrol_router)`.

Active typed command path:

- `novaic-device/device/pc_client.py`
  - `vm_screenshot()` sends typed command `vm_screenshot`.
- `novaic-app/src-tauri/vmcontrol/src/cloud_bridge.rs`
  - maps incoming `VmScreenshot` to local VmControl `POST /api/vms/{vm_id}/screenshot`.
- `docs/gateway/cloudbridge-vm.md`
  - documents `vm_screenshot` as typed CloudBridge protocol.

Searches:

```bash
rg -n "api/vmcontrol/vms|vmcontrol/vms|/vms/\\{vm_id\\}/screenshot|/vms/.*/screenshot|vm_screenshot\\(|vm_screenshot\\b|vmcontrol.*screenshot|screenshot\\(vm_id" .
rg -n "vmcontrol_router|/api/vmcontrol|vmcontrol_routes|vm_screenshot|/api/vms/.*/screenshot" novaic-device/tests novaic-device -g '*.py'
```

Findings:

- No in-repo caller of `POST /api/vmcontrol/vms/{vm_id}/screenshot` was found.
- No `novaic-device` test directly covers that route.
- The active app/VmControl screenshot route is a different local VmControl path: `/api/vms/{id}/screenshot`.

## Recommendation

For `P746`, remove the Device Service screenshot route from `vmcontrol_routes.py`. This leaves the lower-level typed CloudBridge screenshot command intact and removes the ambiguous northbound HTTP route that returns inline MCP image bytes.

## Result

Analysis complete. Implementation can proceed with route removal plus focused checks.
