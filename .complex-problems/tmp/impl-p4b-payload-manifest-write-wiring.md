# Phase 4B Payload Manifest Write Wiring

## Problem

Payload writes currently create scope-local `payloads/*.json` records and may externalize bytes to Blob, but semantic manifest rows are not guaranteed on the live path. The write path must record manifest state in operational SQLite/Workspace at the same semantic boundary where Cortex decides what the payload means.

## Success Criteria

- `Workspace.write_payload` records manifest rows for external Blob payloads with source ref, returned BlobRef, scope/root/step linkage, size/hash/type, status, retention class, and timestamps.
- Local JSON payloads either record manifest rows or have an explicit tested design decision for scope-local-only handling.
- Step normalization/indexing continues to use the final payload ref without duplicating raw payload bytes in step files.
- Tests cover large externalized payload manifest creation, local payload behavior, manifest lookup, and retention markers.

