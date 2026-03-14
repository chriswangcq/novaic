# SubAgent-Centric Gateway 迁移实施文档

## 1. 目标架构

### 1.1 职责划分

| 组件 | 职责 | 对外暴露 |
|------|------|----------|
| **Gateway** | SubAgent 数据源、context 存储、消息队列 | `/internal/subagents/*`（供 Executor、Scheduler 等调用） |
| **RO** | Runtime 执行、LLM 调用、工具执行 | **不对外暴露** `/internal/runtimes/*`；仅调用 Gateway 上报 API |
| **Tools Server Executor** | 执行 subagent_* 工具 | 只调 Gateway，不调 RO |

### 1.2 数据流

```
Executor (subagent_list/history/send)
    → Gateway /internal/subagents/*

RO (执行过程中)
    → Gateway POST /internal/subagents/{agent_id}/{subagent_id}/context/append  (context 增量)
    → Gateway PATCH /internal/subagents/{agent_id}/{subagent_id}  (status 等更新)

subagent_send 投递路径：
    Executor → Gateway /internal/subagents/{agent_id}/{subagent_id}/send
    → Gateway 写入 chat_messages (type=SUBAGENT_SEND, status=sending)
    → Watchdog 消费 → MessageProcess Saga → 投递到目标 SubAgent
```

---

## 2. Gateway 变更

### 2.1 新增/调整表结构

**subagents 表**（已有，需确认字段）：
- `subagent_id`, `agent_id`, `type`, `parent_subagent_id`
- `status` (sleeping/awake/summarizing/running/completed/failed/cancelled)
- `historical_summary`, `wake_triggers`, `handoff_notes`, `wake_at`
- `task`, `progress`, `result`, `error`, `timeout_at`
- `hrl`, `summary_lock`, `need_rest`
- **不存储** `runtime_id`（Gateway 不感知 runtime）

**新增：subagent_context 表**（用于 history API）

```sql
CREATE TABLE IF NOT EXISTS subagent_context (
    id TEXT PRIMARY KEY,
    agent_id TEXT NOT NULL,
    subagent_id TEXT NOT NULL,
    seq INTEGER NOT NULL,           -- 顺序号，用于 append 顺序
    message_type TEXT NOT NULL,    -- assistant/user/tool_result 等
    content TEXT,                  -- JSON
    round_id TEXT,
    created_at TEXT NOT NULL,
    UNIQUE(agent_id, subagent_id, seq)
);
CREATE INDEX idx_subagent_context_lookup ON subagent_context(agent_id, subagent_id, seq);
```

- RO 通过 append 接口推送增量，Gateway 按 seq 写入
- `subagent_history` 查询此表

