# forward_to_runtime_orchestrator 相关 API 调用方全项目调研

> 分工调研文档，可派多人并行完成

---

## 一、调研目标

1. `forward_to_runtime_orchestrator` 转发的 API 是否有真实调用方？
2. 前端/Desktop/Tauri 实际调用的是哪些路径？
3. 是否存在路径重复（如 /api/chat vs /api/chat/send）？
4. RO 未实现的路径（/internal/messages、/internal/chat/*、/internal/agents/*/interrupt）若转发会 404，为何系统能工作？

---

## 二、API 路径对照表（需核实）

| Gateway 路由 | 实现位置 | 是否 forward 到 RO | RO 是否实现 |
|-------------|----------|-------------------|-------------|
| POST /api/chat | routes.py | ✅ → /internal/messages | ❌ |
| POST /api/chat/stream | routes.py | ✅ → /internal/messages | ❌ |
| GET /api/history | routes.py | ✅ → /internal/chat/history | ❌ |
| POST /api/clear | routes.py | ✅ → /internal/chat/clear | ❌ |
| POST /api/interrupt | routes.py | ✅ → /internal/agents/{id}/interrupt | ❌ |
| POST /api/chat/send | main_gateway.py | ❌ 本地 | - |
| GET /api/chat/history | main_gateway.py | ❌ 本地 | - |
| POST /api/agent/interrupt | main_gateway.py | ❌ 本地 | - |

---

## 三、分工任务

### 任务 A：前端 (novaic-app) 调用链

**负责人**：_______

**范围**：`novaic-app/src/` 下所有 `gateway_get`、`gateway_post`、`invoke` 调用

**需回答**：
1. 前端实际调用的 chat 相关路径有哪些？（/api/chat、/api/chat/send、/api/chat/history、/api/chat/messages 等）
2. 前端调用的 interrupt 路径是 `/api/interrupt` 还是 `/api/agent/interrupt`？
3. 前端是否调用 `/api/clear`、`/api/history`？
4. `api.clearHistory()`、`api.interrupt()`、`api.interruptAgent()` 分别被哪些组件使用？

**关键文件**：
- `src/services/api.ts`
- `src/store/index.ts`
- `src/components/**/*.tsx`

---

### 任务 B：Desktop / Tauri 命令与 agent_commands

**负责人**：_______

**范围**：`novaic-app/src-tauri/` 下所有 Gateway 调用

**需回答**：
1. `agent_commands.rs` 中 curl 调用 `/api/chat`、`/api/chat/stream` 的使用场景？
2. 是否有其他 Tauri 命令或 Rust 代码直接调用 Gateway？
3. `gateway_get`、`gateway_post` 的 Tauri 实现如何路由到 Gateway？

**关键文件**：
- `src-tauri/src/commands/agent_commands.rs`
- `src-tauri/src/main.rs`（gateway_get、gateway_post）

---

### 任务 C：agent-runtime (Worker/Watchdog) 对 internal API 的调用

**负责人**：_______

**范围**：`novaic-agent-runtime/` 下 task_queue、watchdog、workers

**需回答**：
1. agent-runtime 的 `gateway_client` 调用 `/internal/messages/*`、`/internal/chat/*` 时，目标 URL 是 Gateway 还是 RO？
2. `UnifiedInternalClient` 或 `TaskQueueClient` 的 `_request` 如何根据 path 选择 GATEWAY_URL vs RUNTIME_ORCHESTRATOR_URL？
3. Watchdog 的 `find_sending_message`、`claim_message` 等发往哪里？

**关键文件**：
- `task_queue/client.py`
- `task_queue/workers/watchdog_sync.py`
- `task_queue/workers/task_worker_sync.py`

---

### 任务 D：Gateway 内部路由结构（重复路径核实）

**负责人**：_______

**范围**：`novaic-gateway/main_gateway.py`、`gateway/api/routes.py`、`gateway/api/internal/`

**需回答**：
1. `api_router`（routes.py）与 `main_gateway.py` 中直接 `@app.xxx` 的路由，是否有路径冲突？
2. `/api/chat` 与 `/api/chat/send` 是否都被注册？请求会命中哪个？
3. `forward_to_runtime_orchestrator` 的 7 处调用，对应的入口路径分别是什么？

