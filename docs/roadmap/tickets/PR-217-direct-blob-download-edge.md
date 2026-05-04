# PR-217 Direct Blob Download Edge

| Field | Value |
| --- | --- |
| Status | `[closed]` |
| Type | Blob download data-plane cleanup |
| Created | 2026-05-04 |
| Scope | App attachment cache download, Gateway Blob proxy routes, docs/guards |
| Dependencies | PR-216 |

## Goal

Make attachment download symmetric with upload: Gateway remains control plane for
upload config and file registration, while Blob bytes move through the
authenticated `/blob/` edge instead of the Gateway application process.

## Large Work Orders

### 1. App Download Path

- Objective: cached attachment downloads resolve `blob://...` into direct Blob
  edge paths.
- Scope: `novaic-app/src-tauri/src/commands/file.rs`,
  `novaic-app/src-tauri/src/core/gateway_client.rs`, App static tests.
- Result:
  - Rust cache command accepts only `blob://...`.
  - Download path is `/blob/v1/blobs/{namespace}/{blob_id}`.
  - Gateway token is still sent; Nginx auth injects `X-Tenant-ID`.
  - No `/api/blobs/fetch` call remains in App source.

### 2. Gateway Old Data-plane Routes

- Objective: remove Gateway app Blob download/fetch/presign proxy routes.
- Scope: `novaic-gateway/main_gateway.py`, Gateway boundary tests.
- Result:
  - `/api/blobs/register` remains as product metadata control plane.
  - `/api/blobs/upload-config` remains as upload control plane.
  - Gateway app no longer returns raw Blob bytes.

### 3. Docs and Guardrails

- Objective: current docs describe direct Blob edge access and reject old
  Gateway app proxy wording.
- Scope: Blob reference docs, architecture docs, roadmap tickets.
- Result:
  - App upload and download both use `/blob/` data plane.
  - Gateway app is not described as a Blob byte proxy.

## Acceptance

- App attachment download uses direct Blob edge.
- Gateway app has no Blob download/fetch/presign data-plane routes.
- Static guards fail if `/api/blobs/fetch` returns to App source.
- Current docs no longer describe Gateway app as attachment download proxy.

## Verification

- `cd novaic-app && npm run test:unit -- src/application/blobAttachmentPath.test.ts`
- `cd novaic-app/src-tauri && cargo check`
- `cd novaic-gateway && PYTHONPATH=.:../novaic-common pytest -q tests/test_pr152_gateway_boundary.py`
- targeted `rg` for `/api/blobs/fetch`, proxy Blob download, and old data-plane
  wording.
