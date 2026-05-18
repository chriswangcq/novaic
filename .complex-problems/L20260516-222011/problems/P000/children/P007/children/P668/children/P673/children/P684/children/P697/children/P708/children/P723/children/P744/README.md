# Disposition Device VmControl screenshot route

## Summary

Review and remediate the mounted Device screenshot HTTP route that still returns inline MCP image content.

## Problem

`novaic-device/device/vmcontrol_routes.py` exposes `/api/vmcontrol/vms/{vm_id}/screenshot` returning inline MCP image bytes. It may be legacy/debug compatibility, but because it is mounted it must be dispositioned carefully rather than left as ambiguous residue.

## Success Criteria

- Identify in-repo callers and route ownership.
- Decide whether to retire, mark legacy/debug-only, or convert to Blob/artifact manifest.
- If route behavior changes, update tests and any affected clients.
- If safe disposition cannot be completed in one child, split into a deeper child with exact blockers.
