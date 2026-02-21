# Round 003 Gateway Migration Map (API Team)

## Target repo

- repo_name: `novaic-gateway`
- repo_path: `novaic-control-plane/rounds/round-003/split-move/repos/novaic-gateway`
- objective: split out gateway service startup + runtime forwarding baseline

## Source -> target migrated paths

| source_path | target_path | decision |
|---|---|---|
| `novaic-backend/gateway/api/runtime_orchestrator_forward.py` | `split-move/repos/novaic-gateway/api/runtime_orchestrator_forward.py` | moved (adapted env-based config for split repo startup) |
| `novaic-backend/main_gateway.py` (health and root API behavior subset) | `split-move/repos/novaic-gateway/services/gateway_api.py` | moved (minimal runnable subset for split baseline) |
| `novaic-backend/scripts/smoke_gateway_independent_startup.sh` (startup/health replay pattern) | `split-move/repos/novaic-gateway/scripts/smoke_gateway_repo_root.sh` | moved (adapted to split repo root + runtime split repo dependency) |

## Removed/kept decisions

- removed-from-initial-split:
  - full gateway DB/config/task orchestration modules (kept in monorepo for phased extraction)
  - vm/tool/file/trs proxy APIs (deferred to next split round)
- kept-in-target-now:
  - gateway startup health endpoint
  - runtime-orchestrator forwarding path
  - split-repo root smoke script with deterministic PASS markers
