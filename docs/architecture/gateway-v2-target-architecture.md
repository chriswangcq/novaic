# Gateway v2 - 终态架构设计

> 基于对 watchdog_sync.py、message_process saga、react_think/react_actions saga、
> subagent_rest saga、context_handlers.py、cortex_handlers.py、runtime_handlers.py、
> message_handlers.py、subagent_handlers.py、tool_handlers.py、queue_service/routes.py、
> novaic-cortex/proxy.py (GatewayProxy)、novaic-cortex/tool_schemas.py 的完整源码审计。

---

## 0. 当前真实架构

先把现在到底怎么跑的画清楚，不带任何简化。

### 0.1 完整触发链

```
[入口层]
  前端发消息 -> Entangled 持久化 -> Gateway 也写 chat_messages(status=sending)
  Scheduler 定时检查 -> Gateway inject_wake -> 写 chat_messages(status=sending)
  Worker 完成子任务 -> Gateway inject_subagent_completed -> 写 chat_messages(status=sending)

[Watchdog 轮询层]
  Watchdog 每 0.1s -> Gateway.find_sending() -> 找到一条 sending 消息
  -> 如果是 INTERRUPT: 直接调 Queue cancel-all -> confirm -> 结束
  -> 其余类型: confirm -> 检查 subagent 状态 -> 可能启动 subagent_wake saga

[Saga 执行层 (ReAct 循环)]
  subagent_wake:
    session_init (Cortex 建 scope) -> set_subagent_awake (Gateway) -> trigger react_think

  react_think:
    prepare_context (Cortex + 从 Gateway 读未读消息合并) -> call_llm -> save_response
    -> 有 tool_calls -> trigger react_actions
    -> 没有 tool_calls + 第一次 -> retry react_think
    -> 没有 tool_calls + 已经 retry -> trigger subagent_rest

  react_actions:
    parallel execute_tools -> parallel save_results
    -> check_continue (从 Gateway 查 has_new_messages + need_rest)
    -> 有新消息 或 不需要休息 -> trigger react_think
    -> 无新消息 且 need_rest -> trigger subagent_rest

  subagent_rest:
    generate_summary -> cortex_scope_end -> set_sleeping/completed (Gateway)
    -> notify_parent (Gateway inject_subagent_completed) -> destroy_mcp
```

### 0.2 Gateway 被 Worker 回调的完整清单

从源码 grep 出的每一处 `gateway_client.*` 调用:

| 调用 | 文件 | 性质 |
|---|---|---|
| `find_sending_message()` | watchdog_sync.py | **轮询**: 寻找待处理消息 |
| `confirm_message(id)` | watchdog_sync.py | **CAS**: sending -> sent |
| `set_subagent_awake(a, s)` | watchdog_sync.py, subagent_handlers.py, message_handlers.py | **CAS**: sleeping -> awake, 返回 previous_status |
| `set_subagent_sleeping(a, s)` | subagent_handlers.py | **写入**: 设为 sleeping |
| `set_subagent_completed(a, s)` | subagent_handlers.py | **写入**: 设为 completed |
| `claim_message(id)` | message_handlers.py | **CAS**: sending -> sent |
| `inject_subagent_completed_message(...)` | message_handlers.py | **写入**: 塞一条新 sending 消息 |
| `inject_wake_message(...)` | scheduler_worker_sync.py | **写入**: 塞一条新 sending 消息 |
| `get_unread_sent_messages(agent_id)` | context_handlers.py | **读取**: 获取未读消息列表 |
| `mark_messages_read([ids])` | context_handlers.py | **写入**: 标记已读 |
| `has_new_messages(agent_id)` | runtime_handlers.py | **读取**: 判断有无新消息 |
| `check_and_clear_need_rest(a, s)` | runtime_handlers.py | **CAS**: 原子读取 + 清除 need_rest |
| `increment_drive_interaction(a)` | watchdog_sync.py | **写入**: 交互计数 |
| `get_due_for_wake()` | scheduler_worker_sync.py | **读取**: 查到期的 subagent |

### 0.3 Cortex BusinessProxy -> Business 的工具代理调用链

> **⚠️ 2026-04-16 更新**：Cortex 已从 `GatewayProxy` 重命名为 `BusinessProxy`，直接指向 Business Service (:19998)，不再经 Gateway 中转。

除了 Worker 回调外, **Cortex 还有一条独立的 Business 依赖**。

