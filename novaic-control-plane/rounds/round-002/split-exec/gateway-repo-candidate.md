# Round 002 Gateway Repo Candidate (API Team)

## Candidate repo

- target_repo: `novaic-gateway`
- owner_team: `API Team`
- source_root_now: `novaic-backend/gateway`
- extraction_mode: physical split with contract-first boundary

## Physical extraction path map

| source_path | target_repo_path | owner_team | run_state |
|---|---|---|---|
| `novaic-backend/gateway/api/**` | `novaic-gateway/api/**` | `API Team` | candidate-ready |
| `novaic-backend/gateway/core/**` | `novaic-gateway/core/**` | `API Team` | candidate-ready |
| `novaic-backend/gateway/db/**` | `novaic-gateway/db/**` | `API Team` | candidate-ready |
| `novaic-backend/gateway/config/**` | `novaic-gateway/config/**` | `API Team` | candidate-ready |
| `novaic-backend/gateway/clients/**` | `novaic-gateway/clients/**` | `API Team` (consumer), provider teams own endpoints | candidate-ready |
| `novaic-backend/gateway/vm/**` | `novaic-gateway/vm/**` | `API Team` + Desktop integration reviewer | candidate-ready |

## Contract dependency boundaries (must not be copied as direct code dependency)

- Runtime internal API contract: `contracts/openapi/runtime-orchestrator-internal.v1.yaml`
- Gateway public API contract: `contracts/openapi/gateway-public.v1.yaml`
- Storage contract baseline: `contracts/openapi/storage-contracts.v1.yaml`

## Replay baseline command for candidate operability

- startup/health replay command:
  - `bash novaic-backend/scripts/smoke_gateway_independent_startup.sh`
- expected markers:
  - `PASS: startup smoke base 61900`
  - `PASS: runtime-orchestrator healthy on 61993`
  - `PASS: gateway healthy on 61999`
  - `PASS: gateway API root reachable`
