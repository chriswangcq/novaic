# Round 002 Storage Consumer Impact Replay (Storage-A/B Team)

## Scope

| area | contract/source | impact_target_consumers |
|---|---|---|
| Schema baseline | `contracts/schema/storage-api.v1.schema.json` | API, Runtime, Tools |
| OpenAPI baseline | `contracts/openapi/storage-contracts.v1.yaml` | API, Runtime, Tools, Desktop |
| Restore replay | `novaic-backend/scripts/storage_ab_validate_restore.sh`, `storage_ab_restore.sh` | Runtime worker and tool result consumers |
| Smoke replay | `novaic-backend/scripts/storage_ab_smoke.sh` | Gateway/runtime/tools integration consumers |

## Replay gates for physical split

1. Validate/restore replay must return `VALIDATION_OK=true` and `RESTORE_OK=true`.
2. Smoke replay must return `SMOKE_OK=true` with both storage domains healthy.
3. Evidence artifacts must be published under Round 002 report directory and linked in team report.

## Consumer impact decision

- No contract shape change in Round 002 split execution baseline.
- Consumer risk is startup/connectivity regression only, controlled by restore/smoke replay markers.
- Schema evolution is deferred; any change requires follow-up round with contract diff evidence.
