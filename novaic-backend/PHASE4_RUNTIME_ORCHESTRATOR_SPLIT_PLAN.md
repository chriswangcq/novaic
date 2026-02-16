# Phase 4: Runtime Orchestrator Domain Split — Execution Plan

**Target**: Migrate `/internal/runtimes`, `/internal/subagents`, `/internal/messages` out of Gateway.  
**Context**: Prior phases completed decoupling and vmcontrol-only VM backend.  
**Risk posture**: Low — strict Runtime Orchestrator dependency, no protocol breaking changes.

---

## 1. Scope and Non-Goals

### In scope
- Move runtime/subagent/message **handlers** (business logic) from `gateway/api/internal/` to a new **Runtime Orchestrator** service
- Gateway becomes a **proxy/adapter** to the new service (same paths, same contract)
- Contract hardening and versioning for `/internal/runtimes`, `/internal/subagents`, `/internal/messages`

### Out of scope (non-goals)
- **Protocol changes**: HTTP paths and response schemas remain backward compatible
- **VM internal API** (`/internal/vm`, `/internal/rt/*`): remains in Gateway; VM split already done in prior phases
- **Tools Server** `/internal/runtimes` endpoints: separate migration (tools-specific runtime context); coordinate but not block Phase 4

---

## 2. Current Boundary Map

| Domain | Gateway Module | DB Repo | Callers |
|--------|----------------|---------|---------|
| **Runtimes** | `gateway/api/internal/runtime.py` | `gateway/db/repositories/runtime.py` | `task_queue/client.py`, `task_queue/business/mcp.py`, `task_queue/handlers/llm_handlers.py`, `tools_server/executor.py`, `tools_server/runtime_manager.py`, `conftest.py` |
| **SubAgents** | `gateway/api/internal/subagent.py` | `gateway/db/repositories/subagent.py` | `task_queue/client.py`, `tools_server/executor.py`, `conftest.py` |
| **Messages** | `gateway/api/internal/message.py` | `gateway/db/repositories/message.py` (MessageRepository), `gateway/db/repositories/chat.py` | `task_queue/client.py`, `task_queue/workers/watchdog.py`, `novaic-gateway/sdk/messages.py`, `conftest.py` |

**Key routes** (internal prefix `/internal`):
- `/runtimes/*`: active, list, batch, with-tools, get-or-create, CRUD, context/append, history, send, tool-ports, …
- `/subagents/*`: due-wake, main, {agent_id}/{subagent_id}, awake/sleeping/completed, hrl, summary-lock, merge-history, …
- `/messages/*`: unread, unread-sent, claim-and-prepare, find-sending, mark-read, inject-wake, inject-subagent-completed, …

---

## 3. Workstreams (Sequence)

### WS1: Contract Hardening (schema / error / versioning)

1. **Schema baseline**: Document request/response shapes for all endpoints in `tests/contract/` (or `novaic-backend/docs/internal_api_contract.md`).
2. **Error contract**: Standardize `{"error": "...", "code": "..."}` and HTTP status mapping; align with `TOOLS_SERVER_QEMU_CONTRACT.md` semantics (body-level success/error).
3. **Version header**: Add optional `X-Internal-API-Version: 1`; accept without breaking legacy clients.
4. **Contract tests**: Expand `test_internal_api_contract_baseline.py` to validate envelopes and error shapes.

**Deliverable**: Contract doc + contract tests passing.

---

### WS2: Adapter / Client Extraction in Gateway (proxy-ready)

1. **RuntimeOrchestratorClient**: New client in `gateway/clients/runtime_orchestrator.py` (pattern: `VmControlClient`), with methods mirroring internal endpoints.
2. **Gateway adapters**: Keep thin handlers in `gateway/api/internal/` that delegate to `RuntimeOrchestratorClient` (strict, no local fallback).
3. **Config**: `RUNTIME_ORCHESTRATOR_URL` default-on in `common/config.py`.
4. **Caller convergence**: `task_queue` / workers internal clients default direct to Runtime Orchestrator `/internal/*`; Gateway `/internal` remains proxy/aggregator.

**Deliverable**: Gateway proxy-only for `/internal/*`; Runtime Orchestrator is mandatory.

---

### WS3: Traffic Cutover and Rollback

1. **Runtime Orchestrator service**: FastAPI service hosting runtime/subagent/message handlers; DB access via `runtime_orchestrator.db`.
2. **Cutover**: Set `RUNTIME_ORCHESTRATOR_URL` in env; Gateway proxies all `/internal/runtimes`, `/internal/subagents`, `/internal/messages` to the new service.
3. **Rollback**: Not required for this phase (no online users). Keep strict path and fail-fast behavior.
4. **Health checks**: Orchestrator exposes `/health`; Gateway health may optionally probe Orchestrator when configured.

**Deliverable**: Cutover playbook and rollback procedure documented.

---

## 4. PR Slicing Plan

| PR | Content | Acceptance |
|----|---------|------------|
| P4-1 | Contract doc + schema baseline + error contract | Contract tests pass |
| P4-2 | Version header + contract tests expansion | All contract tests pass |
| P4-3 | `RuntimeOrchestratorClient` + config | Unit test client against mock |
| P4-4 | Gateway adapters (proxy when URL set) | Existing internal API contract tests pass; manual proxy smoke |
| P4-5 | Runtime Orchestrator service skeleton + handlers | Service starts; contract tests hit new service when URL set |
| P4-6 | Cutover playbook + rollback doc | Reviewed by tech lead |

**Principle**: Each PR is independently reviewable; merge order enforced; no production behavior change until P4-5 + cutover.

---

## 5. Test Plan

### Contract tests
- **Route existence**: Keep `test_internal_api_contract_baseline.py` for route and envelope checks.
- **Schema validation**: Add tests for response fields (`runtimes`, `subagents`, `messages`, `error`, `code`).
- **Error shapes**: 4xx responses include `error`; body-level semantics aligned with QEMU contract.

### Smoke checks
1. **Strict mode**: Runtime Orchestrator healthy before Gateway; internal API tests pass.
2. **Gateway proxy mode**: Gateway `/internal/*` proxies to Orchestrator; same contracts pass.
3. **End-to-end**: Task Queue/Workers → Orchestrator `/internal/*` (direct default) and Gateway `/internal/*` (proxy path) both pass contracts.

### Run commands
```bash
pytest novaic-backend/tests/contract/test_internal_api_contract_baseline.py -v
# After Orchestrator exists:
RUNTIME_ORCHESTRATOR_URL=http://127.0.0.1:<port> pytest novaic-backend/tests/contract/ -v
```

---

## 6. Ownership Suggestions

| Area | Owner | Focus |
|------|-------|-------|
| Contract / schema | Backend lead | WS1, contract doc, versioning |
| Gateway adapters + client | Backend dev | WS2, `RuntimeOrchestratorClient`, feature flag |
| Runtime Orchestrator service | Backend dev | WS3, new service, handler migration |
| Task Queue / Tools Server | Integration owner | No code change; validate after cutover |
| Cutover / rollback | Tech lead | Playbook, deployment, monitoring |

**Coordination**: Weekly sync during Phase 4; contract doc is source of truth; PRs reference contract section.

---

## Summary

- **Scope**: Move runtime/subagent/message handlers to Runtime Orchestrator; Gateway proxies.
- **Non-goals**: No protocol break, VM/Tools Server scoped separately.
- **Sequence**: Contract → Adapter/client → Cutover.
- **PRs**: 6 small PRs (contract, versioning, client, adapters, service, playbook).
- **Tests**: Contract + smoke under strict Runtime Orchestrator dependency.
