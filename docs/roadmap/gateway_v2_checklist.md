# Gateway v2 Implementation Checklist

> 对照 [gateway-v2-target-architecture.md](file:///Users/wangchaoqun/new-build-novaic/docs/architecture/gateway-v2-target-architecture.md)
> 按 Step 1 → 4 依次执行

---

## Step 1: Queue Service 加 Session Coordinator ✅

### 1.1 数据库
- [x] `tq_active_sessions` 表 DDL (schema v6)
- [x] `tq_pending_triggers` 表 DDL (UNIQUE on session_key)
- [x] [session_repo.py](file:///Users/wangchaoqun/new-build-novaic/novaic-agent-runtime/queue_service/session_repo.py): SessionRepository with dispatch/session_ended/rebuild

### 1.2 API 路由
- [x] `POST /api/queue/dispatch` — 路由 trigger 到新 session 或缓冲
- [x] `POST /api/queue/session-ended` — 清理 session，可选从 pending 重启
- [x] `GET /api/queue/sessions` — 诊断：列出活跃 sessions
- [x] `GET /api/queue/pending` — 诊断：列出待处理 triggers

### 1.3 重启恢复
- [x] [main.py](file:///Users/wangchaoqun/new-build-novaic/novaic-agent-runtime/queue_service/main.py) startup 调用 `session_repo.rebuild()`

### 1.4 客户端 SDK
- [x] `SagaClient.dispatch()` 和 `SagaClient.session_ended()`

---

## Step 2: Worker 切数据源（Gateway → EntityStore） ✅

### 2.1 EntityStore 客户端
- [x] `GatewayBusinessClient.entity_get/update/list/create` 方法
- [x] Gateway 新增 `/internal/entities/*` 内部 CRUD 端点

### 2.2 subagent_handlers.py
- [x] [set_awake](file:///Users/wangchaoqun/new-build-novaic/novaic-agent-runtime/task_queue/sagas/subagent_wake.py#28-34): [entity_update("subagents", ...)](file:///Users/wangchaoqun/new-build-novaic/novaic-agent-runtime/task_queue/client.py#584-588)
- [x] [set_sleeping](file:///Users/wangchaoqun/new-build-novaic/novaic-agent-runtime/task_queue/sagas/subagent_rest.py#64-66): [entity_update("subagents", ...)](file:///Users/wangchaoqun/new-build-novaic/novaic-agent-runtime/task_queue/client.py#584-588)
- [x] [set_completed](file:///Users/wangchaoqun/new-build-novaic/novaic-agent-runtime/task_queue/sagas/subagent_rest.py#68-70): [entity_update("subagents", ...)](file:///Users/wangchaoqun/new-build-novaic/novaic-agent-runtime/task_queue/client.py#584-588)

### 2.3 context_handlers.py
- [x] `context.read`: [entity_list("chat_messages", ...)](file:///Users/wangchaoqun/new-build-novaic/novaic-agent-runtime/task_queue/client.py#589-593) + [entity_update](file:///Users/wangchaoqun/new-build-novaic/novaic-agent-runtime/task_queue/client.py#584-588) mark read

### 2.4 runtime_handlers.py
- [x] [check_new_messages](file:///Users/wangchaoqun/new-build-novaic/novaic-agent-runtime/task_queue/handlers/runtime_handlers.py#147-205): [entity_list](file:///Users/wangchaoqun/new-build-novaic/novaic-agent-runtime/task_queue/client.py#589-593) + `entity_get/update` for need_rest

### 2.5 tool_handlers.py
- [x] [subagent_rest](file:///Users/wangchaoqun/new-build-novaic/novaic-gateway/gateway/api/internal/subagent.py#368-403): [entity_update("subagents", {need_rest: 1, ...})](file:///Users/wangchaoqun/new-build-novaic/novaic-agent-runtime/task_queue/client.py#584-588)
- [x] [chat_reply](file:///Users/wangchaoqun/new-build-novaic/novaic-agent-runtime/task_queue/handlers/tool_handlers.py#52-72): [entity_create("chat_messages", ...)](file:///Users/wangchaoqun/new-build-novaic/novaic-agent-runtime/task_queue/client.py#594-598)

### 2.6 message_handlers.py
- [x] [notify_parent](file:///Users/wangchaoqun/new-build-novaic/novaic-agent-runtime/task_queue/sagas/subagent_rest.py#72-84): `saga_client.dispatch(trigger_type="subagent_completed")`
- [x] Deleted `message.claim` and `message.route` handlers

---

## Step 3: 触发路径切换 ✅

### 3.1 subagent_rest saga 新增 session_ended 步骤
- [x] `SESSION_ENDED` topic 注册
- [x] [session_handlers.py](file:///Users/wangchaoqun/new-build-novaic/novaic-agent-runtime/task_queue/handlers/session_handlers.py): [handle_session_ended](file:///Users/wangchaoqun/new-build-novaic/novaic-agent-runtime/task_queue/handlers/session_handlers.py#14-55) handler
- [x] [subagent_rest.py](file:///Users/wangchaoqun/new-build-novaic/novaic-agent-runtime/task_queue/sagas/subagent_rest.py): 新增 [session_ended](file:///Users/wangchaoqun/new-build-novaic/novaic-agent-runtime/queue_service/session_repo.py#138-236) 最终步骤

### 3.2 Watchdog v2
- [x] 重写为 scheduled wake + interrupt only
- [x] 非 interrupt 消息通过 `saga_client.dispatch()` 路由（过渡措施）
- [x] 删除 CortexBridge 依赖

### 3.3 SchedulerWorker
- [x] [inject_wake_message](file:///Users/wangchaoqun/new-build-novaic/novaic-gateway/gateway/api/internal/message.py#467-524) → `saga_client.dispatch(trigger_type="scheduled_wake")`

---

## Step 4: 清理 ✅

### 4.1 删除废弃代码
- [x] 删除 [message_process.py](file:///Users/wangchaoqun/new-build-novaic/novaic-agent-runtime/task_queue/sagas/message_process.py) saga
- [x] 删除 `SubAgentBusiness` class
- [x] 删除 `MESSAGE_CLAIM`、`MESSAGE_ROUTE`、`MESSAGE_PROCESS` topics

### 4.2 GatewayBusinessClient 清理
- [x] 删除: [claim_message](file:///Users/wangchaoqun/new-build-novaic/novaic-gateway/gateway/api/internal/message.py#304-330), [has_new_messages](file:///Users/wangchaoqun/new-build-novaic/novaic-gateway/gateway/api/internal/message.py#332-342), [check_and_clear_need_rest](file:///Users/wangchaoqun/new-build-novaic/novaic-gateway/gateway/api/internal/subagent.py#405-417)
- [x] 删除: `set_subagent_awake/sleeping/completed`
- [x] 删除: [get_unread_sent_messages](file:///Users/wangchaoqun/new-build-novaic/novaic-gateway/gateway/api/internal/message.py#134-163), [mark_messages_read](file:///Users/wangchaoqun/new-build-novaic/novaic-gateway/gateway/api/internal/message.py#344-369)
- [x] 删除: [inject_wake_message](file:///Users/wangchaoqun/new-build-novaic/novaic-gateway/gateway/api/internal/message.py#467-524), [inject_subagent_completed_message](file:///Users/wangchaoqun/new-build-novaic/novaic-gateway/gateway/api/internal/message.py#397-465)
- [x] 删除: [increment_drive_interaction](file:///Users/wangchaoqun/new-build-novaic/novaic-gateway/gateway/api/internal/subagent.py#711-729)
- [x] 保留（过渡）: [find_sending_message](file:///Users/wangchaoqun/new-build-novaic/novaic-agent-runtime/task_queue/client.py#601-604), [confirm_message](file:///Users/wangchaoqun/new-build-novaic/novaic-agent-runtime/task_queue/client.py#605-607), [get_due_for_wake](file:///Users/wangchaoqun/new-build-novaic/novaic-agent-runtime/task_queue/client.py#608-612)

### 4.3 Gateway 新增
- [x] `/internal/entities/*` 内部 CRUD 端点（entity.py）

---

## 待办 → 已全部完成 ✅

### 前端集成 ✅
- [x] 用户发消息接口 → Entangled action `messages.send` → `message_actions.send_action()` → Queue Service dispatch
- [x] Interrupt 接口 → `POST /internal/agents/{id}/interrupt` → Queue `POST /api/queue/recover/cancel-all`

### Gateway 端点清理 ✅
- [x] 删除 `/internal/messages/find-sending` (已在 Step 4 commit 中移除)
- [x] 删除 `/internal/messages/{id}/confirm` (已在 Step 4 commit 中移除)
- [x] 删除 `/internal/subagents/{a}/{s}/awake`
- [x] 删除 `/internal/subagents/{a}/{s}/sleeping`
- [x] 删除 `/internal/subagents/{a}/{s}/completed`
- [x] 删除 `/internal/subagents/{a}/{s}/rest`
- [x] 删除 `/internal/subagents/{a}/{s}/check-and-clear-rest`
- [x] 删除 `/internal/subagents/{a}/{s}/failed`
- [x] 删除 `/internal/subagents/{a}/{s}/summarizing`

### HealthWorker 兜底 ✅
- [x] `_scan_unhandled_messages`: 扫描 Entangled 未读消息 + 查询 Queue 活跃 sessions → 仅为无活跃 session 的 agent 补发 dispatch
- [x] 修复: `GatewayInternalClient` → `GatewayBusinessClient` (旧类已删除)

### 文档 ✅
- [x] 本 checklist 已完结
