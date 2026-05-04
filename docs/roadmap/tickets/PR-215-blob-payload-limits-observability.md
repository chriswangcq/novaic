# PR-215 Blob Payload Limits and Observability

| Field | Value |
| --- | --- |
| Status | `[closed]` |
| Type | Blob failure semantics / observability |
| Created | 2026-05-04 |
| Scope | Size limits, failure copy, upload lifecycle metrics/logs |
| Dependencies | PR-211 |

## Goal

Make Blob large-payload behavior explicit and observable so App/Runtime/Cortex
do not rediscover limits through crashes, silent truncation, or hidden retries.

## Scope

- Defined configurable size limits for base64 upload, object PUT, multipart
  parts, and final multipart objects.
- Too-large payloads return HTTP `413` with explicit payload type, actual size,
  and byte limit.
- Existing multipart 400/404/409 semantics remain distinct for invalid request,
  missing session, hash mismatch, and invalid session state.
- Added logs around upload create/part/complete/abort/expire and object put
  without raw payload bytes.
- Documented env knobs and defaults.

## Acceptance

- Oversized base64 upload fails fast with a documented error.
- Multipart failures are distinguishable and retry-safe where appropriate.
- Logs include blob/session ids, namespace, tenant, size class, and outcome, but
  not raw bytes or secrets.
- Runtime/App-visible errors match product copy contracts.

## Verification

- `cd novaic-blob-service && PYTHONPATH=.:../novaic-common pytest -q tests/test_blob_service.py`
- `cd novaic-blob-service && python -m compileall -q blob_service`
- Unit tests cover base64/object/multipart size limits and no raw payload in
  lifecycle logs.
