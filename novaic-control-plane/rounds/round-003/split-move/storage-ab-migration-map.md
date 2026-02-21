# Round 003 Storage-A/B Migration Map

## Target repo candidates

| domain | repo_url | branch | split_commit_sha |
|---|---|---|---|
| Storage-A | `file:///Users/wangchaoqun/novaic/novaic-storage-a` | `split/round-003-storage-a` | `001a550a77451ecd4d5b8f775a41577ee213c6c6` |
| Storage-B | `file:///Users/wangchaoqun/novaic/novaic-storage-b` | `split/round-003-storage-b` | `ac1b88ccdab29b49f21cdaf897aae2fec7813a09` |

## Migrated paths (source -> target)

| source_path | target_repo_path |
|---|---|
| `novaic-backend/file_service/**` | `novaic-storage-a/file_service/**` |
| `novaic-backend/tool_result_service/**` | `novaic-storage-b/tool_result_service/**` |

## Schema ownership split (Round 003 baseline)

| contract_path | owner_domain | note |
|---|---|---|
| `contracts/openapi/storage-contracts.v1.yaml` | `Storage-A/B shared ownership` | Shared storage API contract kept stable during physical split execution. |
| `contracts/schema/storage-api.v1.schema.json` | `Storage-A/B shared ownership` | Shared schema baseline remains centralized before v2 domain split. |

## Runtime replay entrypoints from split roots

- Storage-A startup/smoke: `bash scripts/smoke_storage_a.sh`
- Storage-B startup/smoke: `bash scripts/smoke_storage_b.sh`
- Cross repo e2e replay: `bash novaic-control-plane/rounds/round-003/20-reports/run_storage_ab_cross_repo_e2e.sh`
