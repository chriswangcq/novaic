# PR-200 — Storage-A to Blob Service Foundation

| Field | Value |
| --- | --- |
| Status | `[done]` |
| Owner | Codex |
| Created | 2026-05-04 |
| Repos | `novaic-storage-a`, docs |
| Depends on | PR-199 |
| Theme | Storage-A de-businessing |

## Goal

Turn Storage-A from a product "File Service" into a Blob Service infrastructure boundary while keeping existing users untouched until each call path is deliberately migrated.

## Current-State Analysis

`novaic-storage-a` currently names its package, health contract, routes, and docs as `file_service` / Storage-A. It stores bytes on disk or OSS and has useful backend abstractions, but its API shape is still `/api/files/*` and it returns `fs://...`.

## Small Tickets

- [x] PR-200A — Introduce Blob Service naming and internal contract without removing existing file facade.
- [x] PR-200B — Add `/v1/blobs/*` put/get/stat/presign endpoints backed by the existing storage backend.
- [x] PR-200C — Update health and tests to expose Blob contract version.
- [x] PR-200D — Document `/api/files/*` as legacy facade only, not a new-code entrypoint.
- [x] PR-200E — Update contract and smoke scripts so validation exercises `/v1/blobs`, not the legacy facade.
- [x] PR-200F — Add disk-backend tenant isolation coverage for Blob API.
- [x] PR-200G — Reject path-unsafe tenant ids and malformed base64 at the Blob boundary.

## Done Criteria

- New Blob API exists and passes roundtrip tests.
- Existing `/api/files/*` remains only as explicitly marked compatibility facade until migrated.
- New code examples use `blob://...`, not `fs://...`.
- No product semantics are added to Blob Service.

## Deployment Checklist

- [x] `novaic-storage-a` tests pass.
- [x] Storage service smoke passes locally against `/v1/blobs`.
- [x] Health check shows Blob Service contract.

## Implementation Notes

- Added `file_service/blob_storage.py` as the Blob infrastructure facade over the existing byte backend.
- Added `/v1/blobs` create/info/read/presign/delete routes. They return `blob://...` metadata and never return raw payload in metadata responses.
- PR-205 later deleted the temporary legacy facade; the active API is now
  `/v1/blobs/*` only.
- Health reports `contract_version=blob/v1` without legacy facade markers.
- Disk backend paths include tenant id under the Blob namespace so local/dev storage also respects tenant isolation.

## Verification

- `PYTHONPATH=/Users/wangchaoqun/new-build-novaic/novaic-common:/Users/wangchaoqun/new-build-novaic/novaic-storage-a .venv/bin/python -m pytest` → `16 passed, 1 skipped`
- `.venv/bin/python -m compileall -q file_service tests`
- `python3 scripts/ci/check_start_config_contract.py` → `start_config_contract OK`
- `PYTHONPATH=/Users/wangchaoqun/new-build-novaic/novaic-common:/Users/wangchaoqun/new-build-novaic/novaic-storage-a bash scripts/verify_contract_version_a.sh` → `BLOB_SERVICE_CONTRACT_VERSION=PASS`
- `PYTHONPATH=/Users/wangchaoqun/new-build-novaic/novaic-common:/Users/wangchaoqun/new-build-novaic/novaic-storage-a STORAGE_A_PORT=<random> bash scripts/smoke_storage_a.sh` → `BLOB_SERVICE_SMOKE_OK=true`
