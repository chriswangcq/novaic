# PR-215 Blob Payload Limits and Observability

| Field | Value |
| --- | --- |
| Status | `[open]` |
| Type | Blob failure semantics / observability |
| Created | 2026-05-04 |
| Scope | Size limits, failure copy, upload lifecycle metrics/logs |
| Dependencies | PR-211 |

## Goal

Make Blob large-payload behavior explicit and observable so App/Runtime/Cortex
do not rediscover limits through crashes, silent truncation, or hidden retries.

## Scope

- Define size limits for base64 upload, object PUT, multipart parts, and final
  objects.
- Define failure semantics for too-large, unsupported type, expired session,
  aborted session, backend unavailable, and hash mismatch.
- Add logs/metrics around upload session lifecycle without leaking raw payload.
- Align user-facing copy and Agent Monitor perception for upload failures.

## Acceptance

- Oversized base64 upload fails fast with a documented error.
- Multipart failures are distinguishable and retry-safe where appropriate.
- Logs include blob/session ids, namespace, tenant, size class, and outcome, but
  not raw bytes or secrets.
- Runtime/App-visible errors match product copy contracts.

## Verification

- Blob Service unit tests for each failure class.
- App upload failure smoke.
- Log/metric shape review.
- Static guard against raw payload logging.
