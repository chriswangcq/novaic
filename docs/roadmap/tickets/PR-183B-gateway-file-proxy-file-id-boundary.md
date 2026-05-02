# PR-183B — Gateway file proxy file-id boundary

Status: `[closed]` — 2026-05-03

## Finding

Gateway GET `/api/files/{file_id_or_path}` still accepts raw storage paths and proxies them directly to File Service. That bypasses the file metadata ownership check and keeps a historical path alive. The product path is:

- GET `/api/files/f_<id>` for registry-backed file download.
- POST `/api/files/fetch` for `fs://...` or `/api/files/...` references used by Tauri cache commands.

## Scope

- Reject non-file-id GET `/api/files/*` paths at Gateway.
- Preserve POST `/api/files/fetch`.
- Pass `X-User-ID` explicitly when Gateway calls File Service so the storage owner boundary is not implicit.
- Add source/route guard.

## Tests

- Gateway file proxy source guard.
- Full Gateway suite.

## Deployment / Git

- Deploy Gateway.
- Commit/push `novaic-gateway`.

## Closure

- GET `/api/files/*` now accepts registry-backed `f_...` IDs only.
- Raw storage path GET bypass returns 404.
- Gateway now passes `X-User-ID` explicitly to File Service for file downloads/fetches.
- POST `/api/files/fetch` remains the explicit fs/path resolver.
- Added Gateway boundary guard.
- Tests: `PYTHONPATH=. pytest -q tests/test_pr152_gateway_boundary.py`, `PYTHONPATH=. pytest -q`.