Cortex 内部的 `BusinessProxy` 类在 Agent 执行工具时, 把 12 种命令全部代理转发到 Business 的 `/internal/` 端点:

| 命令 | 目标 Business 端点 | 性质 |
|---|---|---|
| memory (save/recall/delete) | `/internal/agents/{id}/memory/*` | 有状态工具 |
| notebook (write/read/update/list) | `/internal/agents/{id}/notebook/*` | 有状态工具 |
| chat (reply) | `/internal/agents/{id}/chat/event` | **消息写入** |
| task (CRUD) | `/internal/agents/{id}/quadrant-tasks/*` | 有状态工具 |
| browser/screenshot/keyboard/mouse | `/internal/agents/{id}/vm/*` | VM 操作代理 |
| shell_exec | `/internal/agents/{id}/vm/shell` | VM 操作代理 |
| qemu | `/internal/agents/{id}/qemu/*` | VM 操作代理 |
| subagent (spawn/status/cancel/report) | `/internal/agents/{id}/subagent/*` | 子 Agent 管理 |
| search | `/internal/agents/{id}/memory/recall` | 记忆检索 |

**这些端点不在本次改造范围内**, 但需注意:
- `chat/event` (AGENT_REPLY): Agent 回复消息也是通过 BusinessProxy -> Business 写入 chat_messages。终态应改为 Worker 直接写 Entangled, 但需要先迁移 HEARTBEAT_OK 过滤和附件处理逻辑。
- VM 相关操作: Business 转发到 Device Service，CloudBridge WS 在 Device Service (:19993) 上，Gateway 不参与此链路。
- 工具 API (memory/notebook/task): 中期由 Cortex 直连对应后端服务替代。

### 0.4 `subagent_rest` 的两层机制

`subagent_rest` 在系统中存在于**两个不同的层面**, 容易混淆:

**第一层: LLM 工具调用 (Agent 主动说 "我要休息")**
```
LLM 输出 tool_call: subagent_rest(reason="任务完成")
  -> tool_handlers.py: _exec_subagent_rest()
  -> 调 Gateway: POST /internal/subagents/{a}/{s}/rest
  -> Gateway 只是设了一个标志: need_rest = 1, wake_at = now + 30min
  -> Agent 此时并没有真的休息, react_actions 循环继续!
```

**第二层: Saga 编排 (实际执行休息流程)**
```
react_actions 循环的 check_continue 步骤:
  -> 查 Gateway: has_new_messages? -> 没有
  -> 查 Gateway: check_and_clear_need_rest? -> 是的 (need_rest=1, 原子清除)
  -> 判定 should_complete = true
  -> 触发 subagent_rest saga (5 步清理)
```

所以 `subagent_rest` saga 做的事**不只是 Cortex scope_end**, 它是一个编排 saga 协调 5 个组件的清理:

| 步骤 | 做什么 | 属于谁 | v2 终态 |
|---|---|---|---|
| generate_summary | 调 LLM 生成摘要 | Cortex | 不变 |
| cortex_scope_end | 归档 context 到 /ro/scopes/ | Cortex | 不变 |
| set_sleeping/completed | 改 subagent 状态 | Gateway | -> **Entangled** |
| notify_parent | 注入 sending 消息通知父 Agent | Gateway | -> **Queue dispatch** |
| destroy_mcp | 销毁 MCP Server | Runtime 资源管理 | 不变 |
| session_ended (新增) | 通知 Queue 清理 Session | - | **Queue Service** |

Cortex 的 `scope_end` 只覆盖了步骤 1-2。步骤 3-6 仍需 saga 编排保证顺序。

---

## 1. 设计原则

1. **一处写、多处读** -- 每类数据有且仅有一个写入源
2. **CAS 归属唯一服务** -- 需要原子操作的, 集中到一个有 SQLite 事务的进程里
3. **事件驱动替代轮询** -- 消灭 Watchdog 的 0.1s 扫描循环
4. **Session 排他性** -- 每个 agent+subagent 同时最多一个活跃 Session, 这个不变量由一个地方保证

---

## 2. 数据归属重新划分

### 2.1 三类数据的归宿

