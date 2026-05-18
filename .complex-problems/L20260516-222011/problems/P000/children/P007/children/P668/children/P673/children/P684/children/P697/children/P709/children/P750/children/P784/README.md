# LogicalFS Sandbox VMuse Service Cleanup

## Problem

Clean business-agnostic infrastructure surfaces that still describe stale LogicalFS/Sandbox/VMuse boundaries or expose unused helper paths.

## Success Criteria

- LogicalFS public docs/metadata emphasize live `/ro` and `/rw` file authority and avoid stale snapshot/view/patch-first phrasing.
- Unused Sandbox filesystem helper surface is deleted or relocated if confirmed inactive, including exports/tests that keep it alive artificially.
- Source VMuse stale FastMCP direct-media entry path is removed or replaced with the current Blob/tool-output/display contract.
- Service-level focused tests pass for touched LogicalFS, Sandbox, and VMuse packages.
