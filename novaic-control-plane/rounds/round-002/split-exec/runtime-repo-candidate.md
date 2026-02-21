# Round 002 Runtime Repo Candidate (Runtime Team)

## Goal

Move runtime implementation from monorepo layout to a runnable runtime-owned repo candidate while keeping contract-first boundaries.

## Physical extraction boundaries

### Move to runtime repo candidate (`novaic-backend`)

- `novaic-backend/runtime_orchestrator/**`
- `novaic-backend/main_runtime_orchestrator.py`
- `novaic-backend/gateway/clients/runtime_orchestrator.py`
- `novaic-backend/gateway/api/runtime_orchestrator_forward.py`
- `novaic-backend/gateway/api/internal/runtime_orchestrator.py`
- `novaic-backend/task_queue/business/runtime.py`
- `novaic-backend/task_queue/handlers/runtime_handlers.py`
- `novaic-backend/task_queue/sagas/runtime_start.py`
- `novaic-backend/task_queue/sagas/runtime_complete.py`
- `novaic-backend/tests/contract/test_runtime_orchestrator_process_startup.py`
- `novaic-backend/tests/unit/runtime_orchestrator/test_runtime_lifecycle_consistency.py`
- `novaic-backend/scripts/smoke_gateway_independent_startup.sh`

### Keep in shared contract domain (not runtime repo-local source of truth)

- `contracts/openapi/runtime-orchestrator-internal.v1.yaml`
  - Runtime Team is provider owner; contract remains shared for cross-repo consumption.

## Dependency notes

- Runtime provider contract:
  - `GET /internal/health` from `contracts/openapi/runtime-orchestrator-internal.v1.yaml`.
- API Team dependency:
  - gateway startup health gating depends on runtime-orchestrator reachability and health.
- Agent Runtime Team dependency:
  - idempotent lifecycle semantics (`get-or-create`, CAS set-status) must be preserved.
- Desktop Team dependency:
  - operability diagnostics and startup replay assume stable runtime health path.

## Non-goals in Round 002

- No direct sibling-repo source imports.
- No contract ownership move out of shared contract domain.
