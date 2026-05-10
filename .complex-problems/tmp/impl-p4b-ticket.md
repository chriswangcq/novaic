# Wire Payload Manifest Creation On Write Path

## Problem Definition

The operational store has a `payload_manifest` table, but `Workspace.write_payload` currently only writes scope-local payload records and optional Blob bytes. Externalized payloads and local JSON payloads do not create semantic manifest rows on the live write path.

## Proposed Solution

Make the write side authoritative without changing read/failure behavior yet:

- Adjust the manifest schema/API so local JSON payloads can be represented explicitly without pretending they have a BlobRef.
- Add a small helper in `Workspace` that derives root/scope/step linkage from `scope_path` and payload refs.
- In `Workspace.write_payload`, write a manifest row after the scope-local payload record is persisted.
- For external payloads, record final BlobRef, source ref, JSON mime type, encoded size, sha256, `available` status, and retention class.
- For local payloads, record source/final ref, no BlobRef or a clearly typed local locator, JSON mime type, encoded size, sha256, `available` status, and retention class.
- Update tests to assert manifest rows for local and external payload writes and existing manifest update behavior.

## Acceptance Criteria

- External payload writes create manifest rows with final BlobRef as `payload_ref` and `blob_ref`, plus `source_payload_ref`.
- Local payload writes create manifest rows without hidden Blob authority.
- Manifest schema/API supports local payload rows explicitly.
- Step files/indexes still store only final payload refs and no inline raw payload bytes.
- Targeted write-path tests pass.

## Verification Plan

- Run `test_operational_store.py`, `test_step_index_outcome.py`, `test_context_event_api_steps_write.py`, and `test_workspace.py`.
- Run static searches for `put_payload_manifest` call sites and manifest fields.
- Run `py_compile` on `novaic-cortex/novaic_cortex`.

## Risks

- Write ordering spans Blob upload, scope-local payload file, and SQLite manifest; this ticket should avoid changing read semantics until P043.
- Deriving root/scope from `scope_path` must be deterministic and not depend on old active-stack walking.

## Assumptions

- `Workspace` always has an operational store in current runtime/tests.
- JSON payload mime type is `application/json`.
- Retention class can start as a conservative explicit default such as `default`.
