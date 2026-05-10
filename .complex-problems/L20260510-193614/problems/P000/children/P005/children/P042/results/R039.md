# Phase 4B Payload Manifest Write Wiring Result

## Summary

Wired Cortex payload writes to semantic SQLite manifests. External Blob payloads and local JSON payloads now create `payload_manifest` rows on the live `Workspace.write_payload` path, while step files/indexes continue to store only final payload refs and not raw inline payload bytes.

## Done

- Updated `OperationalSqliteStore` schema version to 2.
- Added `source_payload_ref` to `payload_manifest`.
- Relaxed `payload_manifest.blob_ref` to nullable so local JSON payloads are represented without fake Blob authority.
- Added an idempotent schema migration that converts the old manifest table shape to the new semantic schema.
- Updated `put_payload_manifest(...)` to accept `source_payload_ref` and nullable `blob_ref`.
- Added deterministic scope-id derivation for payload manifests from `scope_path`.
- Updated `Workspace.write_payload(...)` to write a manifest row after persisting the scope-local payload trace record.
- Updated `normalize_step(...)` to pass `step_ref` into payload manifest creation.
- Added/updated tests for:
  - old schema migration
  - local payload manifest without BlobRef
  - local step payload manifest creation
  - external Blob payload manifest creation
  - nested active-scope API step write manifest creation

## Verification

- Targeted tests passed: `35 passed in 0.48s`
  - `novaic-cortex/tests/test_operational_store.py`
  - `novaic-cortex/tests/test_step_index_outcome.py`
  - `novaic-cortex/tests/test_context_event_api_steps_write.py`
  - `novaic-cortex/tests/test_workspace.py`
- Static search verified live `put_payload_manifest` wiring and new manifest fields.
- Full `py_compile` over `novaic-cortex/novaic_cortex` passed.

## Known Gaps

- Read/failure semantics are intentionally not changed here; P043 owns manifest-backed read errors and failure status updates.
- Payload API lookup still finds steps by `_index.jsonl` before reading payload content; P043/P044 will decide whether manifest lookup should become part of read discovery.

## Artifacts

- `novaic-cortex/novaic_cortex/operational_store.py`
- `novaic-cortex/novaic_cortex/workspace.py`
- `novaic-cortex/tests/test_operational_store.py`
- `novaic-cortex/tests/test_step_index_outcome.py`
- `novaic-cortex/tests/test_context_event_api_steps_write.py`
- `.complex-problems/tmp/impl-p4b-result.md`
