# novaic-runtime-orchestrator: DEAD vs LIVE Code Analysis

> Analysis date: 2025-03. RO was split from monolith; many modules were never mounted.

---

## 1. Main App: What Is Actually Mounted?

**File:** `main_runtime_orchestrator.py`

```python
app.include_router(internal_router)  # prefix=/internal
# Plus: app.get("/api/health") -> health()
```

**Mounted routers:**
- `gateway.api.internal.router` → prefix `/internal`
  - `runtime_router` → `/internal/runtimes/*`, `/internal/subagents/by-id/*`
  - `subagent_router` → `/internal/subagents/*`, `/internal/agents/*` (drive, info, notebook-summary, increment-interaction)
- Direct route: `/api/health`

**No other routers are included.** Files like `routes.py`, `agents.py`, `vm.py`, `skills.py`, etc. were never mounted and have been removed from the RO codebase.

---

## 2. gateway/api/* Routers: Included vs NOT Included

| Module/File | Mounted? | Used by live route? | Conclusion |
|-------------|----------|---------------------|------------|
| **gateway/api/internal/__init__.py** | ✅ Yes | N/A (router aggregator) | LIVE |
| **gateway/api/internal/runtime.py** | ✅ Yes | Yes (all routes) | LIVE |
| **gateway/api/internal/subagent.py** | ✅ Yes | Yes (all routes) | LIVE |
| **gateway/api/internal/helpers.py** | ✅ Yes (indirect) | Partially: `resolve_runtime_ids`, `get_runtime_context`, `_runtime_to_dict`, `_subagent_to_dict` used by runtime/subagent. `resolve_agent_id_from_subagent` is **never called** in RO (Gateway-only) | LIVE (with dead branch) |
| **gateway/api/schemas.py** | ❌ No | No (no route imports it) | DEAD |
| **gateway/api/__init__.py** | N/A | N/A | N/A |

**Note:** `routes.py`, `agents.py`, `vm.py`, `devices.py`, `vmcontrol.py`, `skills.py`, `chat_service.py`, `internal_proxy.py`, `runtime_orchestrator_forward.py` were documented as never mounted and have been removed from RO.

---

## 3. common/http/clients.py: Import Chain

**Importers:**
| Caller | Import | Usage |
|--------|--------|-------|
| `gateway/api/internal/helpers.py` | `internal_client` | `resolve_agent_id_from_subagent()` – **never called** by runtime/subagent |
| `gateway/clients/vmcontrol.py` | `internal_async_client` | Used by vmcontrol client |
| `gateway/clients/vmuse_adapter.py` | `internal_async_client` | Used by vmuse adapter |
| `gateway/clients/runtime_orchestrator.py` | `internal_async_client` | Used by RuntimeOrchestratorClient |

**Call chain:**
- helpers → `resolve_agent_id_from_subagent` → never invoked in RO
- vmcontrol → used by `gateway/vm/manager.py` → vm/manager not used by any mounted route
- vmuse_adapter → used only by `vmuse_adapter_example.py`
- runtime_orchestrator client → used by helpers.`resolve_agent_id_from_subagent` → dead

| Module/File | Mounted? | Used by live route? | Conclusion |
|-------------|----------|---------------------|------------|
| **common/http/clients.py** | N/A | No – all callers are in dead code paths | DEAD |

---

## 4. gateway/clients: Who Imports Them?

| Client | Imported by | In mounted route? | Conclusion |
|--------|-------------|-------------------|------------|
| **vmcontrol.py** | `gateway/vm/manager.py` | No – vm/manager not used by any route | DEAD |
| **vmuse_adapter.py** | `gateway/clients/vmuse_adapter_example.py` only | No | DEAD |
| **runtime_orchestrator.py** | `gateway/api/internal/helpers.py` (`resolve_agent_id_from_subagent`) | No – that function never called in RO | DEAD |

| Module/File | Mounted? | Used by live route? | Conclusion |
|-------------|----------|---------------------|------------|
| **gateway/clients/vmcontrol.py** | N/A | No | DEAD |
| **gateway/clients/vmuse_adapter.py** | N/A | No | DEAD |
| **gateway/clients/runtime_orchestrator.py** | N/A | No | DEAD |
| **gateway/clients/vmuse_adapter_example.py** | N/A | Standalone example script | DEAD |

---

## 5. skills/ and SkillRepository

**gateway/db/repositories/skill.py:**
- `SkillRepository` loads builtin skills from `skills/` via `load_builtin_skills()`, `get_builtin_skill()`, etc.
- Exported from `gateway/db/repositories/__init__.py`.

