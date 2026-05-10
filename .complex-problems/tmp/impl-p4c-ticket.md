# Make Payload Reads Manifest-Aware With Explicit Failure Semantics

## Problem Definition

Payload reads still depend on scope-local payload files plus raw Blob client behavior. Missing records, payload_ref mismatch, malformed records, missing Blob client, and Blob fetch failures do not update semantic manifest status and are not represented as explicit Cortex payload errors.

## Proposed Solution

Introduce manifest-aware read semantics:

- Add a small typed Cortex payload error that carries code, message, and payload_ref.
- Update `Workspace.read_payload` to classify missing scope-local records, malformed JSON, payload_ref mismatch, missing Blob client, and Blob fetch failure.
- When a manifest exists, update status/error on read failures.
- Preserve successful read behavior and avoid changing payload API output shape beyond better error classification.
- Update API payload helpers so domain payload errors map to explicit 404/502 details instead of silent `None` where appropriate.
- Add tests for missing local record, payload_ref mismatch, malformed payload record, missing Blob client, Blob fetch failure, and successful manifest-backed read.

## Acceptance Criteria

- Read failures produce explicit domain error codes.
- Manifest rows are updated to `missing`, `corrupt`, or `unavailable` with structured error payloads for read failures.
- Successful reads do not degrade manifest `available` status.
- API payload read/search/summarize/qa still return 404 for not found content but now preserve explicit detail for domain failures.
- Targeted read/failure tests pass.

## Verification Plan

- Run targeted tests:
  - `test_step_index_outcome.py`
  - `test_payload_inspection_api.py`
  - `test_context_event_api_steps_write.py`
- Add/update tests for manifest status transitions.
- Run `py_compile` on modified Cortex modules.

## Risks

- `_read_step_payload` currently swallows several low-level exceptions; changing this too broadly could break payload inspection API semantics.
- Some failures occur before a manifest can be found; those should still produce explicit errors but may not have a row to update.

## Assumptions

- P042 manifest rows exist for new payload writes.
- No backward compatibility is required for old payload rows without manifests, but missing-manifest reads should still fail explicitly rather than crash obscurely.