**关键文件**：
- `main_gateway.py`（include_router、@app 路由）
- `gateway/api/routes.py`
- `gateway/api/internal/message.py`

---

### 任务 E：RO 实际暴露的 internal 路由

**负责人**：_______

**范围**：`novaic-runtime-orchestrator/gateway/api/internal/`

**需回答**：
1. RO 的 internal_router 完整路由列表（runtime、subagent 下的所有 path）
2. 确认 RO 是否**没有** `/internal/messages`、`/internal/chat/history`、`/internal/chat/clear`、`/internal/agents/{id}/interrupt`
3. 若 Gateway 转发到这些路径，RO 会返回 404 还是其他？

**关键文件**：
- `gateway/api/internal/__init__.py`
- `gateway/api/internal/runtime.py`
- `gateway/api/internal/subagent.py`

---

### 任务 F：agents.py 中 forward 的调用场景

**负责人**：_______

**范围**：`novaic-gateway/gateway/api/agents.py`

**需回答**：
1. Agent 创建后发送 SYSTEM_WAKE 的入口：哪个 API 触发？
2. `setup_complete` 后发送 SYSTEM_WAKE 的入口：哪个 API 触发？
3. 这些入口是否被前端或 Tauri 使用？

**关键文件**：
- `gateway/api/agents.py`
- 调用 agents 路由的前端/Tauri 代码

---

## 四、已掌握的初步结论（待各任务核实）

| 项目 | 初步结论 | 需核实 |
|------|----------|--------|
| 前端 chat 发送 | 使用 `/api/chat/send`（main_gateway） | 是否还有地方用 `/api/chat` |
| 前端 chat 历史 | 使用 `/api/chat/history`（main_gateway） | 是否还有地方用 `/api/history` |
| 前端 interrupt | 使用 `/api/agent/interrupt`（main_gateway） | `api.interrupt()` 即 `/api/interrupt` 是否有调用方 |
| 前端 clear | `api.clearHistory()` → `/api/clear` | 是否有 UI 调用 clearHistory |
| Desktop 发消息 | agent_commands 用 curl 调 `/api/chat` | 该命令的触发场景 |
| forward 转发的路径 | 发往 RO，但 RO 未实现 | 为何未 404？或实际已 404？ |

---

## 五、输出格式

每个任务完成后，在对应章节下补充：

```markdown
### 任务 X 结论

- 调用方：...
- 实际路径：...
- 是否经过 forward_to_runtime_orchestrator：...
- 异常/矛盾点：...
```

---

## 六、Subagent 调研结论汇总（2025-03 核实）

### Task A：前端调用链
| 路径 | 前端是否使用 | 说明 |
|------|-------------|------|
| `/api/chat/send` | ✅ | sendChatMessage，store:441 |
| `/api/chat/history` | ✅ | getChatHistory，store:313,748,1276，AgentDrawer:62 |
| `/api/chat/messages` | ✅ | SSE EventSource，store:952 |
| `/api/chat/message/{id}` | ✅ | getChatMessage，store:516 |
| `/api/agent/interrupt` | ⚠️ | interruptAgent，store:477（stopExecution），**无 UI 调用 stopExecution** |
| `/api/chat` | ❌ | 未使用 |
| `/api/chat/stream` | ❌ | 未使用 |
| `/api/history` | ❌ | 未使用 |
| `/api/clear` | ❌ | clearHistory 从未被调用 |
| `/api/interrupt` | ❌ | interrupt 从未被调用 |

**Header.tsx 的「清空」按钮**：调用 `clearMessages` 仅清本地 store，不调 `api.clearHistory()`。

---

### Task B：Tauri / agent_commands
- **agent_commands.rs**：curl 调用 `POST /api/chat`、`POST /api/chat/stream` → **死代码**（commands 未在 main.rs 注册）
- **gateway_get/post**：直接转发到 `http://127.0.0.1:19999` + path，路径由前端传入

---

### Task C：agent-runtime gateway_client
- **全部发往 GATEWAY_URL（19999）**，不发往 RO
- Watchdog/TaskWorker 的 `find_sending_message`、`claim_message`、`confirm_message` 等 → Gateway
- `/internal/messages/*`、`/internal/chat/*` 由 `_is_gateway_internal_path` 判定走 gateway_client

---

