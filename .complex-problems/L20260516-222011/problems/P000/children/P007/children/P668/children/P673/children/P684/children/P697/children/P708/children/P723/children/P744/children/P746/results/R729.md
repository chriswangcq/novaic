# Device screenshot route removal result

## Summary

Removed the mounted Device Service `/api/vmcontrol/vms/{vm_id}/screenshot` route that returned inline MCP image content. The typed CloudBridge screenshot path remains intact.

## Changes

- Edited `novaic-device/device/vmcontrol_routes.py`.
  - Deleted `@router.post("/vms/{vm_id}/screenshot")` handler.
  - Removed now-unused `json` import.

Untouched active screenshot path:

- `novaic-device/device/pc_client.py::vm_screenshot`
- `novaic-app/src-tauri/vmcontrol/src/cloud_bridge.rs` `VmScreenshot` dispatch to local `/api/vms/{id}/screenshot`

## Verification

Commands run:

```bash
rg -n '@router\.post\("/vms/\{vm_id\}/screenshot"|def screenshot\(vm_id|vm_screenshot\(|import json' \
  novaic-device/device/vmcontrol_routes.py \
  novaic-device/device/pc_client.py \
  novaic-app/src-tauri/vmcontrol/src/cloud_bridge.rs

PYTHONDONTWRITEBYTECODE=1 PYTHONPATH="$PWD/novaic-device:$PWD/novaic-common" python3 - <<'PY'
from device.vmcontrol_routes import router
paths = sorted(getattr(route, 'path', '') for route in router.routes)
print('\n'.join(paths))
assert '/api/vmcontrol/vms/{vm_id}/screenshot' not in paths
assert '/api/vmcontrol/vms/{vm_id}/keys' in paths
PY

PYTHONDONTWRITEBYTECODE=1 PYTHONPATH="$PWD/novaic-device:$PWD/novaic-common" python3 -m pytest -q -p no:cacheprovider \
  novaic-device/tests/test_device_explicit_boundary_contracts.py \
  novaic-device/tests/test_pr151_device_binding_contract.py
```

Results:

- Targeted route/import search no longer finds the removed Device Service route.
- Router import/path check passed with screenshot route absent and neighboring routes present.
- Focused Device tests: `6 passed in 0.13s`.

## Note

One first assertion attempt used the un-prefixed route path and failed, because FastAPI route paths include `/api/vmcontrol`. The corrected prefixed assertion passed.

## Result

Device screenshot route disposition is complete.
