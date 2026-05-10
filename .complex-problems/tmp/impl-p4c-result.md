# Phase 4C Payload Read And Failure Semantics Result

## Summary

Implemented manifest-aware payload read failure semantics. `Workspace.read_payload` now raises explicit `PayloadReadError` codes and updates existing manifest rows to `missing`, `corrupt`, or `unavailable` with structured error payloads. Payload API helpers now surface domain details through HTTP errors instead of silently flattening known payload read failures.

## Done

- Added `PayloadReadError` with `code`, `payload_ref`, and `message`.
- Added manifest error-status update helper in `Workspace`.
- Classified read failures:
  - missing scope-local payload record -> `payload_record_missing`, status `missing`
  - malformed payload JSON record -> `payload_record_corrupt`, status `corrupt`
  - payload_ref mismatch -> `payload_ref_mismatch`, status `corrupt`
  - missing Blob client -> `payload_blob_client_missing`, status `unavailable`
  - Blob fetch failure -> `payload_blob_fetch_failed`, status `unavailable`
- Updated API payload helper to map `PayloadReadError` to explicit HTTP details/status codes.
- Added tests for missing record, corrupt record, ref mismatch, Blob fetch failure, missing Blob client, API detail propagation, and manifest status updates.

## Verification

- Targeted payload read/API tests passed: `28 passed in 0.38s`.
- Broader payload/manifest target suite passed: `46 passed in 0.41s`.
- `py_compile` for modified Cortex modules passed.
- Static search confirms domain error codes and status-update test coverage are present.

## Known Gaps

- Full Cortex suite and current-doc/static cleanup are deferred to P044 final verification.
- API payload discovery still starts from step index lookup; P044 will decide if this is acceptable for Phase 4 or needs follow-up.

## Artifacts

- `novaic-cortex/novaic_cortex/workspace.py`
- `novaic-cortex/novaic_cortex/api.py`
- `novaic-cortex/tests/test_step_index_outcome.py`
- `novaic-cortex/tests/test_payload_inspection_api.py`
- `.complex-problems/tmp/impl-p4c-result.md`
