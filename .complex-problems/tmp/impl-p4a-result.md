# Phase 4A Payload Manifest Boundary Audit Result

## Summary

Completed the read-only payload manifest audit. Cortex already has a SQLite `payload_manifest` table and `put/get_payload_manifest` methods, but the live `Workspace.write_payload` / `read_payload` paths do not use them. BlobRefs currently become the final `payload_ref` for externalized payloads, and payload semantics are still mostly inferred from scope-local `payloads/*.json` files plus Blob fetch success.

## Call-Site Map

- Payload filename identity:
  - `novaic-cortex/novaic_cortex/workspace.py:31-32` hashes `payload_ref` to locate `payloads/{sha256}.json`.
- Live payload write:
  - `workspace.py:463-499` `Workspace.write_payload(scope_path, payload_ref, payload)` encodes JSON bytes, decides externalization by `BlobPayloadPolicy`, optionally uploads to Blob, writes a scope-local payload record, and returns the final ref.
  - External record fields: `payload_ref` (returned BlobRef), `source_payload_ref`, `blob_ref`, `content_type="external_blob"`, `payload_bytes`, `created_at`.
  - Local record fields: `payload_ref`, `content`, `content_type="local_json"`, `payload_bytes`, `created_at`.
- Live payload read:
  - `workspace.py:501-515` reads the scope-local payload file by hashed `payload_ref`, checks record `payload_ref`, then either calls Blob `get_payload` or returns local `content`.
  - Current failure behavior is raw `KeyError`/`FileNotFoundError`, `ValueError("payload_ref mismatch")`, `RuntimeError("external Cortex payload requires CORTEX_BLOB_SERVICE_URL")`, Blob client exceptions, or JSON decode exceptions.
- Step normalization/write:
  - `workspace.py:548-571` `normalize_step` removes inline `payload`, requires `payload_ref`, calls `write_payload`, and mirrors the final ref into `step["payload_ref"]` and `observation["payload_ref"]`.
  - `workspace.py:607-608` indexes the final `payload_ref` in `_index.jsonl`.
- API payload readers:
  - `api.py:1707-1739` finds steps by indexed `payload_ref` through the scope tree.
  - `api.py:1788-1796` `_read_step_payload` calls `ws.read_payload` and currently swallows `KeyError`, `FileNotFoundError`, `ValueError`, and `json.JSONDecodeError` as `None`; Blob/runtime errors are not explicitly classified.
  - `api.py:1894-1902` `_payload_text_by_ref` maps missing step/content to 404.
- CLI shell capability:
  - `shell_capabilities.py:750-836` `cortex payload read/search/summarize/qa` calls the API payload endpoints; it has no manifest semantics itself.

## Manifest Substrate

- `operational_store.py:126-140` defines `payload_manifest` with:
  - `payload_ref` primary key
  - `root_scope_id`, `scope_id`, `step_ref`
  - `blob_ref NOT NULL`
  - `mime_type`, `size_bytes`, `sha256`
  - `status`, `retention_class`
  - `created_at_ms`, `updated_at_ms`, `error_json`
- `operational_store.py:389-448` provides `put_payload_manifest(...)` and `get_payload_manifest(...)`.
- `tests/test_operational_store.py:236-269` verifies insert/update, status transitions, error JSON, and created/updated timestamp preservation.
- Gap: the schema currently requires `blob_ref NOT NULL`, which does not naturally represent local JSON payloads unless local payloads use a synthetic ref or the schema is relaxed.

## Current Behavior Classification

- External Blob payloads:
  - `Workspace.write_payload` uploads raw JSON bytes and stores a scope-local record with `blob_ref`.
  - No SQLite manifest row is written on the live path.
  - BlobRef becomes both locator and returned `payload_ref`.
- Local JSON payloads:
  - Stored only in scope-local `payloads/*.json`.
  - No SQLite manifest row is written.
  - Existing manifest schema cannot represent local payloads cleanly because `blob_ref` is required.
- Payload lookup:
  - Step lookup is still `_index.jsonl`-based: find matching final `payload_ref`, then read scope-local payload record.
  - The manifest substrate is unused for lookup.
- Failure semantics:
  - Missing scope-local record becomes `KeyError`/`FileNotFoundError` and then often `payload content not found`.
  - Payload ref mismatch is `ValueError`.
  - Missing Blob client is `RuntimeError`.
  - Blob missing/fetch failure bubbles from the Blob client unless swallowed by a narrow API helper.
  - No manifest status is updated on read failure.

## Existing Tests

- `tests/test_step_index_outcome.py` covers:
  - local payload normalization/write/read
  - large payload externalization to BlobRef
  - missing Blob client for large payload
  - no inline `result`
- `tests/test_context_event_api_steps_write.py` covers active-scope routed large payload externalization.
- `tests/test_workspace.py` covers payload record timestamps through injected clock.
- `tests/test_payload_inspection_api.py` covers payload read/search/summarize/qa API behavior but not manifest status.
- `tests/test_operational_store.py` covers manifest substrate in isolation.

## Boundary Decisions

- Cortex, not Blob, must own payload semantic manifest and availability status.
- Blob Service owns bytes and returns BlobRefs; it should not be the only semantic record for payload availability or retention.
- Scope-local `payloads/*.json` should remain a trace/artifact pointer, not the only authority for external payload semantics.
- P042 should wire manifest creation/update into the write path.
- P043 should define domain errors and manifest status transitions for missing/corrupt/unavailable payload reads.
- P044 should verify static/docs cleanup so current architecture does not imply Blob raw bytes own semantics.

## Verification

- Used `rg` and source reads over `workspace.py`, `blob_payload.py`, `operational_store.py`, `api.py`, `shell_capabilities.py`, and payload-related tests.
- No production code was modified in this audit ticket.

## Known Gaps

- Live workspace payload paths do not write or read SQLite manifests.
- Local payloads do not fit the current manifest schema without a design adjustment.
- Read failures do not update manifest status or emit structured domain errors.
- API payload helpers still depend on step-index search plus scope-local payload records.

## Artifacts

- `novaic-cortex/novaic_cortex/workspace.py`
- `novaic-cortex/novaic_cortex/operational_store.py`
- `novaic-cortex/novaic_cortex/blob_payload.py`
- `novaic-cortex/novaic_cortex/api.py`
- `novaic-cortex/novaic_cortex/shell_capabilities.py`
- `novaic-cortex/tests/test_step_index_outcome.py`
- `novaic-cortex/tests/test_context_event_api_steps_write.py`
- `novaic-cortex/tests/test_payload_inspection_api.py`
- `novaic-cortex/tests/test_operational_store.py`
