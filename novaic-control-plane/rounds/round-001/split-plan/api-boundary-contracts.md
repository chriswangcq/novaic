# Round 001 API Boundary Contracts (API Team)

## External API boundary (`novaic-gateway`)

| boundary_type | contract_source | owned_by | consumer | notes |
|---|---|---|---|---|
| Public health endpoint | `contracts/openapi/gateway-public.v1.yaml` (`/health`) | `API Team` | external clients, operability checks | Must remain stable across repo split; replayed by gateway smoke check. |
| Gateway API root reachability | `novaic-backend/scripts/smoke_gateway_independent_startup.sh` (`/api`) | `API Team` | CI/non-author operators | Split guard for startup and routing baseline. |

## Internal dependency boundaries (gateway runtime coupling)

| dependency | current_interface | contract_owner_after_split | impact_note |
|---|---|---|---|
| Runtime Orchestrator | `contracts/openapi/runtime-orchestrator-internal.v1.yaml` (`/internal/health`) | `Runtime Team` (provider), `API Team` (consumer) | Gateway startup depends on runtime-orchestrator health before declaring gateway healthy. |
| Queue Service | runtime URL wiring in `scripts/smoke_gateway_independent_startup.sh` (`--queue-service-url`) | `Runtime Team` | Gateway keeps dependency through service URL contract; no direct repo-relative imports allowed. |
| Tools Server | runtime URL wiring in `scripts/smoke_gateway_independent_startup.sh` (`--tools-server-url`) | `Tools Team` | API layer consumes tools capability only via service endpoint boundary. |
| VMControl | runtime URL wiring in `scripts/smoke_gateway_independent_startup.sh` (`--vmcontrol-url`) | `Desktop Team` + runtime integration owner | Gateway must treat VM lifecycle API as external dependency surface. |
| File Service / Tool Result Service | runtime URL wiring in `scripts/smoke_gateway_independent_startup.sh` (`--file-service-url`, `--tool-result-service-url`) | `Storage-A/B Team` | Storage path must remain contract-first and replayable in split migration. |

## Boundary rules for split execution

1. API Team owns gateway external contract shape and compatibility notes.
2. Provider teams own their internal service contracts; API Team owns consumer impact notes when gateway coupling changes.
3. Any cross-repo contract change requires command-level replay evidence in team report before status can be `DONE`.
