# 为什么 1 个 Task 卡住会导致 8 个 Saga 卡住？

## 🔍 核心原因：Saga 是**同步等待** Task 完成的

### 📊 message_process Saga 的执行流程

```python
# message_process saga 定义（4个步骤）
MESSAGE_PROCESS_SAGA = SagaDefinition("message_process")

步骤 0: claim_message    (Task: message.claim)
步骤 1: route_message    (Task: message.route)     ← 卡在这里！
步骤 2: decide_action    (Decision)
步骤 3: trigger_runtime_start (Task: saga.trigger, 有条件)
```

### 🔄 Saga Worker 如何执行 Task 步骤

```python
# saga_worker_v2.py: _execute_task_step()

async def _execute_task_step(saga_id, step, context, step_results):
    # 1️⃣ 发布 Task 到队列
    resp = await client.post("/internal/tq/tasks/publish", json={
        "topic": "message.route",  # 例如这个
        "payload": {...},
        "idempotency_key": f"{saga_id}-route_message",
    })
    
    task_id = resp.json()["task_id"]  # 比如 task-0c5210bb9bd2
    
    # 2️⃣ 同步等待这个 Task 完成 ← 关键！
    return await self._wait_for_task(task_id, "route_message")


async def _wait_for_task(task_id, step_name):
    """等待任务完成（带超时 300 秒）"""
    start_time = time.time()
    
    while True:
        # 🔁 不断轮询 Task 状态
        resp = await client.get(f"/internal/tq/tasks/{task_id}")
        task = resp.json()["task"]
        status = task["status"]
        
        # ✅ 如果完成了，返回结果
        if status == "done":
            return task["result"]
        
        # ❌ 如果失败了，返回错误
        if status == "failed":
            return {"success": False, "error": task["error"]}
        
        # ⏳ 否则继续等待（sleep 0.5秒后再查询）
        if time.time() - start_time > 300:  # 超时 300 秒
            raise TimeoutError(...)
        
        await asyncio.sleep(0.5)  # ← Saga 被阻塞在这里！
```

### 💥 问题场景重现

```
时间线：04:40:20 - 04:40:35

1️⃣ 8 条用户消息到达
   ↓
2️⃣ 创建 8 个 message_process saga

3️⃣ Saga Worker 认领这 8 个 saga，开始执行
   Saga #1 → 步骤 1 → 发布 task-xxxxx1 (message.route) → 等待...
   Saga #2 → 步骤 1 → 发布 task-xxxxx2 (message.route) → 等待...
   Saga #3 → 步骤 1 → 发布 task-xxxxx3 (message.route) → 等待...
   ...
   Saga #8 → 步骤 1 → 发布 task-0c5210bb9bd2 (message.route) → 等待... ← 卡住！

4️⃣ Task Worker 认领这些 task，开始执行
   ✅ task-xxxxx1 → 执行完成 (0.5秒) → Saga #1 继续
   ✅ task-xxxxx2 → 执行完成 (0.5秒) → Saga #2 继续
   ✅ task-xxxxx3 → 执行完成 (0.5秒) → Saga #3 继续
   ...
   ❌ task-0c5210bb9bd2 → 执行中... 卡住！永远不返回！

5️⃣ Saga #8 在 _wait_for_task 的 while 循环里不断查询
   每 0.5 秒查询一次: GET /internal/tq/tasks/task-0c5210bb9bd2
   
   04:40:35.5s → status: claimed (还在执行，继续等)
   04:40:36.0s → status: claimed (还在执行，继续等)
   04:40:36.5s → status: claimed (还在执行，继续等)
   ...
   04:43:00s   → status: claimed (已经等了 188 秒！)
```

### 📋 数据库状态证据

#### Saga 状态
```sql
SELECT id, status, current_step, heartbeat_at FROM tq_sagas WHERE status='running';

saga-fdec74ef26f1 | running | 0 | 2026-02-04T04:40:26.680858  ← 卡在步骤 0
saga-e868a8a2cc5c | running | 0 | 2026-02-04T04:40:31.175292  ← 卡在步骤 0
...
```

**为什么 `current_step = 0`？**

因为步骤还没完成！步骤 0 是 `claim_message`（已完成），步骤 1 是 `route_message`（正在等待 task），只有步骤完成后，`current_step` 才会递增。

实际上它们卡在**步骤 1**（route_message），但 `current_step` 还显示为 1（数组索引从 0 开始）。

