# Duplication: DEAD vs TRULY NEEDS SHARING

> Synthesized from codebase analysis. Determines which duplicated copies are in live code paths vs dead.

---

## 1. common/http/clients.py

| Repo | Usage Locations | Mounted/Live? | Verdict |
|------|-----------------|---------------|---------|
| **agent-runtime** | task_queue/business/mcp.py, handlers/llm_handlers.py, handlers/summary_handlers.py, workers/health_worker_sync.py, utils/trs_sdk.py | ✅ task_queue is active | **LIVE** |
| **tools-server** | executor.py, trs.py, api.py, tool_context_manager.py, tool_result_adapter.py | ✅ All mounted/used | **LIVE** |
| **runtime-orchestrator** | helpers.py (resolve_agent_id_from_subagent), gateway/clients/* | ❌ resolve_agent_id never called (routes not mounted); gateway/clients only used by unmounted routes | **DEAD** |
| **gateway** | web.py, llm.py, agents.py, vm.py, main_gateway.py, routes.py, devices.py, runtime_orchestrator_forward.py, gateway/clients/* | ✅ All mounted | **LIVE** |

**Conclusion**: 3 of 4 copies are LIVE. RO's copy is **DEAD** — all usage is in unmounted routes (helpers.resolve_agent_id_from_subagent) or gateway/clients that are only used by vm.py, vmcontrol.py, agents.py, etc., which RO never mounts.

---

## 2. gateway/clients (vmuse_adapter, runtime_orchestrator, vmcontrol)

| Client | Gateway | RO | Verdict |
|--------|---------|-----|---------|
| **vmcontrol** | routes.py, vm.py, vmcontrol.py, devices.py — all mounted | Only used by vm.py, vmcontrol.py — **not mounted** | Gateway: **LIVE** / RO: **DEAD** |
| **runtime_orchestrator** | internal/subagent.py, internal/agent.py, runtime_orchestrator_forward.py — mounted via internal_proxy | helpers.resolve_agent_id (never called); no other usage in mounted routes | Gateway: **LIVE** / RO: **DEAD** |
| **vmuse_adapter** | No usage in gateway/api; only tests + vmuse_adapter_example.py | No usage in RO api; only in gateway/clients (unmounted) | Gateway: **DEAD** / RO: **DEAD** |

**Conclusion**: 
- **vmcontrol**, **runtime_orchestrator**: Only Gateway needs them. RO's copies are **DEAD** (routes that use them are never mounted).
- **vmuse_adapter**: **DEAD in both**. Tools-server calls vmcontrol directly via HTTP; no live route uses VmuseAdapter.

---

## 3. skills/

| Location | Used By | Mounted/Live? | Verdict |
|----------|---------|---------------|---------|
| **RO skills/** | SkillRepository → gateway/db/repositories/skill.py | skills.py **not mounted** in RO; SkillRepository never used | **DEAD** |
| **tools-server mcp_client/skills/** | api.py `_list_skills()`, `_get_skill_content()` | internal_router `/subagents/.../skills` **mounted** | **LIVE** |

**Conclusion**: Only tools-server's copy is LIVE. RO's skills/ and SkillRepository are **DEAD** — skills.py route is not mounted in RO.

---

## 4. mcp_client Python package

| Repo | Status |
|------|--------|
| **tools-server** | **LIVE** — MCPServerConnection, ToolRegistry, mcp_client/skills/ in use |
| **RO** | **Removed** — no mcp_client package |

**Conclusion**: Single copy in tools-server. No duplication.

---

## 5. Final Matrix

| Duplicated Item | agent-runtime | tools-server | runtime-orchestrator | gateway | Live in A? | Live in B? | Live in RO? | Live in G? | Verdict |
|-----------------|---------------|--------------|---------------------|---------|------------|------------|-------------|------------|---------|
| **common/http/clients.py** | ✓ | ✓ | ✓ | ✓ | ✅ | ✅ | ❌ | ✅ | **3 LIVE, 1 DEAD** → NEEDS SHARING (3 repos) |
| **gateway/clients/vmcontrol** | - | - | ✓ | ✓ | - | - | ❌ | ✅ | **1 LIVE, 1 DEAD** → Only Gateway needs it |
| **gateway/clients/runtime_orchestrator** | - | - | ✓ | ✓ | - | - | ❌ | ✅ | **1 LIVE, 1 DEAD** → Only Gateway needs it |
| **gateway/clients/vmuse_adapter** | - | - | ✓ | ✓ | - | - | ❌ | ❌ | **0 LIVE, 2 DEAD** → Both copies DEAD |
| **skills/** | - | ✓ | ✓ | - | - | ✅ | ❌ | - | **1 LIVE, 1 DEAD** → Only tools-server needs it |
| **mcp_client** | - | ✓ | removed | - | - | ✅ | - | - | **1 copy only** → No duplication |

---

## 6. Summary Verdicts

| Item | DEAD copies | NEEDS SHARING | Action |
|------|--------------|---------------|--------|
| **common/http/clients.py** | RO (1) | agent-runtime, tools-server, gateway (3) | Extract to shared; RO can remove its copy |
| **gateway/clients (vmcontrol, runtime_orchestrator)** | RO (2 each) | Gateway only (1 each) | RO can delete its copies; only Gateway needs them |
| **gateway/clients (vmuse_adapter)** | Both (2) | None | Consider removing from both or keeping for future use |
| **skills/** | RO (1) | tools-server (1) | RO can delete skills/; tools-server is sole user |
| **mcp_client** | N/A | tools-server only | No action (single copy) |

---

## 7. Recommended Cleanup

1. **RO**: Remove `common/http/clients.py` (dead), `gateway/clients/vmuse_adapter.py`, `gateway/clients/runtime_orchestrator.py`, `gateway/clients/vmcontrol.py`, and `skills/` — all dead.
2. **common/http/clients.py**: Extract to `novaic-shared-runtime-common`; agent-runtime, tools-server, gateway consume from shared.
3. **gateway/clients**: Keep only in Gateway; no sharing needed (RO doesn't use).
4. **skills/**: Keep only in tools-server; RO can delete. Gateway has skills.py but looks for `mcp_client/skills` (returns None); tools-server has the only live skills directory.
