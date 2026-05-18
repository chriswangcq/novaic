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

- Defined configurable size limits for object PUT, multipart parts, and final
  multipart objects.
- Too-large payloads return HTTP `413` with explicit payload type, actual size,
  and byte limit.
- Existing multipart 400/404/409 semantics remain distinct for invalid request,
  missing session, hash mismatch, and invalid session state.
- Added logs around upload create/part/complete/abort/expire and object put
  without raw payload bytes.
- Documented env knobs and defaults.

## Acceptance

- Multipart failures are distinguishable and retry-safe where appropriate.
- Logs include blob/session ids, namespace, tenant, size class, and outcome, but
  not raw bytes or secrets.
- Runtime/App-visible errors match product copy contracts.

## Verification

- `cd novaic-blob-service && PYTHONPATH=.:../novaic-common pytest -q tests/test_blob_service.py`
- `cd novaic-blob-service && python -m compileall -q blob_service`
- Unit tests cover object/multipart size limits and no raw payload in lifecycle
  logs.

## Supersession

PR-216 removed the remaining base64 upload API entirely. This ticket now records
the surviving payload-limit semantics only.
