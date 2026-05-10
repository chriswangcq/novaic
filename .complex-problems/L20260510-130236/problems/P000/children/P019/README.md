# Replace In-Process Cortex File Authority With LogicalFS Boundary

## Problem

The current implementation routes active Cortex `RO` / `RW` operations through `CortexLogicalFileAuthority`, which is an improvement, but the authority still lives inside `novaic-cortex` and persists through `CortexStore`. The final target requires LogicalFS to be the live file authority boundary, with Cortex passing explicit semantic owner/layout inputs and no direct Cortex-owned persistence adapter for live file operations.

## Success Criteria

- Cortex Workspace live file operations call a LogicalFS boundary/port instead of directly owning the store adapter.
- The transitional `CortexLogicalFileAuthority -> CortexStore` path is removed or downgraded to a test-only/local implementation behind the LogicalFS boundary.
- `BlobCortexStore` is no longer reachable from live Workspace/registry construction except as a LogicalFS-internal persistence adapter.
- Tests prove Workspace/API/runtime/sandbox active paths still work through the LogicalFS boundary.
- Residue scans fail direct live Workspace use of `CortexStore`, `BlobCortexStore`, or `/v1/objects` outside the LogicalFS boundary.
