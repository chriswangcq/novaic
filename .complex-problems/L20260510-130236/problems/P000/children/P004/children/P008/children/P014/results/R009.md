# Architecture Docs Language Cleanup Result

## Summary

Updated architecture/reference docs so Blob is described as cheap byte/object infrastructure or a transitional adapter, not as the live Cortex/shell `RO` / `RW` authority.

## Done

- Updated `docs/reference/blob-service.md`:
  - Renamed "Transitional Cortex Object Store" to "Transitional Cortex Object Store Adapter".
  - Reframed `/v1/objects` as transitional/internal adapter API, not live filesystem API.
- Updated `docs/architecture/cortex.md`:
  - Replaced `WorkspaceRegistry` Blob cache wording with store-adapter wiring below the LogicalFS boundary.
- Updated `docs/architecture/data-ownership.md`:
  - Changed Workspace/context ownership to Cortex + LogicalFS file authority, with Blob only as lower byte/object persistence.
- Rewrote `docs/cortex/object-keys.md` around `CortexLogicalFileAuthority` and transitional object keys.
- Updated `docs/cortex/satellite-modules.md` to describe `blob_store.py` as a transitional adapter below the live file boundary.
- Updated `docs/architecture/logicalfs-realtime-file-authority.md` current-gap and migration wording to reflect the current in-process authority and remaining service-boundary gap.
- Updated `novaic-cortex/requirements.txt` header wording.

## Verification

- Ran focused scans over `docs/architecture`, `docs/cortex`, `docs/reference/blob-service.md`, and `novaic-cortex/requirements.txt`.
- Remaining Blob terms are intentionally scoped:
  - `Blob-backed` remains only for ordinary files/artifacts that can use Blob byte serving.
  - `BlobCortexStore`, `/v1/objects`, and object API mentions remain only as transitional adapter/internal references or guardrail language.

## Known Gaps

- P015 still needs independent residual verification and guardrail test rerun.

## Artifacts

- `docs/reference/blob-service.md`
- `docs/architecture/cortex.md`
- `docs/architecture/data-ownership.md`
- `docs/cortex/object-keys.md`
- `docs/cortex/satellite-modules.md`
- `docs/architecture/logicalfs-realtime-file-authority.md`
- `novaic-cortex/requirements.txt`
- `.complex-problems/logicalfs-impl-p4c2-result.md`
