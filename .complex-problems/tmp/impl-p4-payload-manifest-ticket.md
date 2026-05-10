# Cut Blob Payload Manifests Into Cortex Authority

## Problem Definition

Large Cortex tool payloads are currently externalized to Blob and a scope-local `payloads/*.json` record is written, while `OperationalSqliteStore` already has a `payload_manifest` substrate. The live `Workspace.write_payload` / `read_payload` path does not yet consistently write/read semantic manifest state from the operational store, so BlobRefs can become the hidden source of truth for payload meaning, availability, and corruption/missing behavior.

## Proposed Solution

Implement Phase 4 in small closure problems:

- Audit current payload externalization and manifest substrate boundaries.
- Wire `Workspace.write_payload` to write a manifest row whenever a local or external payload record is created.
- Make `Workspace.read_payload` consult and update manifest status for explicit missing/corrupt/blob-fetch failure behavior.
- Add retention/status markers so external payload state is visible without treating Blob as semantic authority.
- Update tests to cover externalization, missing blob, manifest lookup, local payload records, and failure status transitions.
- Remove or rewrite any old tests/docs that imply Blob raw bytes are the semantic source of truth.

## Acceptance Criteria

- Every successful payload externalization records a manifest with `payload_ref`, `source_payload_ref`, `root_scope_id`, `scope_id`, `step_ref`, `blob_ref`, size/hash/type, status, retention class, and timestamps where applicable.
- Local JSON payloads also have manifest coverage or a documented explicit reason why they remain scope-local only.
- Missing blob, malformed scope-local record, payload_ref mismatch, and Blob fetch failure produce explicit errors and manifest status updates instead of implicit raw exceptions.
- Tests cover successful externalization, missing blob/fetch failure, manifest lookup, local payload behavior, retention markers, and status updates.
- Static audit proves payload semantic state is not inferred only from BlobRef.

## Verification Plan

- Run targeted payload/step/operational-store tests:
  - `test_operational_store.py`
  - `test_step_index_outcome.py`
  - `test_workspace.py`
  - `test_context_event_api_steps_write.py`
- Run static searches for `write_payload`, `read_payload`, `put_payload_manifest`, `get_payload_manifest`, `blob_ref`, and payload failure messages.
- Run full Cortex tests and `py_compile`.

## Risks

- Payload writes span Blob, Workspace file trace, and SQLite manifest; ordering and retry behavior must be explicit to avoid partial-state ambiguity.
- Existing tests may only assert step index behavior and need stronger manifest assertions.
- Overloading BlobRef as both locator and semantic identity would recreate the hidden authority problem.

## Assumptions

- Operational SQLite store is available on every `Workspace`.
- No backward compatibility with pre-manifest payload behavior is required.
- Blob Service owns raw bytes only; Cortex owns payload semantic manifest and status.
