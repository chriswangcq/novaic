# 设计方案：从根源消灭 Gateway、Tools Server 的 Runtime 逻辑

## 一、目标

1. **Gateway**：彻底移除 runtime 概念，删除 agent_runtimes、RuntimeRepository、resolve_runtime_ids、get_runtime_context、maybe_forward 等
2. **Tools Server**：去除 runtime 命名，统一为 subagent 维度（SubAgentToolContext）
3. **原则**：RO 保留 runtime_id 内部流转；Gateway、Tools Server 仅使用 agent_id + subagent_id

---

## 二、当前状态

### 2.1 已完成

| 项目 | 状态 |
|------|------|
| Gateway self_drive | 已删除 |
| Gateway /rt/{runtime_id}/* 路由 | 已删除 |
| Gateway config/llm/runtime | 已删除 |
| Gateway tool-context API (v42) | 已实现：/subagents/{agent_id}/{subagent_id}/tool-context、tool-ports、with-tools |
| Tools Server task_queue | 已删除 |
| Tools Server 调用 Gateway | 已用 subagent API：tool-context、tool-ports、with-tools |
| Tools Server executor | 已用 /internal/agents/{agent_id}/* |

### 2.2 待清理

**Gateway：**
- `helpers.py`：resolve_runtime_ids、get_runtime_context（死代码，无调用方）
- `helpers.py`：maybe_forward_to_runtime_orchestrator（路径永不匹配，恒返回 None）
- `helpers.py`：_runtime_to_dict（仅 RO 用，Gateway 可删）
- `schema.py`：agent_runtimes 表（v40 已清空）
- `gateway/db/repositories/runtime.py`：RuntimeRepository 整模块
- `_RO_FORWARDED_PREFIXES`、RUNTIME_ORCHESTRATOR_URL 依赖

**Tools Server：**
- `runtime_manager.py`：RuntimeContext、RuntimeManager、runtime_id 命名
- `api.py`、`executor.py`：runtime_id 作为工具上下文 key 的命名

---

## 三、Phase 1：Gateway 彻底移除 Runtime

### 3.1 删除死代码

| 文件 | 删除内容 |
|------|----------|
| **helpers.py** | resolve_runtime_ids、get_runtime_context、_runtime_to_dict |
| **helpers.py** | maybe_forward_to_runtime_orchestrator、_RO_FORWARDED_PREFIXES、set_runtime_orchestrator_process |
| **helpers.py** | RUNTIME_ORCHESTRATOR_URL 相关逻辑 |

### 3.2 移除 maybe_forward 调用

| 文件 | 改动 |
|------|------|
| **message.py** | 删除所有 `maybe_forward_to_runtime_orchestrator` 调用，直接走本地逻辑 |
| **subagent.py** | 同上 |

### 3.3 删除 RuntimeRepository 与 agent_runtimes

| 文件 | 改动 |
|------|------|
| **gateway/db/repositories/runtime.py** | 整文件删除 |
| **gateway/db/repositories/__init__.py** | 移除 RuntimeRepository、AgentRuntime 导出 |
| **schema.py** | 可选：v43 迁移 DROP TABLE agent_runtimes，或保留空表做兼容 |
| **tests** | 移除 RuntimeRepository mock，改用 SubAgentRepository |

### 3.4 清理 Gateway 对 RO 的转发依赖

| 项目 | 说明 |
|------|------|
| **RuntimeOrchestratorClient** | Gateway 的 subagent/agent 路由中，部分会 `client.forward` 到 RO（如 cancel、spawn 的 runtime 操作）。这些是 Gateway 主动调 RO，不是 maybe_forward。保留。 |
| **RUNTIME_ORCHESTRATOR_URL** | Gateway 仍需要它来调用 RO 的 cancel-by-subagent、delete-by-subagent 等。保留。 |
| **maybe_forward** | 删除后，所有请求走本地。Gateway 不暴露 /internal/runtimes、/internal/rt/，无影响。 |

### 3.5 依赖检查

- `_subagent_to_dict`：subagent.py 使用，保留
- `_runtime_to_dict`：Gateway 内无调用方（agent.py 仅 import），可删
- `gateway/api/skills.py`：不用 resolve_runtime_ids、get_runtime_context，仅用 GatewayInternalClient

---

## 四、Phase 2：Tools Server 去除 Runtime 命名

### 4.1 重命名（概念统一）

| 原命名 | 新命名 | 说明 |
|--------|--------|------|
| **RuntimeContext** | **SubAgentToolContext** | 工具上下文，主键为 subagent |
| **RuntimeManager** | **SubAgentToolContextManager** | 或简化为 ToolContextManager |
| **runtime_id**（内部 key） | **context_key** 或 **subagent_key** | `f"{agent_id}:{subagent_id}"` |
| **runtime_manager.py** | **tool_context_manager.py** | 文件名 |
| **get_runtime_manager** | **get_tool_context_manager** | 导出 |

### 4.2 主键策略

- **当前**：`_runtimes: Dict[runtime_id, RuntimeContext]`，`runtime_id = f"rt-{agent_id[:8]}-{subagent_id[:12]}"`
- **目标**：`_contexts: Dict[subagent_key, SubAgentToolContext]`，`subagent_key = f"{agent_id}:{subagent_id}"`
- **兼容**：RO 调用 Tools Server 时传 agent_id + subagent_id，不再传 runtime_id

### 4.3 涉及文件

| 文件 | 改动 |
|------|------|
| **runtime_manager.py → tool_context_manager.py** | 重命名类、变量、方法 |
| **api.py** | 导入改为 get_tool_context_manager，context_key 替代 runtime_id |
| **executor.py** | 同上 |
| **main_tools.py** | init_runtime_manager → init_tool_context_manager |
| **common/config.py** | 移除 RUNTIME_ORCHESTRATOR_URL（若未使用） |

### 4.4 RO 调用 Tools Server

RO 的 MCP client 已传 agent_id + subagent_id，路径为 `/internal/subagents/{agent_id}/{subagent_id}/tools/*`。无需改 RO。

---

## 五、Phase 3：Gateway 删除 agent_runtimes 表（可选）

| 选项 | 说明 |
|------|------|
| **A. 保留空表** | 兼容历史迁移，避免 DROP 风险 |
| **B. v43 迁移 DROP** | 彻底删除，需确认无残留引用 |

建议：Phase 1 完成后观察，若无问题再执行 Phase 3 的 DROP。

---

## 六、施工顺序与依赖

```
Phase 1 (Gateway)                    Phase 2 (Tools Server)
删除死代码、RuntimeRepository          重命名 RuntimeManager → ToolContextManager
移除 maybe_forward                     context_key 替代 runtime_id
                                      （与 Phase 1 可并行）
```

| 阶段 | 任务 | 预估 |
|------|------|------|
| Phase 1 | Gateway 删除 resolve_runtime_ids、get_runtime_context、maybe_forward、RuntimeRepository | 0.5d |
| Phase 2 | Tools Server 重命名 RuntimeManager、RuntimeContext、runtime_id | 0.5d |
| Phase 3 | Gateway DROP agent_runtimes（可选） | 0.5d |

---

## 七、验收标准

1. **Gateway**：无 resolve_runtime_ids、get_runtime_context、RuntimeRepository、maybe_forward
2. **Gateway**：agent_runtimes 表可保留空或 DROP
3. **Tools Server**：无 RuntimeContext、RuntimeManager、runtime_id 命名（或仅注释/文档残留）
4. **Tools Server**：RUNTIME_ORCHESTRATOR_URL 若未使用则移除
5. **端到端**：工具注册、调用、恢复流程正常

---

## 八、风险与回滚

| 风险 | 缓解 |
|------|------|
| Gateway 删除 maybe_forward 后，若有隐藏调用方 | maybe_forward 当前恒返回 None，删除无行为变化 |
| RuntimeRepository 被测试或外部引用 | 全面 grep 确认 |
| Tools Server 重命名影响 RO 调用 | RO 调用路径为 subagent 维度，不受影响 |

---

## 九、相关文档

- [IMPLEMENTATION-PLAN-runtime-cleanup-subagent-centric.md](./IMPLEMENTATION-PLAN-runtime-cleanup-subagent-centric.md)
- [INVESTIGATION-GATEWAY-RUNTIME-USAGE.md](./INVESTIGATION-GATEWAY-RUNTIME-USAGE.md)
- [ARCHITECTURE-SERVICES-AND-HANDLERS.md](./ARCHITECTURE-SERVICES-AND-HANDLERS.md)
