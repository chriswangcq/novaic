# 审查报告：Tools Server 摘除 Runtime/RO 后的代码审查

## 一、审查范围

1. **Diff 逻辑**：`get_quadrant_task_board` 等 API 调用参数是否正确
2. **Gateway**：是否还有 runtime 相关逻辑残留
3. **Tools Server**：是否还有 runtime 相关逻辑残留

---

## 二、Diff 逻辑审查

### 2.1 问题与修复

| 位置 | 问题 | 修复 |
|------|------|------|
| `novaic-tools-server/task_queue/utils/system_prompt.py` | `get_quadrant_task_board(runtime_id)` 错误：接口已改为 agent 维度，应传 `agent_id` | 改为 `get_quadrant_task_board(agent_id)`，并移除多余的 `get_main_subagent` 调用 |
| `novaic-tools-server/task_queue/client.py` | `GatewayInternalClient.__init__` 仍保留未使用的 `internal_url` 参数 | 删除 `internal_url` 参数 |

### 2.2 修复后逻辑

```python
# system_prompt.py - 修复前
main_subagent = client.get_main_subagent(agent_id)
if main_subagent:
    runtime_id = main_subagent.get("runtime_id")
    if runtime_id:
        board_result = client.get_quadrant_task_board(runtime_id)

# system_prompt.py - 修复后
board_result = client.get_quadrant_task_board(agent_id)
```

`get_quadrant_task_board` 已改为调用 `/internal/agents/{agent_id}/quadrant-tasks/board`，直接传 `agent_id` 即可。

---

## 三、Gateway 中的 runtime 逻辑

### 3.1 已移除

- **internal_proxy**：已移除 `/internal/runtimes/*`、`/internal/rt/*` 代理

### 3.2 保留（合理）

| 模块 | 说明 |
|------|------|
| **subagent.py** | 通过 `maybe_forward_to_runtime_orchestrator` 将部分请求（due-wake、hrl、merge-history 等）转发到 RO，属于 Gateway 作为入口的职责 |
| **message.py** | 同样使用 `maybe_forward` 转发 |
| **schema.py** | 保留 `agent_runtimes` 表（v40 已清空，Gateway 不再拥有 runtime 数据） |
| **RuntimeRepository** | 仍存在，用于 Gateway 本地 subagent 相关逻辑 |

**结论**：Gateway 不再直接拥有 runtime 生命周期管理，仅作为入口转发部分请求到 RO，符合架构预期。

---

## 四、Tools Server 中的 runtime 逻辑

### 4.1 已摘除

| 项目 | 状态 |
|------|------|
| RUNTIME_ORCHESTRATOR_URL 依赖 | ✅ 已移除 |
| runtime_handlers、context_handlers 注册 | ✅ 已注释 |
| internal_url、直连 RO | ✅ 已移除 |
| get_quadrant_task_board 参数 | ✅ 已改为 agent_id |

### 4.2 保留（死代码或无关）

| 模块 | 说明 |
|------|------|
| **task_queue/client.py** | 仍保留 `get_runtime`、`create_runtime`、`append_context` 等 runtime API 方法，但仅被 task_queue handlers 使用；handlers 已不注册，为死代码 |
| **task_queue/handlers/runtime_handlers.py** | 已不注册，死代码 |
| **task_queue/handlers/context_handlers.py** | 已不注册，死代码 |
| **tools_server/runtime_manager.py** | `RuntimeContext`、`RuntimeManager` 用 `runtime_id` 做内存管理，属于**工具调用上下文**（如 `rt-{agent_id}-{subagent_id}`），与 RO 的 runtime 无关 |
| **tools_server/api.py** | `runtime_id` 用于构造工具调用上下文 key，与 RO 无关 |

**结论**：Tools Server 实际执行路径（HTTP API 层）已无 runtime/RO 依赖。`runtime_handlers.py`、`context_handlers.py` 已删除。

---

## 五、修复清单

| # | 修复项 | 状态 |
|---|--------|------|
| 1 | system_prompt.py：`get_quadrant_task_board(agent_id)` | ✅ 已修复 |
| 2 | GatewayInternalClient：移除 `internal_url` 参数 | ✅ 已修复 |
| 3 | 删除 runtime_handlers.py、context_handlers.py | ✅ 已删除 |

---

## 六、Gateway 能否不保留 runtime 逻辑？

**结论：可以移除，但需按施工计划执行，改动较大。**

### 6.1 当前 Gateway 的 runtime 依赖

| 模块 | 用途 |
|------|------|
| `maybe_forward_to_runtime_orchestrator` | 仅转发 `/internal/runtimes`、`/internal/rt/` 到 RO；subagent/message 路径不匹配，走本地逻辑 |
| `RuntimeRepository`、`agent_runtimes` | `resolve_runtime_ids`、`get_runtime_context` 被 self_drive、llm、task、config 等大量 internal API 使用；v40 已清空表，RO 模式下数据在 RO 侧 |
| `message.py` | INTERRUPT 时 `UPDATE agent_runtimes` |
| `subagent.py` | `/status` 用 `runtime_repo.get_latest_runtimes` |

### 6.2 移除路径

参考 [IMPLEMENTATION-PLAN-runtime-cleanup-subagent-centric.md](./IMPLEMENTATION-PLAN-runtime-cleanup-subagent-centric.md)：

1. **Phase 1**：Gateway 实现 subagent 维度 API（`/internal/subagents/{agent_id}/{subagent_id}/tool-context` 等）
2. **Phase 2**：Tools Server 改为 subagent 维度，不再调用 runtime API
3. **Phase 3**：Gateway 删除 `agent_runtimes`、`RuntimeRepository`、`resolve_runtime_ids`、`get_runtime_context`，所有 internal API 改为 subagent 维度或直连 RO

当前该计划尚未实施。

---

## 七、相关文档

- [IMPLEMENTATION-PLAN-tools-server-remove-runtime-ro.md](./IMPLEMENTATION-PLAN-tools-server-remove-runtime-ro.md) - Tools Server 摘除方案
- [IMPLEMENTATION-PLAN-runtime-cleanup-subagent-centric.md](./IMPLEMENTATION-PLAN-runtime-cleanup-subagent-centric.md) - Gateway 去 runtime 施工计划
- [ARCHITECTURE-SERVICES-AND-HANDLERS.md](./ARCHITECTURE-SERVICES-AND-HANDLERS.md) - 服务与 Handler 架构
