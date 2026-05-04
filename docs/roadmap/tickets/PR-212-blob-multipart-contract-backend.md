# PR-212 Blob Multipart Contract and Backend Support

| Field | Value |
| --- | --- |
| Status | `[open]` |
| Type | Blob large-file upload |
| Created | 2026-05-04 |
| Scope | Blob Service upload-session API, Disk/S3-compatible backend support, tests |
| Dependencies | PR-211 |

## Goal

Add a real multipart/resumable upload lifecycle to Blob Service without making
Gateway, Runtime, Cortex, or App carry large-byte data-plane responsibilities.

## Scope

- Define upload-session schema and lifecycle: create, upload part, complete,
  abort, status.
- Add Disk and S3-compatible backend interfaces for multipart semantics.
- Add limits and failure semantics for incomplete, expired, or conflicting
  sessions.
- Keep stable `blob://...` metadata invisible until complete.

## Acceptance

- Multipart upload is idempotent by `(session_id, part_number, part_hash)`.
- Incomplete sessions can be listed/expired/aborted.
- Whole-object base64 path is guarded as small-file only.
- Tests cover success, duplicate parts, wrong hash, abort, expiration, and S3
  adapter calls.

## Verification

- Blob Service unit tests.
- Backend contract tests for Disk and mocked S3-compatible clients.
- Static guard that new large-file paths do not use `/v1/blobs` base64 upload.
