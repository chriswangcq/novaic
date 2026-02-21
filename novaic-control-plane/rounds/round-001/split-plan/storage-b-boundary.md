# Round 001 Storage-B Boundary (Storage-A/B Team)

## Scope and ownership

| domain | primary_owner_team | target_repo | source_path_candidates | contract_surface |
|---|---|---|---|---|
| Storage-B (Tool Result Domain) | `Storage-A/B Team` | `novaic-backend` (implementation), `novaic-shared-kernel` (shared contract) | `novaic-backend/tool_result_service/**` | `contracts/openapi/storage-contracts.v1.yaml`, `contracts/schema/storage-api.v1.schema.json` |

## Extraction path (Storage-B)

1. Extract tool result persistence/query implementation from `tool_result_service` module into Storage-B owned service boundary.
2. Keep result payload compatibility and shared field definitions in shared kernel contract sources (`contracts/**`).
3. Maintain API-level producer/consumer contract with runtime and tools integrations; disallow cross-repo internal module coupling.
4. Preserve replayable verification via validate/smoke scripts under `novaic-backend/scripts/`.

## Boundary rules

1. Storage-B owns tool result create/read persistence semantics and retention-compatible schema evolution.
2. Any change to result payload fields must be evaluated for downstream runtime/tools consumers.
3. Breaking changes are gated by contract diff + validate/smoke evidence and documented in `storage-contract-impact.md`.
