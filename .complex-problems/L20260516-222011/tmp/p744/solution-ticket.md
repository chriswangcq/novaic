# Disposition Device VmControl screenshot route

## Summary

Determine whether the mounted Device VmControl screenshot route is legacy/debug-only, still product-facing, or should be converted to a Blob/artifact contract.

## Problem Definition

`novaic-device/device/vmcontrol_routes.py` exposes `/api/vmcontrol/vms/{vm_id}/screenshot` returning inline MCP image content. This conflicts with the preferred media boundary if it is product-facing, but changing it without caller analysis could break clients.

## Proposed Solution

Inspect route implementation, mounting, tests, and in-repo callers. If safe and clearly obsolete, remove or mark legacy/debug-only with tests/docs. If still used, design the smallest compatible migration to Blob/artifact manifest. If ownership or compatibility is unclear, spawn a deeper child problem with exact blockers.

## Acceptance Criteria

- In-repo callers and mounting points are identified.
- The route is classified as removable, legacy/debug-only, or still active product API.
- Safe disposition is implemented or a deeper blocking child problem is created with exact next steps.
- Any code change is covered by focused tests.

## Verification Plan

- Search route path and handler references across repo.
- Inspect Device route tests if present.
- Run focused Device tests or route-level tests after any change.
- Re-run media-byte scan for the route after disposition.