| 数据类别 | 现在在哪 | 终态归属 | 理由 |
|---|---|---|---|
| **聊天消息** (chat_messages) | Gateway DB + Entangled 双写 | **Entangled 唯一** | 前端需要实时同步, Worker 需要读取, 只写一份 |
| **SubAgent 实体状态** (status, wake_at, need_rest) | Gateway DB + Entangled 双写 | **Entangled 唯一** | 前端需要显示, Worker 需要读取 |
| **Session 路由决策** ("要不要启动新 Saga") | Gateway 的 CAS (set_subagent_awake) | **Queue Service 独占** | 这是调度决策, 必须原子, 和 Saga 生命周期天然绑定 |

### 2.2 CAS 操作的归宿

现在有三个 CAS 操作散落在 Gateway:

| CAS 操作 | 用途 | 终态 |
|---|---|---|
| `set_subagent_awake` (返回 previous_status) | 防止多条消息并发各自启动 Session | **Queue Service dispatch 内部实现** |
| `confirm_message` (sending -> sent) | 消息去重 | **消灭** (不再有 sending 状态) |
| `check_and_clear_need_rest` | 原子判定 "要不要休息" | **Worker 本地判断** (Session 排他性保证此刻只有一个 Worker 在操作这个 subagent) |

关于 `check_and_clear_need_rest`: 因为 Queue Service 保证了同一个 agent+subagent 只有一个活跃 Session, 所以在 Session 执行期间, 没有第二个进程会并发修改 `need_rest`。Worker 可以安全地: 读 Entangled -> 判断 -> 写回 Entangled, 不需要 CAS。

---

## 3. Queue Service 新增: Session Coordinator

Queue Service 已经有 SQLite, 已经管理 Saga 生命周期。给它加一层 Session 概念是自然延伸。

### 3.1 新增数据结构

```sql
-- Session 追踪 (内存表 + 可从 sagas 表重建)
-- 保证每个 agent+subagent 最多一个活跃 Session
CREATE TABLE IF NOT EXISTS active_sessions (
    session_key TEXT PRIMARY KEY,         -- "{agent_id}:{subagent_id}"
    saga_id TEXT NOT NULL,                -- 当前关联的 saga_id
    scope_id TEXT NOT NULL,
    created_at TEXT NOT NULL
);

-- 待处理触发器 (持久化, 防止竞态窗口丢消息)
CREATE TABLE IF NOT EXISTS pending_triggers (
    id TEXT PRIMARY KEY,
    session_key TEXT NOT NULL,            -- "{agent_id}:{subagent_id}"
    agent_id TEXT NOT NULL,
    subagent_id TEXT NOT NULL,
    user_id TEXT,
    trigger_type TEXT NOT NULL,           -- user_message / system_wake / subagent_completed / spawn_subagent
    metadata TEXT,                        -- JSON
    created_at TEXT NOT NULL
);
-- 同一个 session_key 只保留最新一条, 旧的被覆盖
CREATE UNIQUE INDEX IF NOT EXISTS idx_pending_session ON pending_triggers(session_key);
```

### 3.2 新增 API

#### `POST /api/queue/dispatch`

所有想触发 Agent 行动的操作, 统一走这个入口。

```python
def dispatch(agent_id, subagent_id, user_id, trigger_type, metadata):
    session_key = f"{agent_id}:{subagent_id}"

    with db.transaction():
        # 1. 检查是否有活跃 Session
        active = db.get("active_sessions", session_key)

        if active:
            # 有活跃 Session -> 缓冲触发器
            # (正在运行的 react_think 下一轮 prepare_context 会从 Entangled 读到新消息)
            db.upsert("pending_triggers", {
                "id": uuid4(),
                "session_key": session_key,
                "agent_id": agent_id,
                "subagent_id": subagent_id,
                "user_id": user_id,
                "trigger_type": trigger_type,
                "metadata": json.dumps(metadata),
                "created_at": utc_now(),
            })
            return {"action": "buffered"}

        # 2. 没有活跃 Session -> 创建 subagent_wake Saga
        scope_id = str(uuid4())
        saga_id = orchestrator.create(
            saga_type="subagent_wake",
            context={
                "agent_id": agent_id,
                "subagent_id": subagent_id,
                "user_id": user_id,
                "scope_id": scope_id,
                "trigger_type": trigger_type,
                **metadata,
            },
            idempotency_key=f"session-{session_key}-{scope_id}",
        )

        # 3. 登记活跃 Session
        db.insert("active_sessions", {
            "session_key": session_key,
            "saga_id": saga_id,
            "scope_id": scope_id,
            "created_at": utc_now(),
        })

        return {"action": "saga_started", "saga_id": saga_id, "scope_id": scope_id}
```

