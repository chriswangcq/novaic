# PR-200 — Blob Service Foundation

| Field | Value |
| --- | --- |
| Status | `[done]` |
| Owner | Codex |
| Created | 2026-05-04 |
| Repos | `novaic-blob-service`, docs |
| Depends on | PR-199 |
| Theme | Blob Service infrastructure boundary |

## Goal

Turn the byte-storage service into a Blob Service infrastructure boundary while keeping existing users untouched until each call path is deliberately migrated.

## Current-State Analysis

`novaic-blob-service` is now the Blob Service implementation. It stores bytes on
disk or OSS behind a product-agnostic Blob API and returns `blob://...` refs.

## Small Tickets

- [x] PR-200A — Introduce Blob Service naming and internal contract.
- [x] PR-200B — Add `/v1/blobs/*` put/get/stat/presign endpoints backed by the existing storage backend.
- [x] PR-200C — Update health and tests to expose Blob contract version.
- [x] PR-200D — Document Blob API as the only active entrypoint.
- [x] PR-200E — Update contract and smoke scripts so validation exercises `/v1/blobs`.
- [x] PR-200F — Add disk-backend tenant isolation coverage for Blob API.
- [x] PR-200G — Reject path-unsafe tenant ids and malformed base64 at the Blob boundary.

## Done Criteria

- New Blob API exists and passes roundtrip tests.
- No retired facade remains after migration closure.
- New code examples use Blob refs.
- No product semantics are added to Blob Service.

## Deployment Checklist

- [x] `novaic-blob-service` tests pass.
- [x] Storage service smoke passes locally against `/v1/blobs`.
- [x] Health check shows Blob Service contract.

## Implementation Notes

- Added the Blob infrastructure facade over the existing byte backend.
- Added `/v1/blobs` create/info/read/presign/delete routes. They return `blob://...` metadata and never return raw payload in metadata responses.
- PR-205 later deleted the temporary retired facade; the active API is now
  `/v1/blobs/*` only.
- Health reports `contract_version=blob/v1`.
- Disk backend paths include tenant id under the Blob namespace so local/dev storage also respects tenant isolation.

## Verification

- `PYTHONPATH=/Users/wangchaoqun/new-build-novaic/novaic-common:/Users/wangchaoqun/new-build-novaic/novaic-blob-service .venv/bin/python -m pytest` → `16 passed, 1 skipped`
- `.venv/bin/python -m compileall -q blob_service tests`
- `python3 scripts/ci/check_start_config_contract.py` → `start_config_contract OK`
- `PYTHONPATH=/Users/wangchaoqun/new-build-novaic/novaic-common:/Users/wangchaoqun/new-build-novaic/novaic-blob-service bash scripts/verify_contract_version_blob.sh` → `BLOB_SERVICE_CONTRACT_VERSION=PASS`
- `PYTHONPATH=/Users/wangchaoqun/new-build-novaic/novaic-common:/Users/wangchaoqun/new-build-novaic/novaic-blob-service BLOB_SERVICE_PORT=<random> bash scripts/smoke_blob_service.sh` → `BLOB_SERVICE_SMOKE_OK=true`