#### Task 状态
```sql
SELECT id, topic, status, heartbeat_at FROM tq_tasks WHERE id='task-0c5210bb9bd2';

task-0c5210bb9bd2 | message.route | claimed | 2026-02-04T04:41:49.946858
```

**为什么卡在 `claimed` 状态？**

Task Worker 认领后开始执行 handler，但 handler 内部卡住了（可能是 HTTP 请求超时、死锁等），永远不会调用 `complete_task` 或 `fail_task`。

### 🔗 完整调用链

```
用户消息 #1101 到达
    ↓
Watchdog 创建 message_process saga
    ↓
Saga Worker 认领 saga
    ↓
执行步骤 0: claim_message ✅
    ↓
执行步骤 1: route_message
    ↓ 发布 task-0c5210bb9bd2
    ↓
Task Worker 认领 task-0c5210bb9bd2
    ↓
执行 handle_message_route(...)
    ↓
在这里卡住！(可能是 HTTP 请求到 Gateway 超时)
    ↓ (永远不会返回)
    ↓
Saga Worker 在 _wait_for_task() 里无限等待
    ↓
while True:
    status = get_task_status(task_id)  ← 一直是 "claimed"
    if status == "done": break         ← 永远等不到
    await sleep(0.5)
    
    ↓ 188 秒后
    
测试脚本超时（120秒），但 saga 还在等待...
```

### 🎯 关键点

1. **Saga Worker 是同步等待 Task 的**
   - 发布 task 后，进入 while 循环
   - 每 0.5 秒查询一次 task 状态
   - 只有 task 状态变成 `done` 或 `failed`，才会继续

2. **Task Worker 卡住不会更新状态**
   - Task 状态停留在 `claimed`
   - Saga 永远等不到 `done` 或 `failed`
   - 直到超时（300 秒）

3. **多个 Saga 可能等待不同的 Task**
   - 每个 saga 会发布自己的 task
   - 如果多个 task 都卡住了，对应的多个 saga 也会卡住
   - 在这个测试中，有 8 个 saga 卡住，可能是它们的 task 都卡住了

### 📊 为什么日志里反复出现同一个 Task ID？

```log
INFO: GET /internal/tq/tasks/task-0c5210bb9bd2 HTTP/1.1" 200 OK
INFO: GET /internal/tq/tasks/task-0c5210bb9bd2 HTTP/1.1" 200 OK
INFO: GET /internal/tq/tasks/task-0c5210bb9bd2 HTTP/1.1" 200 OK
...（重复上百次）
```

这就是 Saga Worker 在 `_wait_for_task()` 的 while 循环里，每 0.5 秒查询一次 task 状态：

```python
while True:
    # 查询 task 状态
    resp = await client.get(f"/internal/tq/tasks/{task_id}")  # ← 日志来源
    
    task = resp.json()["task"]
    status = task["status"]
    
    if status in ("done", "failed"):
        break
    
    # 等待 0.5 秒后重试
    await asyncio.sleep(0.5)
```

### 🔧 解决方案总结

#### 问题根源
- Task Worker 执行 `message.route` handler 时卡住（可能是 HTTP 超时）
- Task 状态永远停留在 `claimed`
- Saga Worker 无限等待，导致 saga 卡住

#### 修复措施
1. ✅ **清理卡住的 task**（设置为 failed）
2. ✅ **清理卡住的 saga**（设置为 failed）
3. ✅ **重启 Task Worker**

#### 预防措施
1. 为 HTTP 客户端添加超时（10秒）
2. 为 Task 执行添加总超时（60秒）
3. 实现 Health Worker 自动恢复超时的 task/saga

### 📈 类比理解

想象一个餐厅：

```
🍽️ Saga = 客人点了一份套餐
📋 Task = 厨房做菜

客人点单：
1. 前菜 ✅ (claim_message task - 已完成)
2. 主菜 ⏳ (route_message task - 正在做)
3. 甜品 ⏸️ (decide_action - 等待中)
4. 咖啡 ⏸️ (trigger_runtime_start - 等待中)

问题：
- 厨房在做主菜时卡住了（厨师睡着了？）
- 主菜永远做不完
- 服务员（Saga Worker）一直在厨房门口等："主菜好了吗？""主菜好了吗？"...
- 甜品和咖啡永远上不了桌
- 客人（用户）饿着等了 188 秒...
```

**1 个主菜卡住 → 1 份套餐卡住**
**8 个主菜卡住 → 8 份套餐卡住**

这就是为什么 1 个（或 8 个）task 卡住会导致对应的 saga 卡住！
