# PR-212 Blob Multipart Contract and Backend Support

| Field | Value |
| --- | --- |
| Status | `[closed]` |
| Type | Blob large-file upload |
| Created | 2026-05-04 |
| Scope | Blob Service upload-session API, backend-backed raw part staging, tests |
| Dependencies | PR-211 |

## Goal

Add a real multipart/resumable upload lifecycle to Blob Service without making
Gateway, Runtime, Cortex, or App carry large-byte data-plane responsibilities.

## Scope

- Define upload-session schema and lifecycle: create, upload part, complete,
  abort, status.
- Store raw byte parts through the configured Blob backend until completion.
- Add limits and failure semantics for incomplete, expired, or conflicting
  sessions.
- Keep stable `blob://...` metadata invisible until complete.

## Acceptance

- Multipart upload is idempotent by `(session_id, part_number, part_hash)`.
- Incomplete sessions can be listed/expired/aborted.
- Tests cover success, duplicate parts, wrong hash, abort, expiration, and tenant
  isolation.

## Verification

- Blob Service unit tests.
- Backend-backed session lifecycle tests through Blob Service API.
- Static guard that multipart paths use raw request bytes.

## Implementation

- Added `blob_service.multipart_storage.MultipartStorage`.
- Added routes:
  - `POST /v1/blobs/uploads`
  - `GET /v1/blobs/uploads`
  - `GET /v1/blobs/uploads/{session_id}`
  - `PUT /v1/blobs/uploads/{session_id}/parts/{part_number}`
  - `POST /v1/blobs/uploads/{session_id}/complete`
  - `POST /v1/blobs/uploads/{session_id}/abort`
  - `POST /v1/blobs/uploads/_expire`
- Stable Blob metadata is written only after `complete`.
- Part re-upload with the same sha256 is idempotent; conflicting bytes return
  conflict.
- Expired/aborted sessions reject new parts.

## Result Review

- [x] Multipart session lifecycle is tenant-scoped.
- [x] Part upload uses raw request bytes, not base64.
- [x] Completion verifies ordered parts, size, and sha256.
- [x] Abort and expiration delete temporary part bytes.
- [x] Completed session can be repeated idempotently.
- [x] Tests cover success, duplicate part, conflict, abort, expiration, bad hash,
  incomplete complete, and tenant isolation.

## Verification Log

- `cd novaic-blob-service && PYTHONPATH=.:../novaic-common pytest -q`
  - Result: `16 passed, 2 skipped`.

## Closure

Closed. Blob Service now has a real multipart session API. Direct App upload and
upload presign remain separate follow-up work under PR-213.

## Supersession

PR-216 later removed the remaining whole-object base64 upload API. Multipart is
now the only App attachment upload path.
