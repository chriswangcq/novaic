# Round 001 Storage-A Boundary (Storage-A/B Team)

## Scope and ownership

| domain | primary_owner_team | target_repo | source_path_candidates | contract_surface |
|---|---|---|---|---|
| Storage-A (File Object Domain) | `Storage-A/B Team` | `novaic-backend` (implementation), `novaic-shared-kernel` (shared contract) | `novaic-backend/file_service/**` | `contracts/openapi/storage-contracts.v1.yaml`, `contracts/schema/storage-api.v1.schema.json` |

## Extraction path (Storage-A)

1. Extract file object implementation and persistence behavior from `file_service` module into Storage-A owned service boundary.
2. Keep cross-repo contract artifacts versioned in shared kernel governance path (`contracts/**`).
3. Expose only API-level interactions to consumers (gateway/runtime/tools), no direct module import from other service repos.
4. Preserve health/read/write replay entrypoint via `novaic-backend/scripts/storage_ab_smoke.sh`.

## Boundary rules

1. Storage-A owns binary/object file lifecycle APIs and file metadata read path.
2. Changes to file payload schema must be reflected in `contracts/schema/storage-api.v1.schema.json`.
3. Any breaking boundary change requires a consumer impact update in `storage-contract-impact.md` and replay evidence in team report.
