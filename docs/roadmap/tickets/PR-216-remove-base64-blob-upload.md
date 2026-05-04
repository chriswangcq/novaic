# PR-216 Remove Base64 Blob Upload Path

| Field | Value |
| --- | --- |
| Status | `[closed]` |
| Type | Blob upload cleanup / old path deletion |
| Created | 2026-05-04 |
| Scope | App upload path, Gateway Blob edge, Blob Service upload API, docs/guards |
| Dependencies | PR-212, PR-213, PR-214, PR-215 |

## Goal

Finish the Blob upload migration by physically deleting the remaining base64
upload path. After this ticket, chat attachments behave as if the earlier
base64 upload version never existed in active code.

## Large Work Orders

### 1. App Upload Path

- Objective: all chat attachments upload through direct multipart Blob sessions.
- Scope: `novaic-app/src/services/fileUpload.ts` and static upload-path tests.
- Result:
  - no `FileReader`
  - no `readAsDataURL`
  - no `fileToBase64`
  - no `/api/blobs/from-base64`
  - no size threshold branch selecting an old upload path
- Verification:
  - `npm run test:unit -- src/application/blobAttachmentPath.test.ts`
  - `npm run build`

### 2. Gateway and Blob Service APIs

- Objective: remove the old upload API from service code.
- Scope:
  - Gateway `/api/blobs/from-base64`
  - Blob Service `POST /v1/blobs`
  - Blob storage base64 decoder/storage helper
  - base64 upload size-limit env knob
  - Blob Service smoke script
- Result:
  - Gateway is upload control plane plus register/fetch/presign edge.
  - Blob Service upload data plane is multipart raw bytes.
  - 0-byte files still work through multipart completion, not a fallback.
- Verification:
  - Gateway boundary test
  - Blob Service unit tests
  - `python -m compileall -q blob_service`
  - Blob Service smoke script uses multipart create/part/complete.

### 3. Docs and Guardrails

- Objective: current docs cannot lead maintainers back to the removed path.
- Scope: Blob reference docs, architecture docs, roadmap/ticket docs, README.
- Result:
  - current docs state multipart-only App attachment upload.
  - historical tickets that mention earlier base64 state point to PR-216 as
    supersession.
  - static guards fail if the old active code path returns.
- Verification:
  - targeted `rg` for old-path tokens
  - manual review of current Blob docs

## Acceptance

- App uploads every chat attachment via multipart raw bytes.
- Gateway no longer exposes `/api/blobs/from-base64`.
- Blob Service no longer exposes the base64 JSON upload API.
- Blob Service no longer contains a base64 decoder path for Blob uploads.
- Current docs no longer describe base64 upload as active.
- Remaining mentions of base64 are either unrelated low-level platform code or
  explicit historical/negative guards.

## Verification

- `cd novaic-app && npm run test:unit -- src/application/blobAttachmentPath.test.ts`
- `cd novaic-app && npm run build`
- `cd novaic-gateway && PYTHONPATH=.:../novaic-common pytest -q tests/test_pr152_gateway_boundary.py`
- `cd novaic-blob-service && PYTHONPATH=.:../novaic-common pytest -q tests/test_blob_service.py`
- `cd novaic-blob-service && python -m compileall -q blob_service`
- `cd novaic-blob-service && bash scripts/smoke_blob_service.sh`

## Closure

Closed when the above checks pass and submodule/root commits record the cleanup.
