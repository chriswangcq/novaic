# Round 001 Runtime Extraction Paths (Runtime Team)

## Target repo

- `novaic-backend`

## Extraction scope (move to runtime repo candidate)

### Core runtime service

- `novaic-backend/runtime_orchestrator/**`
  - Reason: runtime lifecycle source of truth (state machine, internal runtime APIs, persistence).
- `novaic-backend/main_runtime_orchestrator.py`
  - Reason: runtime-orchestrator entrypoint owned by runtime service.

### Runtime-facing gateway adapters (runtime-owned integration surface)

- `novaic-backend/gateway/clients/runtime_orchestrator.py`
  - Reason: gateway client wrapper for runtime orchestrator dependency.
- `novaic-backend/gateway/api/runtime_orchestrator_forward.py`
  - Reason: forwarding layer that binds gateway to runtime service boundary.
- `novaic-backend/gateway/api/internal/runtime_orchestrator.py`
  - Reason: internal runtime orchestrator route surface consumed by other backend components.

### Runtime lifecycle business flow

- `novaic-backend/task_queue/business/runtime.py`
  - Reason: runtime lifecycle business logic on queue path.
- `novaic-backend/task_queue/handlers/runtime_handlers.py`
  - Reason: runtime lifecycle event handler entrypoints.
- `novaic-backend/task_queue/sagas/runtime_start.py`
  - Reason: runtime startup saga orchestration.
- `novaic-backend/task_queue/sagas/runtime_complete.py`
  - Reason: runtime completion saga orchestration.

### Runtime reliability checks and baseline tests

- `novaic-backend/tests/contract/test_runtime_orchestrator_process_startup.py`
  - Reason: process-level startup contract baseline for extraction safety.
- `novaic-backend/tests/unit/runtime_orchestrator/test_runtime_lifecycle_consistency.py`
  - Reason: lifecycle determinism and CAS semantics baseline.
- `novaic-backend/scripts/run_strict_runtime_orchestrator_contracts.sh`
  - Reason: replay entrypoint for runtime startup contract checks.

## Keep outside runtime repo (contract-only dependency)

- `contracts/openapi/runtime-orchestrator-internal.v1.yaml`
  - Keep in `novaic-shared-kernel` contract domain; runtime team is provider owner, consumers include API/gateway.

## Consumer impact note

- Consumers must integrate through runtime service URL/API contract, not source imports.
- Any contract change in runtime lifecycle/status semantics requires impact notes from:
  - `API Team` (gateway coupling),
  - `Agent Runtime Team` (retry/idempotency consumers),
  - `Desktop Team` (runtime operability diagnostics).
