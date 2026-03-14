# SubAgent 唤醒消息方案分析：SPAWN_SUBAGENT 应写入 Gateway DB

## 1. 问题现象

- ✅ subagent_spawn 返回成功，分配了 subagent_id
- ❌ runtime_list 只显示主 agent，没有子 agent 运行时
- ❌ subagent_query 返回 success: false
- ❌ runtime_send 返回 "Runtime not found"

**结论**：子 agent 创建成功，但未能启动 runtime（未被唤醒）。

---

## 2. 根因分析

### 2.1 唤醒流程

```
SPAWN_SUBAGENT 消息 (status=sending)
    ↓
Watchdog 轮询 find-sending
    ↓
创建 message_process Saga
    ↓
route_message → get_or_create_runtime
    ↓
启动 subagent runtime
```

### 2.2 当前数据流（问题所在）

| 步骤 | 组件 | 操作 | 写入 DB |
|------|------|------|---------|
| 1 | Tools Server | POST /internal/agents/{id}/subagent/spawn → Gateway | - |
| 2 | Gateway | 转发到 RO | - |
| 3 | **RO** | 创建 subagent + 写 SPAWN_SUBAGENT | **runtime_orchestrator.db** |
| 4 | Watchdog | find-sending → Gateway | - |
| 5 | **Gateway** | 本地处理，读 chat_messages | **gateway.db** |

**矛盾**：SPAWN_SUBAGENT 写在 RO 的 DB，Watchdog 从 Gateway 的 DB 读 → **消息永远找不到** → 无 Saga → 无 runtime 启动。

### 2.3 设计原则

- **chat_messages** 中需 Watchdog 处理的唤醒类消息（USER_MESSAGE, SYSTEM_WAKE, SPAWN_SUBAGENT, SUBAGENT_COMPLETED）应统一在 **Gateway DB**
- Watchdog 通过 `gateway_client.find_sending_message()` 调用 Gateway 的 `/internal/messages/find-sending`
- Gateway 的 find-sending **不转发**到 RO，本地读 gateway.db
- 因此：**唤醒消息必须写在 gateway.db**

---

## 3. 方案对比

### 方案 A：subagent_spawn 不转发，Gateway 处理全流程

**流程**：
1. subagent_spawn 在 Gateway 处理（移除转发）
2. Gateway 调用 RO 的「仅创建 subagent」API
3. Gateway 写 SPAWN_SUBAGENT 到 gateway.db

**需要**：
- RO 新增内部 API：`POST /internal/subagents/{agent_id}/create-only`（只创建 subagent，不写 message）
- Gateway 的 agent_subagent_spawn：先调 RO create-only，再写 message

**优点**：职责清晰，message 天然在 Gateway  
**缺点**：需新增 RO API，Gateway 需能调 RO

---

### 方案 B：RO 创建 subagent 后，调用 Gateway 写 message（推荐）

**流程**：
1. subagent_spawn 仍在 RO 处理（保持转发）
2. RO 创建 subagent 后，**不**在本地写 message
3. RO 调用 Gateway 的 `POST /internal/messages` 写入 SPAWN_SUBAGENT

**需要**：
- RO 的 agent_subagent_spawn 中，用 `MessageRepository.add_message` 改为调用 Gateway API
- RO 需 Gateway client（已有 GATEWAY_URL，可建 httpx  client）
- Gateway 的 `POST /internal/messages` 已支持 type=SPAWN_SUBAGENT

**优点**：
- 不改转发逻辑
- subagent 仍在 RO，message 在 Gateway
- Gateway 已有 create_message API，RO 只需反向调用

**缺点**：RO 需依赖 Gateway 可用（与现有架构一致）

---

### 方案 C：find-sending 转发到 RO

**流程**：让 Watchdog 从 RO 读 message

**问题**：USER_MESSAGE、SYSTEM_WAKE 等由 Gateway 写入 gateway.db，若 find-sending 转发到 RO，RO 读不到这些消息。**不可行**。

---

## 4. 推荐方案：方案 B

### 4.1 修改点

**RO `agent_subagent_spawn`**：
1. 保留：创建 subagent、计算 initial_context
2. 删除：`message_repo.add_message(..., type="SPAWN_SUBAGENT")` 本地写入
3. 新增：调用 Gateway `POST /internal/messages` 写入 SPAWN_SUBAGENT

**RO 调用 Gateway 示例**：
```python
# 在 RO 的 agent_subagent_spawn 中
gateway_url = ServiceConfig.GATEWAY_URL
async with httpx.AsyncClient() as client:
    resp = await client.post(
        f"{gateway_url}/internal/messages",
        json={
            "agent_id": agent_id,
            "type": "SPAWN_SUBAGENT",
            "content": task_description,
            "metadata": {
                "subagent_id": subagent.subagent_id,
                "trigger_id": trigger_id,
                "initial_context": initial_context,
                "parent_subagent_id": parent_subagent_id,
            },
        },
    )
```

注意：Gateway 的 create_message 会根据 type 自动设 `status="sending"`。

### 4.2 其他唤醒消息

- **USER_MESSAGE**：用户发消息 → 已走 Gateway API → 在 gateway.db ✓
- **SYSTEM_WAKE**：Scheduler 调 `inject_wake_message` → Gateway API → 在 gateway.db ✓
- **SUBAGENT_COMPLETED**：inject-subagent-completed → Gateway 处理 → 在 gateway.db ✓
- **SPAWN_SUBAGENT**：当前在 RO 写 → 需改为 RO 调 Gateway 写

### 4.3 依赖检查

- Gateway `POST /internal/messages`：支持 type=SPAWN_SUBAGENT，设 status=sending ✓
- RO 的 GATEWAY_URL：config 中有 ✓
- RO 调用 Gateway：message.py 中已有 `GatewayInternalClient(ServiceConfig.GATEWAY_URL)` 先例 ✓

---

## 5. 小结

| 项目 | 内容 |
|------|------|
| 根因 | SPAWN_SUBAGENT 写在 RO DB，Watchdog 从 Gateway DB 读 |
| 原则 | 唤醒消息统一在 Gateway DB |
| 推荐方案 | 方案 B：RO 创建 subagent 后，调用 Gateway API 写 message |
| 修改范围 | RO agent_subagent_spawn 一处 |