### Task D：Gateway 路由结构
| 入口路径 | 实现 | forward 到 RO? |
|----------|------|----------------|
| POST /api/chat | routes.py | ✅ → /internal/messages |
| POST /api/chat/stream | routes.py | ✅ → /internal/messages |
| GET /api/history | routes.py | ✅ → /internal/chat/history |
| POST /api/clear | routes.py | ✅ → /internal/chat/clear |
| POST /api/interrupt | routes.py | ✅ → /internal/agents/{id}/interrupt |
| POST /api/chat/send | main_gateway | ❌ 本地 |
| GET /api/chat/history | main_gateway | ❌ 本地 |
| POST /api/agent/interrupt | main_gateway | ❌ 本地 |

**无路径冲突**，`/api/chat` 与 `/api/chat/send` 并存。

---

### Task E：RO 实际路由
- RO **未实现**：`/internal/messages`、`/internal/chat/history`、`/internal/chat/clear`、`/internal/agents/{id}/interrupt`
- 若 Gateway 转发到上述路径 → RO 返回 **404**，`forward_to_runtime_orchestrator` 会抛出 HTTPException

---

### Task F：agents.py forward 调用
| 入口 | 触发场景 | 前端调用方 |
|------|----------|------------|
| POST /api/agents | create_agent → SYSTEM_WAKE | CreateAgentModal, OnboardingFlow |
| PATCH /api/agents/{id} | setup_complete → SYSTEM_WAKE | SetupWorkspace → store.setupAgent |

**两者均被前端使用**，会触发 `forward_to_runtime_orchestrator` → RO `/internal/messages` → **RO 无此路由，会 404**。

---

## 七、关键矛盾与结论

### 矛盾
- **agents.py** 的 create_agent、setup_complete 会 forward 到 RO 的 `/internal/messages`
- **RO 未实现** `/internal/messages`
- 按理创建 Agent、完成 setup 时应 **404**

### 可能原因（待验证）
1. 实际运行中 RO 有该路由（代码与运行版本不一致）
2. 前端/流程未走到 create_agent 或 setup_complete 的 forward 分支
3. 错误被上层吞掉，用户未感知

### 建议
1. **routes.py** 的 5 处 forward（/api/chat、/api/chat/stream、/api/history、/api/clear、/api/interrupt）：**无调用方**，可改为本地调用或删除
2. **agents.py** 的 2 处 forward：**有调用方**，应改为调用 Gateway 本地 `/internal/messages`（或直接调用 message_repo），而非转发到 RO
3. **agent_commands.rs**：死代码，可考虑移除或恢复注册

---

## 九、汇总后的建议

根据 Subagent 调研结果，建议如下：

1. **可删除或改为本地的 forward**：routes.py 中 /api/chat、/api/chat/stream、/api/history、/api/clear、/api/interrupt 无调用方，可改为直接调用 Gateway 本地 internal API
2. **agents.py 必须改**：create_agent、setup_complete 的 forward 有调用方，但 RO 无 /internal/messages，应改为调用 Gateway 本地 message API
3. **RO 无需补充**：/internal/messages、/internal/chat/* 等由 Gateway 实现，agent-runtime 已发往 Gateway
4. **agent_commands.rs**：死代码，可移除或恢复 Tauri 注册

---

## 十、forward_to_runtime_orchestrator 排查结果（2025-03 续）

### 10.1 已完成的修改

| 修改项 | 状态 |
|--------|------|
| routes.py 5 处 forward（chat、chat_stream、history、clear、interrupt） | ✅ 已删除 |
| agents.py 2 处 forward（create_agent、update_agent setup_complete） | ✅ 已改为 MessageRepository.add_message 本地写入 |
| agent_commands.rs | ✅ 已删除（死代码） |

### 10.2 当前剩余调用方

**已全部移除**（2025-03）：

- `GET /api/runtime-orchestrator/health`：已删除，仅被 split 验证脚本使用，无业务价值
- `forward_to_runtime_orchestrator`：已删除，`api/runtime_orchestrator_forward.py` 已移除

### 10.4 main_gateway.py 与 forward 的关系

- **main_gateway.py** 不导入 `forward_to_runtime_orchestrator`
- 启动时通过 `check_runtime_orchestrator_health()` 做 RO 健康检查（直接 HTTP 调用 RO `/api/health`）
- 业务路由（chat、agents 等）已全部改为本地实现，不再转发到 RO
