# PR-203 — App / Gateway Blob Attachment Access

| Field | Value |
| --- | --- |
| Status | `[done]` |
| Owner | Codex |
| Created | 2026-05-04 |
| Repos | `novaic-app`, `novaic-gateway`, `novaic-business`, `novaic-blob-service`, docs |
| Depends on | PR-201 |
| Theme | User attachment path cleanup |

## Goal

Move user attachments and previews onto BlobRef while keeping Gateway as auth/proxy edge, not a file business service.

## Current-State Analysis

App attachment upload, preview, and download now use BlobRef semantics through
Gateway's auth-bound Blob proxy. Gateway talks to Blob Service and Business
persists product attachment metadata separately from raw byte storage.

The target boundary is:

- App sends upload bytes to Gateway Blob upload and receives `blob://...`.
- Gateway remains auth/proxy edge and talks to Blob Service `/v1/blobs`.
- Business `messages` attachments are product metadata carrying BlobRef, not
  service-private storage URLs.
- App preview/download resolves BlobRef through Gateway Blob fetch.

## Small Tickets

- [x] PR-203A — App upload returns and stores BlobRef for user attachments.
  - Scope: `src/services/fileUpload.ts`, message attachment VM types/tests.
  - Verification: App unit tests assert uploaded metadata uses `blob_ref` /
    `blob://`.
- [x] PR-203B — Gateway exposes only auth-bound blob proxy/presign helpers.
  - Scope: `main_gateway.py`, Gateway boundary tests.
  - Verification: upload/fetch/presign call Blob Service `/v1/blobs`; no new
    upload/fetch path constructs retired file routes.
- [x] PR-203C — Business message attachment fields store BlobRef, not
  service-private URL.
  - Scope: `business/message_actions.py`, `business/internal/message.py`,
    Business tests.
  - Verification: message send rejects non-Blob attachment locators and stores
    attachment metadata with `blob_ref`.
- [x] PR-203D — Agent Monitor and chat rendering resolve BlobRef for display
  without leaking storage internals.
  - Scope: App Rust cache commands and React rendering helper comments/tests.
  - Verification: preview/download fetches through `/api/blobs/fetch` and no
    active App rendering path documents retired file locators as supported.

## Done Criteria

- Chat attachment upload and preview work with BlobRef.
- App does not construct service-private storage URLs.
- Gateway does not own file business semantics.
- Business persists product attachment semantics separately from Blob storage.

## Deployment Checklist

- [x] App build/test passes.
- [x] Gateway/business tests pass where touched.
- [ ] Services deployed.
- [ ] Smoke: upload, preview, download attachment.

## Implementation Notes

- Historical note: this ticket first moved chat attachment semantics to
  BlobRefs. PR-216 later retired the temporary Gateway base64 upload route.
  The active upload path is Gateway `/api/blobs/upload-config` → Blob multipart
  upload → Gateway `/api/blobs/register`.
- Uploaded attachment metadata carries `blob_ref` and uses the same
  `blob://...` value as the display locator.
- App Rust cache commands now fetch `blob://...` refs through
  `/api/blobs/fetch` and reject non-Blob file references.
- Gateway exposes upload config/register, `/api/blobs/fetch`,
  `/api/blobs/{namespace}/{blob_id}`, and presign proxy routes. These call Blob
  Service with `X-Tenant-ID` and keep file product metadata in Business.
- Business file metadata registration now validates `storage_key` as
  `blob://...` and defaults `storage_backend` to `blob-service`.
- Business message attachments now normalize to `blob_ref`/`url =
  blob://...` and reject non-Blob attachment locators.

## Verification

- `novaic-app`: `npm run test:unit` → 48 passed.
- `novaic-app`: `npm run build` → passed, with existing Vite chunk warnings.
- `novaic-business`: `PYTHONPATH=../novaic-common:. python3 -m pytest` →
  159 passed.
- `novaic-gateway`: `PYTHONPATH=../novaic-common:. python3 -m pytest` →
  24 passed.
- `diff --check` for touched repos and parent → passed.

## Residual Risk

Closed by PR-204/PR-205: historical locators were audited and the legacy file
facade was physically deleted from Gateway and Blob Service. App chat attachment
and preview/download paths use Blob refs only.