**Usage:** No mounted route imports `SkillRepository`. runtime.py and subagent.py use only `RuntimeRepository`, `SubAgentRepository`, `DriveRepository`, `NotebookRepository`.

**gateway/api/skills.py:** Was never mounted (removed per docs).

| Module/File | Mounted? | Used by live route? | Conclusion |
|-------------|----------|---------------------|------------|
| **gateway/db/repositories/skill.py** (SkillRepository) | N/A | No | DEAD |
| **skills/** (builtin SKILL.md dirs) | N/A | No – only SkillRepository reads them | DEAD |

---

## 6. Summary Table: All Key Modules

| Module/File | Mounted? | Used by live route? | Conclusion |
|-------------|----------|---------------------|------------|
| **gateway/api/internal/runtime.py** | ✅ | Yes | LIVE |
| **gateway/api/internal/subagent.py** | ✅ | Yes | LIVE |
| **gateway/api/internal/helpers.py** | ✅ (indirect) | Partially (resolve_agent_id branch dead) | LIVE |
| **gateway/api/schemas.py** | ❌ | No | DEAD |
| **gateway/db/access.py** | N/A | Yes (runtime, subagent) | LIVE |
| **gateway/db/repositories/runtime.py** | N/A | Yes | LIVE |
| **gateway/db/repositories/subagent.py** | N/A | Yes | LIVE |
| **gateway/db/repositories/drive.py** | N/A | Yes | LIVE |
| **gateway/db/repositories/notebook.py** | N/A | Yes | LIVE |
| **gateway/db/repositories/agent.py** | N/A | Yes (agents_db) | LIVE |
| **gateway/db/repositories/device.py** | N/A | Yes (agents_db) | LIVE |
| **gateway/db/repositories/skill.py** | N/A | No | DEAD |
| **gateway/db/repositories/config.py** | N/A | No (manager_db only, dead) | DEAD |
| **gateway/db/repositories/session.py** | N/A | No | DEAD |
| **gateway/db/repositories/chat.py** | N/A | No | DEAD |
| **gateway/db/repositories/agent_state.py** | N/A | No | DEAD |
| **gateway/db/repositories/memory.py** | N/A | No | DEAD |
| **gateway/db/repositories/message.py** | N/A | No | DEAD |
| **gateway/db/repositories/task.py** | N/A | No | DEAD |
| **gateway/config/agents.py** | N/A | Yes (subagent) | LIVE |
| **gateway/config/agents_db.py** | N/A | Yes (subagent via agents) | LIVE |
| **gateway/config/manager_db.py** | N/A | No (task_manager only, dead) | DEAD |
| **gateway/config/devices.py** | N/A | No (DeviceRepository; agents_db uses DeviceRepository but devices config may be unused in RO) | See note* |
| **gateway/vm/manager.py** | ❌ | No | DEAD |
| **gateway/vm/** (deployer, ssh, repository, etc.) | N/A | No | DEAD |
| **gateway/core/task_manager.py** | N/A | No | DEAD |
| **gateway/core/llm_client.py** | N/A | No | DEAD |
| **gateway/sse/broadcaster.py** | N/A | No | DEAD |
| **common/http/clients.py** | N/A | No | DEAD |
| **common/config.py** | N/A | Yes | LIVE |
| **common/enums.py** | N/A | Yes | LIVE |
| **common/utils/time.py** | N/A | Yes (repos, config) | LIVE |
| **common/db/** | N/A | Yes | LIVE |

\* `gateway/config/devices.py` is imported by `DeviceRepository`, which is used by `agents_db`. So devices.py is LIVE (indirectly via agents_db → subagent).

---

## 7. Dead Code Removal Candidates

**Safe to remove or refactor:**
1. `gateway/api/schemas.py` – unused
2. `gateway/db/repositories/skill.py` + `skills/` – no route uses SkillRepository
3. `gateway/db/repositories/config.py`, `session.py`, `chat.py`, `agent_state.py`, `memory.py`, `message.py`, `task.py` – no route uses them
4. `gateway/config/manager_db.py` – only used by task_manager (dead)
5. `gateway/vm/*` – entire VM module (manager, deployer, ssh, repository)
6. `gateway/clients/vmcontrol.py`, `vmuse_adapter.py`, `runtime_orchestrator.py`
7. `gateway/core/task_manager.py`, `llm_client.py`
8. `gateway/sse/broadcaster.py`
9. `common/http/clients.py` – all usages in dead paths
10. `helpers.resolve_agent_id_from_subagent` – dead branch (Gateway-only); can remove or move to shared lib

**Note:** Some dead modules may still be needed for DB schema/migration (e.g. skills table). Verify schema dependencies before deleting.
