# PR-213 App Large Upload Cutover

| Field | Value |
| --- | --- |
| Status | `[open]` |
| Type | App upload data-plane cleanup |
| Created | 2026-05-04 |
| Scope | App upload strategy, Gateway control-plane authorization, base64 cutoff |
| Dependencies | PR-212 |

## Goal

Move large user attachments away from base64 and Gateway data-plane upload while
preserving the `blob://user-file/...` attachment contract.

## Scope

- Add App upload strategy that chooses multipart/direct upload above a configured
  threshold.
- Keep Gateway as auth/control-plane only where required.
- Remove TODO-only large-upload comments once the new path is live.
- Preserve chat attachment product semantics in Business/App, not Blob.

## Acceptance

- Large attachments do not become base64 strings in App memory.
- Gateway does not proxy large bytes for the new path.
- Completed upload writes the same BlobRef shape currently used by messages.
- User-facing upload errors are clear for size, network, abort, and completion
  failures.

## Verification

- App unit/integration tests for threshold selection.
- Manual smoke with small file and large file.
- Static guard against large-upload path using `/api/blobs/from-base64`.