**原子性保证**: 整个 dispatch 在一个 SQLite 事务里完成。两条消息并发到达时, 只有一个能创建 Session, 另一个进入 pending_triggers。这替代了 Gateway 的 `set_subagent_awake` CAS。

#### `POST /api/queue/session-ended`

由 subagent_rest saga 的最后一步调用。

```python
def session_ended(agent_id, subagent_id, scope_id):
    session_key = f"{agent_id}:{subagent_id}"

    with db.transaction():
        # 1. 清理活跃 Session
        db.delete("active_sessions", session_key)

        # 2. 检查 pending_triggers
        pending = db.pop("pending_triggers", session_key)

        if pending:
            # 3. 有待处理触发器 -> 立即启动新 Session
            new_scope_id = str(uuid4())
            saga_id = orchestrator.create(
                saga_type="subagent_wake",
                context={
                    "agent_id": pending["agent_id"],
                    "subagent_id": pending["subagent_id"],
                    "user_id": pending["user_id"],
                    "scope_id": new_scope_id,
                    "trigger_type": pending["trigger_type"],
                    **json.loads(pending.get("metadata", "{}")),
                },
                idempotency_key=f"session-{session_key}-{new_scope_id}",
            )
            db.insert("active_sessions", {
                "session_key": session_key,
                "saga_id": saga_id,
                "scope_id": new_scope_id,
                "created_at": utc_now(),
            })
            return {"action": "restarted", "saga_id": saga_id}

    return {"action": "session_closed"}
```

### 3.3 Queue Service 重启恢复

```python
def rebuild_sessions_on_startup():
    # 从 sagas 表查所有 status=running 的 saga
    running_sagas = saga_repo.find_by_status("running")
    for saga in running_sagas:
        ctx = saga["context"]
        session_key = f"{ctx['agent_id']}:{ctx['subagent_id']}"
        db.upsert("active_sessions", {
            "session_key": session_key,
            "saga_id": saga["id"],
            "scope_id": ctx.get("scope_id", ""),
            "created_at": saga["created_at"],
        })
    # pending_triggers 已持久化, 无需恢复
```

---

## 4. Saga 变更

### 4.1 message_process saga -> 删除

整个 `message_process` saga (claim -> route -> decide -> trigger wake) 被 Queue Service 的 `dispatch` 接口完全替代。dispatch 在一个事务里做了 claim + route + decide 的全部工作。

### 4.2 subagent_wake 变更

```diff
  subagent_wake saga:
    1. session_init (Cortex)           -- 不变
-   2. set_subagent_awake (Gateway)    -- 删除, dispatch 时已经登记了 Session
+   2. set_subagent_awake (Entangled)  -- 仅写 Entangled 实体以更新前端显示
    3. trigger react_think             -- 不变
```

### 4.3 react_think 变更

```diff
  react_think saga:
-   1. prepare_context (Cortex + Gateway 读未读消息)
+   1. prepare_context (Cortex + Entangled 读未读消息)
    2. call_llm                        -- 不变
    3. save_response                   -- 不变
    4. decide_actions                  -- 不变
    5. trigger actions / retry / rest  -- 不变
```

### 4.4 react_actions 变更

```diff
  react_actions saga:
    1. execute_tools (parallel)        -- 不变
    2. save_results (parallel)         -- 不变
-   3. check_continue (Gateway: has_new_messages + need_rest)
+   3. check_continue (Entangled: 查未读消息 + need_rest)
    4. decide_continue                 -- 不变
    5. trigger think / rest            -- 不变
```

### 4.5 subagent_rest 变更

subagent_rest saga **保留**, 但目标全部迁移:

```diff
  subagent_rest saga:
    1. generate_summary                -- 不变, Cortex 领域
    2. cortex_scope_end                -- 不变, Cortex 领域
-   3. set_sleeping/completed (Gateway)
+   3. set_sleeping/completed (Entangled)  -- 直接写 Entangled 更新前端
-   4. notify_parent (Gateway inject -> 写 sending 消息 -> Watchdog 再轮询)
+   4. notify_parent -> Queue dispatch(trigger_type=subagent_completed)  -- 直调 dispatch
    5. destroy_mcp                     -- 不变
+   6. session_ended (新增) -> Queue /api/queue/session-ended
```

### 4.6 `subagent_rest` 工具的 `need_rest` 标志迁移

