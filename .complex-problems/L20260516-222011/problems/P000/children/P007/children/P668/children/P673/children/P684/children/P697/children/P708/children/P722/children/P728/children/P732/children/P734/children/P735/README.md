# Classify Device VmControl screenshot route

## Problem

Determine the status of `novaic-device/device/vmcontrol_routes.py` screenshot output. It currently returns inline MCP-style image bytes from `/api/vmcontrol/vms/{vm_id}/screenshot`. We need to know whether this is active product/runtime behavior, legacy compatibility, safe-to-retire, or a remediation candidate for the Blob/artifact contract.

## Success Criteria

- The screenshot route implementation is inspected with file pointers.
- Route mounting and call sites are checked so its active/dormant status is evidence-based.
- The final classification states exactly one status: active product path, legacy compatibility, safe-to-retire, or remediation candidate.
- If remediation is needed, the required change is stated minimally.
