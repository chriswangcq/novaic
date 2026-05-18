# PR-213 App Large Upload Cutover

| Field | Value |
| --- | --- |
| Status | `[closed]` |
| Type | App upload data-plane cleanup |
| Created | 2026-05-04 |
| Scope | App upload strategy, Gateway control-plane authorization, multipart cutover |
| Dependencies | PR-212 |

## Goal

Move large user attachments away from Gateway data-plane upload while preserving
the `blob://user-file/...` attachment contract.

## Scope

- Added App upload strategy that chooses multipart/direct upload above the
  configured threshold.
- Kept Gateway as auth/control-plane only: it returns upload config and registers
  completed BlobRefs into the product file registry.
- Added a direct `/blob/` Nginx edge to Blob Service for multipart raw bytes.
- Removed TODO-only large-upload behavior from `fileUpload.ts`.
- Preserved chat attachment product semantics in Business/App, not Blob.

## Acceptance

- Large attachments do not become base64 strings in App memory.
- Gateway does not proxy large bytes for the new path.
- Completed upload writes the same BlobRef shape currently used by messages.
- User-facing upload errors are clear for size, network, abort, and completion
  failures.

## Verification

- `cd novaic-app && npm run test:unit -- src/application/blobAttachmentPath.test.ts`
- `cd novaic-gateway && PYTHONPATH=.:../novaic-common pytest -q tests/test_pr152_gateway_boundary.py`
- `cd novaic-blob-service && PYTHONPATH=.:../novaic-common pytest -q tests/test_blob_service.py`
- Static guards assert the large-upload path uses `/api/blobs/upload-config`,
  `/api/blobs/register`, `/v1/blobs/uploads`, and `X-Part-Sha256`.

## Supersession

PR-216 later removed the remaining small-file base64 upload path too. The active
App upload path is now multipart for all chat attachments.
