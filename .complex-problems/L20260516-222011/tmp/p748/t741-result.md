# Focused media-boundary test sweep result

## Summary

Focused media-boundary tests passed. Shell artifact output, Cortex projection, Runtime display/history multimodal behavior, Device route import/path behavior, and VMuse resource hygiene all verify the intended contract.

## Commands And Results

### Shell / Cortex Projection / Runtime Shell Output

```bash
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH="$PWD/novaic-logicalfs:$PWD/novaic-sandbox-sdk:$PWD/novaic-cortex:$PWD/novaic-agent-runtime:$PWD/novaic-common" \
  python3 -m pytest -q -p no:cacheprovider \
  novaic-cortex/tests/test_shell_capabilities_blob_contract.py \
  novaic-agent-runtime/tests/unit/task_queue/test_shell_output_contract.py \
  novaic-cortex/tests/test_tool_output_projection.py \
  novaic-cortex/tests/test_step_result_projection.py \
  novaic-cortex/tests/test_context_event_projection.py
```

Result: `62 passed in 1.52s`.

### Runtime Display / Historical Image Injection / Factory Multimodal

```bash
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH="$PWD/novaic-agent-runtime:$PWD/novaic-common" \
  python3 -m pytest -q -p no:cacheprovider \
  novaic-agent-runtime/tests/unit/task_queue/test_tool_handlers_display_chat_history.py \
  novaic-agent-runtime/tests/unit/task_queue/test_no_historical_tool_image_injection.py \
  novaic-agent-runtime/tests/unit/task_queue/test_factory_client_multimodal.py
```

Result: `17 passed in 0.14s`.

### Device Route / Resource Hygiene

```bash
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH="$PWD/novaic-device:$PWD/novaic-common" python3 - <<'PY'
from device.vmcontrol_routes import router
paths = sorted(getattr(route, 'path', '') for route in router.routes)
assert '/api/vmcontrol/vms/{vm_id}/screenshot' not in paths
assert '/api/vmcontrol/vms/{vm_id}/keys' in paths
print('route check ok')
PY

PYTHONDONTWRITEBYTECODE=1 PYTHONPATH="$PWD/novaic-device:$PWD/novaic-common" \
  python3 -m pytest -q -p no:cacheprovider \
  novaic-device/tests/test_device_explicit_boundary_contracts.py \
  novaic-device/tests/test_pr151_device_binding_contract.py

python3 -m pytest -q -p no:cacheprovider scripts/ci/test_app_resource_hygiene.py
```

Results:

- Route check: `route check ok`.
- Device focused tests: `6 passed in 0.10s`.
- Resource hygiene: `2 passed in 0.03s`.

## Result

Focused verification passed with no blockers.
