# Clean Stale Blob Language In Architecture Docs

## Problem

Architecture and reference docs still contain broad "Blob-backed Workspace" or "Cortex uses Blob Service object APIs for production backend" phrasing. These docs should distinguish Blob as cheap byte/object persistence from LogicalFS/Cortex file authority for live `RO` / `RW`.

This child belongs under T010 because docs require a separate semantic pass from code comments.

## Success Criteria

- `docs/architecture/*`, `docs/cortex/*`, and `docs/reference/blob-service.md` no longer claim Blob is the live `RO` / `RW` authority.
- Transitional object API references are marked as adapter/internal or historical, not the desired live file path.
- Blob usage for artifacts/display/download remains described as cheap byte serving.
