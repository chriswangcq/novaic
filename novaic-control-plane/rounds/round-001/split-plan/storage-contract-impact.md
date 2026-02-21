# Round 001 Storage Contract Impact (Storage-A/B Team)

## Contract baseline in split scope

| contract_artifact | purpose | owned_by_after_split | consumers |
|---|---|---|---|
| `contracts/openapi/storage-contracts.v1.yaml` | Storage API boundary and endpoint semantics | `Storage-A/B Team` | `API Team`, `Runtime Team`, `Tools Team`, `Desktop Team` |
| `contracts/schema/storage-api.v1.schema.json` | Storage payload schema and compatibility baseline | `Storage-A/B Team` | `API Team`, `Runtime Team`, `Tools Team` |

## Consumer impact by domain split

| split_domain | primary consumer flows | compatibility risk | required controls |
|---|---|---|---|
| Storage-A (file object) | file upload/download/read-info flows from gateway/runtime/tooling | URL/path semantics drift and metadata field mismatch | schema diff check, smoke write/read replay |
| Storage-B (tool result) | tool result create/read flows for runtime workers and tools integrations | result payload drift, ID/metadata mismatch | restore validate replay, contract diff gate |

## Round 001 impact decision

1. Keep API contract files in shared governance path during repo split to avoid temporary duplication.
2. Split implementation paths by domain (Storage-A vs Storage-B), but keep one contract baseline until post-split v2 planning.
3. Require replay evidence (validate/smoke) for each round that touches storage boundary assumptions.

## Required replay checks

- `bash novaic-backend/scripts/storage_ab_validate_restore.sh`
- `bash novaic-backend/scripts/storage_ab_smoke.sh`