### 2.2 Gateway 新增 API（供 Executor 调用）

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/internal/subagents/list` | 列出 active SubAgents，仅返回 subagent 维度：`subagent_id`, `agent_id`, `type`, `status`, `created_at` 等，**不含 runtime_id** |
| GET | `/internal/subagents/{agent_id}/{subagent_id}/history` | 查询 SubAgent 的 context 历史（分页：limit, offset） |
| POST | `/internal/subagents/{agent_id}/{subagent_id}/send` | 发送消息给 SubAgent；写入 chat_messages，status=sending，由 Watchdog 消费 |

### 2.3 Gateway 新增 API（供 RO 上报）

| 方法 | 路径 | 说明 |
|------|------|------|
| POST | `/internal/subagents/{agent_id}/{subagent_id}/context/append` | RO 追加 context 增量（单条或多条 message） |
| PATCH | `/internal/subagents/{agent_id}/{subagent_id}` | RO 更新 status 等字段；建议拆分为更细粒度接口（见下） |

**RO 上报拆分建议**（按 API 需求设计）：

| 接口 | 用途 | 典型字段 |
|------|------|----------|
| `POST .../context/append` | 每轮结束推送 context 增量 | `messages: [{role, content, ...}]` |
| `PATCH .../status` | 更新 status | `status`, `phase`? |
| `PATCH .../progress` | 更新 progress（Sub SubAgent） | `progress` |
| `PATCH .../round` | 更新 round 信息（如需要） | `current_round_num`, `current_round_id` |
| `PATCH .../summary` | 完成时更新 summary | `simple_summary`, `hot_summary`, `cold_summary` |

可根据实际需求合并或再拆。

---

## 3. subagent_send 投递路径

1. **Executor** 调用 `POST /internal/subagents/{agent_id}/{subagent_id}/send`，body: `{ "message": "..." }`
2. **Gateway** 创建 `chat_messages` 记录：
   - `type`: `SUBAGENT_SEND`（新增类型）
   - `content`: 消息内容
   - `metadata`: `{ "target_subagent_id": "...", "sender_subagent_id": "..." }`
   - `status`: `sending`
3. **Watchdog** 轮询 `find_sending`，发现 `SUBAGENT_SEND`
4. **Watchdog** 创建 `message_process` Saga，context：
   - `subagent_id`: 目标 subagent_id
   - `trigger_type`: `subagent_send`
   - `message_id`: ...
5. **MessageProcess Saga** 走现有流程：`get_or_create_runtime` → 将消息 append 到 runtime context → 触发 `runtime_start` 或 ReactThink

---

## 4. RO 变更

### 4.1 停用对外暴露

- **删除或停用** RO 的 `/internal/runtimes/*` 对外路由（不再被 Executor、Tools Server 等直接调用）
- 保留 RO 内部对 runtime 的 CRUD（用于自身执行逻辑）

### 4.2 新增：RO → Gateway 上报调用

RO 在以下时机调用 Gateway 上报 API：

| 时机 | 调用 |
|------|------|
| 每轮结束（context 有更新） | `POST .../context/append` |
| status 变更 | `PATCH .../status` 或等价 |
| Sub SubAgent progress 更新 | `PATCH .../progress` |
| Runtime 完成（summary 生成后） | `PATCH .../summary` |

- RO **不**从 Gateway 拉取 context；context 以 RO 为准，RO 主动 push 增量给 Gateway

### 4.3 RO 内部

- 继续使用 `agent_runtimes` 表存储 runtime 与 context
- 执行逻辑不变，仅在上述时机增加对 Gateway 的上报调用

---

## 5. Tools Server Executor 变更

| 工具 | 原调用 | 新调用 |
|------|--------|--------|
| `subagent_list` | `GET /internal/runtimes/list` | `GET /internal/subagents/list` |
| `subagent_history` | 先解析 runtime_id，再 `POST /internal/runtimes/{id}/history` | `GET /internal/subagents/{agent_id}/{subagent_id}/history` |
| `subagent_send` | 先解析 runtime_id，再 `POST /internal/runtimes/{id}/send` | `POST /internal/subagents/{agent_id}/{subagent_id}/send` |
| `subagent_rest` | `POST /internal/subagents/{agent_id}/{subagent_id}/rest` | 不变（已是 Gateway） |

Executor 只调 Gateway，不再依赖 RO 的 `/internal/runtimes/*`。

---

## 6. 迁移步骤（一次性切到新架构）

### Phase 1：Gateway 能力就绪

1. 新增 `subagent_context` 表及 migration
2. 实现 Gateway API：
   - `GET /internal/subagents/list`（仅 subagent 维度，不含 runtime_id）
   - `GET /internal/subagents/{agent_id}/{subagent_id}/history`
   - `POST /internal/subagents/{agent_id}/{subagent_id}/send`
   - `POST /internal/subagents/{agent_id}/{subagent_id}/context/append`
   - `PATCH /internal/subagents/{agent_id}/{subagent_id}`（或拆分的 status/progress/summary 等）

### Phase 2：Watchdog 支持 SUBAGENT_SEND

1. 在 Watchdog 中增加对 `SUBAGENT_SEND` 的处理分支
2. 创建 `message_process` Saga，`trigger_type=subagent_send`

### Phase 3：RO 上报

1. 在 RO 执行流程中，在每轮结束、status 变更、summary 完成等时机调用 Gateway 上报 API
2. 确保 `context/append` 的幂等（如用 round_id + seq 去重）

### Phase 4：Executor 切到 Gateway

1. 修改 Executor：`subagent_list`、`subagent_history`、`subagent_send` 全部改为调用 Gateway 新 API
2. 移除对 RO `/internal/runtimes/*` 的依赖

### Phase 5：停用 RO 对外 /internal/runtimes/*

1. 从 Gateway 的 proxy 配置中移除对 RO `/internal/runtimes/*` 的转发（若 Gateway 曾转发）
2. 从 RO 的路由中移除或禁用对外暴露的 `/internal/runtimes/*`（保留 RO 内部使用）
3. 确认无其他服务直接调用 RO 的 `/internal/runtimes/*`

---

## 7. 依赖关系检查

迁移前需确认：

- **Tools Server**：仅通过 Gateway 访问 subagent 相关能力
- **Scheduler**：`due-wake` 等是否已走 Gateway
- **agent-runtime**（Watchdog、Saga、Task Worker）：通过 Gateway 的 messages、subagents 等 API，不直接依赖 RO 的 runtimes

---

## 8. 回滚预案

若迁移后出现问题：

1. Executor 可临时回退到「通过 Gateway 转发到 RO」的旧路径（若 Gateway 仍保留转发）
2. 或保留 RO 的 `/internal/runtimes/*` 一段时间，通过配置开关在「新路径」与「旧路径」间切换

---

## 9. 已知限制与说明

### 9.1 subagent_history 与 RO context 的时序差

`subagent_history` 依赖 Gateway 的 `subagent_context`，由 RO 在 append 时异步推送。若 RO 推送失败或延迟，`subagent_history` 可能返回空或滞后。用户刚完成一轮对话后立刻查 history，可能看不到最新消息。若需强一致，可考虑同步等待推送完成（会增加延迟，不推荐默认开启）。

### 9.2 subagent_send 在目标已有 active runtime 时的投递

目标 subagent 已有 active runtime 时，`message_process` 返回 `action=skip_active`，不会触发 `runtime_start`。消息依赖 ReactThink 的 `context.read` 被消费。ReactThink 在每轮 think 前会调用 `context.read`，消息会在下一轮被处理。若 ReactThink 长时间不执行（如等待工具调用），消息会延迟到达。

---

## 10. 附录：现有相关组件

- **Gateway subagents**：`gateway/db/repositories/subagent.py`，`gateway/api/internal/subagent.py`
- **Gateway messages**：`gateway/db/repositories/message.py`，`gateway/api/internal/message.py`
- **Watchdog**：`novaic-agent-runtime/task_queue/workers/watchdog_sync.py`
- **MessageProcess Saga**：`novaic-agent-runtime/task_queue/sagas/message_process.py`
- **RO context append**：`novaic-runtime-orchestrator/gateway/api/internal/runtime.py`（`append_runtime_context`）
- **Executor**：`novaic-tools-server/tools_server/executor.py`