当 Agent 调用 `subagent_rest` 工具时, `_exec_subagent_rest` 现在调 Gateway 设 `need_rest=1`。
终态改为直接写 Entangled:

```diff
  tool_handlers.py -> _exec_subagent_rest:
-   gw.request("POST", f"/internal/subagents/{agent_id}/{subagent_id}/rest", body)
+   entangled_client.update_entity("subagents", subagent_id, {
+       "need_rest": 1,
+       "wake_at": wake_at,
+       "wake_triggers": wake_triggers,
+       "handoff_notes": handoff_notes,
+   }, params={"agent_id": agent_id})
```

---

## 5. Worker 读写路径迁移

### 5.1 消息读取: Gateway -> Entangled

`context_handlers.py` 里的 `handle_context_read` 现在:
```python
all_messages = gateway_client.get_unread_sent_messages(agent_id)
# ... filter by subagent_id ...
gateway_client.mark_messages_read([msg["id"]])
```

终态改为通过 Entangled HTTP API:
```python
all_messages = entangled_client.query_entities("chat_messages",
    filters={"agent_id": agent_id, "read": False, "status": "sent"})
# ... filter by subagent_id ...
entangled_client.batch_update("chat_messages", [msg["id"]], {"read": True})
```

### 5.2 SubAgent 状态写入: Gateway -> Entangled

`subagent_handlers.py` 里三个 handler 改为写 Entangled:
```python
# 以前
gateway_client.set_subagent_sleeping(agent_id, subagent_id)

# 以后
entangled_client.update_entity("subagents", subagent_id,
    {"status": "sleeping", "need_rest": 0},
    params={"agent_id": agent_id})
```

### 5.3 check_continue: Gateway -> Entangled

`runtime_handlers.py` 里的 `handle_session_check_new_messages`:
```python
# 以前
msg_resp = gateway_client.has_new_messages(agent_id)
resp = gateway_client.check_and_clear_need_rest(agent_id, subagent_id)

# 以后
messages = entangled_client.query_entities("chat_messages",
    filters={"agent_id": agent_id, "read": False})
has_new = len(messages) > 0

subagent = entangled_client.get_entity("subagents", subagent_id,
    params={"agent_id": agent_id})
need_rest = subagent.get("need_rest", False)
if need_rest:
    entangled_client.update_entity("subagents", subagent_id,
        {"need_rest": 0}, params={"agent_id": agent_id})
```

不需要 CAS: Session 排他性保证此刻只有一个 Worker 操作这个 subagent。

---

## 6. 触发路径迁移总表

| 触发场景 | 现在 | 终态 |
|---|---|---|
| 用户发消息 | 前端 -> Gateway DB 写 sending -> Watchdog 轮询 -> message_process saga -> subagent_wake | 前端 -> Gateway 鉴权 -> 写 Entangled -> Queue dispatch |
| 中断 | 前端 -> Gateway DB 写 INTERRUPT sending -> Watchdog -> cancel-all | 前端 -> Gateway 鉴权 -> Queue cancel-all |
| 定时唤醒 | Scheduler -> Gateway inject_wake -> sending -> Watchdog -> Queue | Scheduler -> Queue dispatch(trigger_type=system_wake) |
| 子任务完成 | Worker -> Gateway inject -> sending -> Watchdog -> Queue | Worker -> Queue dispatch(trigger_type=subagent_completed) |
| 派生子 Agent | Tool -> Gateway inject -> sending -> Watchdog -> Queue | Tool -> Queue dispatch(trigger_type=spawn_subagent) |

**每一条链路都从 5 步 (写 DB -> Watchdog 轮询 -> 再调 Queue) 缩减为 1-2 步 (直调 Queue dispatch)。**

---

## 7. 删除清单

### 7.1 可删除的组件

| 组件 | 说明 |
|---|---|
| **Watchdog** (`watchdog_sync.py`) | 完全消灭, 其 "故障恢复" 能力由 HealthWorker 的 recover_stale 替代 |
| **message_process saga** (`message_process.py`) | 被 Queue dispatch 替代 |
| **MessageRepository** (`gateway/db/repositories/message.py`) | 不再需要 |
| `main_novaic.py` 中的 `run_watchdog()` | 不再需要 |

### 7.2 Gateway 可删除的端点 (17 个)

