> **文档状态（2026-04）**：本文为**历史方案 / 迁移记录与归档对照**，**非**当前唯一架构来源。现行拓扑与端口以 `docs/backend-architecture.md`、`docs/architecture-verification-2026-04.md`、`docs/runbooks/ARCHITECTURE-SERVICES-AND-HANDLERS.md` 为准。  
> **2026-04-09 合并**：已与父仓库 **Gateway internal** 与 **Agent-Runtime `task_queue/handlers/tool_handlers.py`** 现状对齐；Tools Server 段落仅适用于**分拆仓**（本 monorepo 不含 `novaic-tools-server/`）。

# 设计方案：从根源消灭 Gateway、Tools Server 的 Runtime 逻辑

## 历史说明（为何保留本文）

- **起草背景**：在仍存在独立 Runtime Orchestrator、Gateway 持有 `agent_runtimes`、独立 Tools Server 进程的年代，本文把「Gateway / Tools Server 去掉 DB/runtime 编排语义、改为 agent_id + subagent_id」拆成 Phase 1–3。
- **父仓库现状**：`novaic-runtime-orchestrator/` 与内嵌 **Tools Server** 已从本仓库移除（见 `HANDOVER.md`、`ARCHITECTURE-SERVICES-AND-HANDLERS.md`）。**默认工具执行**由 **Agent-Runtime** 的 `tool_handlers` + **Cortex** 路径承担；可选分拆仓仍可通过 `NOVAIC_TOOLS_SERVER_SPLIT_REPO` + `main_tools.py` 起独立 HTTP，与本设计中的「Tools Server」章节同源但**不在本树内**。
- **命名易混点**：`gateway/agent_binding.py` 的 `resolve_agent_runtime_context` / `build_runtime_context` 表示**设备与 subject 侧**供 LLM 使用的「运行上下文」配置，**不是**已删除的 Gateway 表 `agent_runtimes`；勿与本文档 Phase 1 的 DB 清理混为一谈。

---

## 一、目标（原文档意图）

1. **Gateway**：彻底移除「runtime 编排」概念，删除 `agent_runtimes`、`RuntimeRepository`、`resolve_runtime_ids`、`get_runtime_context`、`maybe_forward` 等与 RO 耦合的 DB/转发层。
2. **Tools Server**（分拆仓）：去除 `runtime_*` 命名，统一为 subagent 维度（如 `SubAgentToolContext`）。
3. **原则**：权威实体与上下文以 Entangled / Cortex 为准；Gateway Internal 以 `agent_id` + `subagent_id` 为主键。

---

## 二、合并后的「当前状态」（父仓库可验证）

### 2.1 Gateway

| 项目 | 现状 |
|------|------|
| `gateway/api/internal/helpers.py` | **仅** `_subagent_to_dict`；已无 `resolve_runtime_ids`、`get_runtime_context`、`maybe_forward`、`_runtime_to_dict`。 |
| `gateway/db/repositories/` | **无** `runtime.py` / `RuntimeRepository`；仅保留与本仓库相关的 repository（如 `question`）。 |
| `gateway/db/schema.py` | **SCHEMA_VERSION = 63**；建表语句中**无** `agent_runtimes`（该表随历史迁移移除；`gateway/db/fix_indexes.sql` 注释记 v43 起不再维护该表索引）。 |
| Internal API | SubAgent 维度路由已实现（如 `/internal/subagents/...`）；与本文「Phase 1 Gateway」目标一致的部分**已落地**。 |
| `--runtime-orchestrator-url` | `main_gateway.py` CLI 仍保留**隐藏**参数以兼容旧启动脚本；业务上以 `HANDOVER` / 当前部署为准（RO 子模块已不在本仓库）。 |

### 2.2 Agent-Runtime：`tool_handlers`（现行「工具网关」）

工具执行在 **`novaic-agent-runtime/task_queue/handlers/tool_handlers.py`**，**不是** 本仓库内的 Tools Server 进程。

| 项目 | 现状 |
|------|------|
| 关联键 | `handle_tool_execute` 使用 **`scope_id`**：`payload.get("scope_id") or payload.get("runtime_id", "")` —— **对外字段名为 `scope_id`**，仍接受旧 payload 键 `runtime_id` 作为兼容别名（用于 round / 广播去重，**不是** Gateway `agent_runtimes` 行）。 |
| 身份 | `agent_id`、`subagent_id`（默认 `"main"`）来自 payload；与 Gateway 的 `gw_client.request(..., f"/internal/agents/{agent_id}/...", ...)`、`/internal/subagents/...` 调用一致。 |
| 返回 | 统一 `_ok` / `_err`，带 `scope_id`、`round_id`、`tool_call_id`、`tool_name`。 |
| 可选 Tools Server HTTP | `task_queue/client.py` 等在**配置了** `tools_server_url` 时仍可走分拆仓的 `/internal/subagents/.../tools/*`；父仓库默认路径不依赖内嵌 `main_tools.py`。 |

### 2.3 Tools Server（分拆仓 / 可选）

