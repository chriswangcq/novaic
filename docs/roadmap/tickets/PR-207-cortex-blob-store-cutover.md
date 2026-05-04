# PR-207 — Cortex Blob-backed Store Cutover

| Field | Value |
| --- | --- |
| Status | `[closed]` |
| Theme | Storage boundary cleanup |
| Principle | Cortex owns work-trace semantics; Blob Service owns byte/object storage |

## Goal

Remove Cortex's direct S3/OSS production storage path. Cortex must access
workspace/scope objects only through Blob Service.

## Large Work Orders

### 1. Blob Service Object Store Boundary

- Add object-tree primitives to Blob Service: `put`, `get`, `list`,
  `list_recursive`, `move_prefix`, `delete`.
- Keep Blob Service free of Cortex semantics.
- Verify tenant isolation and Cortex tree operations.

### 2. Cortex Blob-backed Store

- Add `BlobCortexStore` implementing `CortexStore` over Blob Service object APIs.
- Switch `WorkspaceRegistry` to create `BlobCortexStore` per user.
- Remove Cortex startup S3/OSS client creation.

### 3. Physical Old Path Deletion

- Delete Cortex S3/OSS modules and tests.
- Remove Cortex S3/OSS dependencies and startup parameters.
- Move OSS/S3 physical backend config to Blob Service.

### 4. Guardrails, Docs, and Verification

- Add guard preventing S3/OSS storage residue from reappearing in Cortex code.
- Update architecture and deployment docs.
- Run targeted and package-level tests.
- Deploy the cutover and remove old object prefixes that are no longer part of
  the supported data shape.

## Acceptance

- Cortex package has no direct physical object-store implementation or SDK path.
- `scripts/start.sh` passes OSS/S3 config only to Blob Service.
- Cortex receives only `--blob-service-url` for object storage.
- Blob Service object API supports Cortex `move_prefix` semantics.
- Tests pass for Blob Service and Cortex store paths.
- Production Blob Service object PUT/GET/DELETE works through the OSS backend.
- Legacy `users/` and `cortex/` object prefixes are removed after cutover.

## Verification

- `novaic-storage-a`: `12 passed, 2 skipped`
- `novaic-cortex`: `344 passed`
- `novaic-common` targeted config/blob tests: `16 passed`
- `bash -n scripts/start.sh`
- `bash -n deploy`
- Static residue search for Cortex S3/OSS hot path.
- Deployed with `./deploy services`; `./deploy status` shows all backend
  services, Cortex, Blob Service, workers, and Relay running.
- Production smoke: Blob Service `/api/health`, Cortex `/ready`, Blob object
  PUT/GET/DELETE through `cortex-store` namespace.
- Old data cleanup: deleted 857 objects under legacy `users/` prefix, 0 under
  legacy `cortex/`, and removed `/opt/novaic/data/cortex`.