```
POST   /messages/find-sending
POST   /messages/claim-and-prepare
POST   /messages/{message_id}/confirm
POST   /messages/{message_id}/claim
POST   /messages/inject-subagent-completed
POST   /messages/inject-wake
POST   /messages                            # Worker 不再写, 前端通过 Entangled 写
PATCH  /messages/mark-read
PATCH  /messages/mark-processed
GET    /messages/has-new/{agent_id}
GET    /messages/unread-sent/{agent_id}

POST   /subagents/{a}/{s}/awake
POST   /subagents/{a}/{s}/sleeping
POST   /subagents/{a}/{s}/completed
POST   /subagents/{a}/{s}/failed
POST   /subagents/{a}/{s}/rest
POST   /subagents/{a}/{s}/check-and-clear-rest
```

### 7.3 Gateway 保留的端点

```
# 前端查询 API (Gateway 鉴权后透传 Entangled)
GET    /agents/{agent_id}
GET    /agents/{agent_id}/chat/history
GET    /subagents/list
GET    /subagents/{a}/{s}/history

# 前端操作 API (Gateway 鉴权后透传到对应服务)
POST   /agents/{agent_id}/interrupt           -> Queue cancel-all
POST   /subagents/{a}/spawn                   -> Queue dispatch

# Cortex BusinessProxy 工具 API (现经 Business Service, 中期 Cortex 直连后端替代)
# 这 12 类端点由 Cortex 的 BusinessProxy 在工具执行时调用，目标是 Business Service (:19998)
POST   /agents/{agent_id}/memory/*             # -> 中期 Cortex 直连 Entangled
POST   /agents/{agent_id}/notebook/*           # -> 中期 Cortex 直连 Entangled
POST   /agents/{agent_id}/quadrant-tasks/*     # -> 中期 Cortex 直连 Entangled
POST   /agents/{agent_id}/chat/event           # -> v2 改为 Worker 写 Entangled
ANY    /agents/{agent_id}/vm/*                 # -> CloudBridge 在 Device Service (:19993) 上, Gateway 不参与
ANY    /agents/{agent_id}/qemu/*               # -> CloudBridge 在 Device Service (:19993) 上, Gateway 不参与
POST   /agents/{agent_id}/subagent/*           # -> v2 改为 Queue dispatch

# 配置 API
GET    /config/agent/{agent_id}
GET    /config/llm/agent/{agent_id}

# WebSocket
WS     /pc/ws                                  # -> 注意: CloudBridge WS 在 Device Service (:19993), 非 Gateway
```

> **注意**: `chat/event` (AGENT_REPLY) 是 Agent 回复消息的唯一写入路径。
> 终态应改为 Worker 执行 `chat_reply` 工具时直接写 Entangled,
> 但需要先迁移 HEARTBEAT_OK 过滤和附件处理逻辑到 tool_handlers 侧。

---

## 8. 故障恢复

| 故障场景 | 恢复机制 |
|---|---|
| Queue Service 重启 | `rebuild_sessions_on_startup()` 从 running sagas 重建 active_sessions |
| 用户消息写入 Entangled 成功但 dispatch 失败 | HealthWorker 每 30s 扫描: 有未读消息 + 无活跃 Session -> 补发 dispatch |
| Saga 执行超时未结束 | HealthWorker 的 `recover_stale_sagas()` 已有此能力 |
| 子 Agent 完成但 notify_parent dispatch 失败 | 同上, HealthWorker 兜底 |

HealthWorker 的恢复扫描 (30s 间隔) 本质上就是 Watchdog 的极度退化版, 只在异常时生效。

---

## 9. 实施步骤

不是渐进式改造。按模块一次性切换:

**Step 1**: Queue Service 加 dispatch + session-ended + 两张表 + 重启恢复
(此时不改任何其他东西, 先确保 Queue Service 接口可用)

**Step 2**: Worker 切数据源:
- subagent_handlers 写 Entangled 替代 Gateway
- context_handlers 从 Entangled 读消息替代 Gateway
- runtime_handlers (check_continue) 从 Entangled 查替代 Gateway
- tool_handlers 的 subagent_rest 写 Entangled 替代 Gateway

**Step 3**: 触发路径切换:
- Watchdog 停用, Scheduler 直接 dispatch
- subagent_rest 的 notify_parent 改为 dispatch
- Gateway 前端入口改为: 写 Entangled + dispatch

**Step 4**: 清理:
- 删 Watchdog、删 message_process saga、删 Gateway 旧端点
- 删 gateway.db 中的 chat_messages 表
- HealthWorker 加故障恢复扫描
