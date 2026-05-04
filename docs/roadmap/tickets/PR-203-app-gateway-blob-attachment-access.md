# PR-203 — App / Gateway Blob Attachment Access

| Field | Value |
| --- | --- |
| Status | `[planned]` |
| Owner | Codex |
| Created | 2026-05-04 |
| Repos | `novaic-app`, `novaic-gateway`, `novaic-business`, `novaic-storage-a`, docs |
| Depends on | PR-201 |
| Theme | User attachment path cleanup |

## Goal

Move user attachments and previews onto BlobRef while keeping Gateway as auth/proxy edge, not a file business service.

## Current-State Analysis

Docs still show App upload through Gateway `/api/files/from-base64` into Storage-A `/api/files/from-base64`. Current product direction prefers Entangled for business state and narrow Gateway edge responsibilities.

## Small Tickets

- [ ] PR-203A — App upload returns and stores BlobRef for user attachments.
- [ ] PR-203B — Gateway exposes only auth-bound blob proxy/presign helpers.
- [ ] PR-203C — Business message attachment fields store BlobRef, not service-private URL.
- [ ] PR-203D — Agent Monitor and chat rendering resolve BlobRef for display without leaking storage internals.

## Done Criteria

- Chat attachment upload and preview work with BlobRef.
- App does not construct Storage-A URLs.
- Gateway does not own file business semantics.
- Business persists product attachment semantics separately from Blob storage.

## Deployment Checklist

- [ ] App build/test passes.
- [ ] Gateway/storage/business tests pass where touched.
- [ ] Services deployed.
- [ ] Smoke: upload, preview, download attachment.