| 项目 | 说明 |
|------|------|
| 本 monorepo | **不包含** `novaic-tools-server/`；下文「Phase 2」中的文件级重命名**仅在对照分拆仓或历史 PR 时有意义**。 |
| 业务结论 | 见 `HANDOVER.md`：独立 Tools Server **已退役**于默认拓扑；若仍维护分拆仓，可自行对照原 Phase 2 清单清理 `RuntimeManager` 等命名。 |

### 2.4 与原文档「§2.2 待清理」的对照

原文列出的 Gateway 死代码与 `RuntimeRepository` **在父仓库当前树中已不存在**（或已迁移为上述现状）。Tools Server 侧待清理项 **不适用本仓库路径**；若分拆仓仍存在 `runtime_manager.py` 等，视为可选后续工作。

---

## 三、原 Phase 1：Gateway 彻底移除 Runtime（归档 — 已基本完成于父仓库）

以下表格保留为**历史施工清单**；实施时请以当时分支为准。当前父仓库已符合「helpers 精简、无 RuntimeRepository、无 `agent_runtimes` 表」的结论性描述。

### 3.1 删除死代码（历史）

| 文件 | 删除内容 |
|------|----------|
| **helpers.py** | `resolve_runtime_ids`、`get_runtime_context`、`_runtime_to_dict` |
| **helpers.py** | `maybe_forward_to_runtime_orchestrator`、`_RO_FORWARDED_PREFIXES`、`set_runtime_orchestrator_process` |
| **helpers.py** | `RUNTIME_ORCHESTRATOR_URL` 相关逻辑（若曾存在于 helpers） |

### 3.2–3.4 移除转发与仓库（历史）

见原文档版本控制历史；当前以 `internal/message.py`、`internal/subagent.py` 等**实际代码**为准，已无 `maybe_forward` 模式。

### 3.5 依赖检查（历史）

- `_subagent_to_dict`：仍在 `helpers.py`，保留。
- `gateway/api/skills.py`：以当前实现为准（Internal Client / Entangled）。

---

## 四、原 Phase 2：Tools Server 去除 Runtime 命名（归档 — 分拆仓）

**适用范围**：含 `main_tools.py` 的分拆仓库；**非**本 monorepo 必做项。

### 4.1 重命名（概念统一）

| 原命名 | 新命名 | 说明 |
|--------|--------|------|
| **RuntimeContext** | **SubAgentToolContext** | 工具上下文，主键为 subagent |
| **RuntimeManager** | **SubAgentToolContextManager** | 或简化为 ToolContextManager |
| **runtime_id**（内部 key） | **context_key** 或 **subagent_key** | `f"{agent_id}:{subagent_id}"` |
| **runtime_manager.py** | **tool_context_manager.py** | 文件名 |
| **get_runtime_manager** | **get_tool_context_manager** | 导出 |

### 4.2–4.4 主键策略与 RO 调用（历史）

RO 已不在父仓库；若分拆 Tools Server 仍暴露 HTTP，以 `agent_id` + `subagent_id` 路径为准。

---

## 五、原 Phase 3：Gateway `agent_runtimes` 表（归档）

| 选项 | 说明 |
|------|------|
| **保留空表** | 历史部署可能曾采用；**当前 schema 已不再创建该表**。 |
| **DROP** | 已在历史迁移中完成；现行 **v63** 迁移专注于 Entangled 影子表清理等（见 `schema.py`）。 |

---

## 六、原施工顺序与验收（归档）

```
Phase 1 (Gateway)                    Phase 2 (Tools Server)
删除死代码、RuntimeRepository          重命名 RuntimeManager → ToolContextManager
移除 maybe_forward                     context_key 替代 runtime_id
                                      （与 Phase 1 可并行）
```

**父仓库验收要点（现行）**

1. **Gateway**：`helpers.py` 无 `resolve_runtime_ids` / `get_runtime_context` / `maybe_forward`；无 `RuntimeRepository` 模块；schema 无 `agent_runtimes`。
2. **Agent-Runtime**：`tool_handlers` 使用 `scope_id`，兼容 payload 中旧键 `runtime_id`；工具调用走 Gateway Internal 与可选 `tools_server_url`。
3. **端到端**：以当前 `docs/backend-architecture.md` 与部署配置为准。

---

## 七、风险与回滚（历史）

原文档风险表仍可供查阅旧部署；当前回滚策略以数据库备份与 `schema.py` 迁移链为准。

---

## 八、相关文档

- [IMPLEMENTATION-PLAN-runtime-cleanup-subagent-centric.md](./IMPLEMENTATION-PLAN-runtime-cleanup-subagent-centric.md)
- [INVESTIGATION-GATEWAY-RUNTIME-USAGE.md](./INVESTIGATION-GATEWAY-RUNTIME-USAGE.md)
- [ARCHITECTURE-SERVICES-AND-HANDLERS.md](../runbooks/ARCHITECTURE-SERVICES-AND-HANDLERS.md)
- [DESIGN-ELIMINATE-RUNTIME-ROOT-PLAN.md](./DESIGN-ELIMINATE-RUNTIME-ROOT-PLAN.md)
