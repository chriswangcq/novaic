# PR-203 — App / Gateway Blob Attachment Access

| Field | Value |
| --- | --- |
| Status | `[done]` |
| Owner | Codex |
| Created | 2026-05-04 |
| Repos | `novaic-app`, `novaic-gateway`, `novaic-business`, `novaic-storage-a`, docs |
| Depends on | PR-201 |
| Theme | User attachment path cleanup |

## Goal

Move user attachments and previews onto BlobRef while keeping Gateway as auth/proxy edge, not a file business service.

## Current-State Analysis

App currently uploads chat attachments through `gateway_post` to Gateway
`/api/files/from-base64`, and Rust preview/download commands fetch through
Gateway `/api/files/fetch`. Gateway proxies those requests to Storage-A legacy
`/api/files/*` and registers Business `files` rows with `storage_key` values
shaped as service-private file URLs. Business message actions preserve
attachment `url` fields without requiring BlobRef.

The new target is narrower:

- App sends upload bytes to Gateway Blob upload and receives `blob://...`.
- Gateway remains auth/proxy edge and talks to Blob Service `/v1/blobs`.
- Business `messages` attachments are product metadata carrying BlobRef, not
  Storage-A private URL.
- App preview/download resolves BlobRef through Gateway Blob fetch.

## Small Tickets

- [x] PR-203A — App upload returns and stores BlobRef for user attachments.
  - Scope: `src/services/fileUpload.ts`, message attachment VM types/tests.
  - Verification: App unit tests assert uploaded metadata uses `blob_ref` /
    `blob://`.
- [x] PR-203B — Gateway exposes only auth-bound blob proxy/presign helpers.
  - Scope: `main_gateway.py`, Gateway boundary tests.
  - Verification: upload/fetch/presign call Blob Service `/v1/blobs`; no new
    upload/fetch path constructs `/api/files`.
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
    active App rendering path documents `fs://` or `/api/files` as supported.

## Done Criteria

- Chat attachment upload and preview work with BlobRef.
- App does not construct Storage-A URLs.
- Gateway does not own file business semantics.
- Business persists product attachment semantics separately from Blob storage.

## Deployment Checklist

- [x] App build/test passes.
- [x] Gateway/business tests pass where touched.
- [ ] Services deployed.
- [ ] Smoke: upload, preview, download attachment.

## Implementation Notes

- App chat uploads now call Gateway `/api/blobs/from-base64`; uploaded
  attachment metadata carries `blob_ref` and uses the same `blob://...` value
  as the display locator.
- App Rust cache commands now fetch `blob://...` refs through
  `/api/blobs/fetch` and reject non-Blob file references.
- Gateway exposes `/api/blobs/from-base64`, `/api/blobs/fetch`,
  `/api/blobs/{namespace}/{blob_id}`, and presign proxy routes. These call Blob
  Service `/v1/blobs/*` with `X-Tenant-ID` and keep file product metadata in
  Business.
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

The legacy `/api/files/*` facade remains in Gateway and Storage-A only for the
separate PR-204/PR-205 migration and physical-deletion stages. New App chat
attachment and preview/download paths no longer use it.
