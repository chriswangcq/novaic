# 施工方案：Tools Server 彻底摘除 Runtime 与 RO

## 一、目标

1. **移除 RO 依赖**：Tools Server 不再依赖 RUNTIME_ORCHESTRATOR_URL，不再直连 RO
2. **runtime/context 任务由 RO 处理**：Tools Server 不注册 runtime.*、context.* handlers
3. **统一入口**：所有 internal API 调用经 Gateway。Gateway 已移除 /internal/runtimes/* 代理，应使用 subagent/agent API

---

## 二、已实施（v1）

### Phase 1：Client 改造 ✅

| 步骤 | 状态 |
|------|------|
| 1.1 | 删除 `internal_url`、`RUNTIME_ORCHESTRATOR_URL` 依赖 ✅ |
| 1.2 | `_request`：所有请求统一使用 `gateway_url` ✅ |
| 1.3 | get_quadrant_task_board 改为 `/internal/agents/{agent_id}/quadrant-tasks/board` ✅ |
| 1.4 | 删除死代码：get_growth_log、get_drive_config、get_self_drive_state ✅ |
| 1.5 | main_tools.py：移除 `--runtime-orchestrator-url` ✅ |

### Phase 4：Runtime Handler 迁移 ✅

| 步骤 | 状态 |
|------|------|
| 4.1 | Tools Server：取消注册 runtime_handlers、context_handlers ✅ |
| 4.2 | RO：保留 runtime/context handlers，由 RO worker 处理 ✅ |

### Phase 6：配置与启动清理 ✅

| 步骤 | 状态 |
|------|------|
| 6.1 | main_tools.py：删除 `--runtime-orchestrator-url` ✅ |
| 6.3 | README、fail_path 脚本：移除 RUNTIME_ORCHESTRATOR_URL 相关 ✅ |

---

## 三、Gateway 与 runtime API

Phase 4 已移除 Gateway 对 `/internal/runtimes/*`、`/internal/rt/*` 的代理。Tools Server 应使用 subagent/agent 维度 API。**novaic-agent-runtime 允许内部直连 RO**，保留 RUNTIME_ORCHESTRATOR_URL，runtime API 由 agent-runtime 直连 RO 调用。

---

## 四、验收标准

1. ✅ Tools Server 启动无需 RUNTIME_ORCHESTRATOR_URL
2. ✅ GatewayInternalClient 仅使用 GATEWAY_URL
3. 工具执行、LLM 调用、system prompt 等流程正常（需集成测试）
4. ✅ 无对 RO 的直连调用
5. ✅ get_quadrant_task_board 使用 agent 维度 API

---

## 五、待办（可选）

- Phase 3：Payload 改造（agent_id + subagent_id 优先，减少 get_runtime fallback）
- Phase 5：RuntimeManager 去 runtime 化
