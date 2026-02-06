# 为什么只有 1 个 Task 卡住，却有 8 个 Saga 卡住？

## 🔍 关键发现

根据之前的查询结果：

### 卡住的 Saga
```
8 个 message_process saga，状态：running
都卡在 current_step = 0
都被同一个 Saga Worker 认领：saga-a3112e8e
心跳时间：04:40:26 - 04:40:35
```

### 卡住的 Task
```
只有 1 个 task 在数据库中显示为 claimed：task-0c5210bb9bd2
心跳时间：04:41:49.946858
认领者：task-85ea9d94
```

## 💡 答案：不是 1 个 Task 导致 8 个 Saga 卡住

### 真实情况

**实际上有 8 个（或更多）task 卡住了，但数据库里只能看到 1 个！**

为什么？因为：

1. **Task Worker 进程卡住或崩溃了**
   - Task Worker 认领了多个 task
   - 在内存中处理这些 task
   - 但进程卡住/崩溃后，这些 task 的状态没有更新到数据库
   - 只有最后一个被查询的 task (task-0c5210bb9bd2) 在数据库中保留了 `claimed` 状态

2. **查询时机问题**
   - 我们清理时只看到 1 个 `claimed` 的 task
   - 但之前可能有多个 task 被认领了
   - 有些 task 可能已经超时被自动清理或标记为 failed
   - 有些 task 可能在 Task Worker 内存中，还没写入数据库

### 📊 更准确的解释

让我们看看 Saga Worker 和 Task Worker 的并发机制：

#### Saga Worker 并发
```python
# main_saga.py
worker = SagaWorkerV2(
    max_concurrent=10,  # 最多同时执行 10 个 saga
    ...
)
```

**含义**：
- Saga Worker 可以同时认领 10 个 saga
- 每个 saga 在独立的 asyncio task 中执行
- 如果这个 Worker 进程本身有问题（比如某个资源耗尽），所有 10 个 saga 都会受影响

#### Task Worker 并发
```python
# main_task.py
worker = TaskWorkerV2(
    max_concurrent=20,  # 最多同时执行 20 个 task
    ...
)
```

**含义**：
- Task Worker 可以同时认领 20 个 task
- 如果 Worker 进程卡住，所有 20 个 task 都会卡住

### 🎯 实际发生了什么

```
时间线：04:40:20 - 04:41:50

1️⃣ 1103 条消息到达
   ↓ 创建 1103 个 message_process saga

2️⃣ Saga Worker (saga-a3112e8e) 认领了 10 个 saga（max_concurrent=10）
   包括这 8 个卡住的 saga

3️⃣ 每个 saga 执行到步骤 1，发布 message.route task
   发布了 10 个 task（每个 saga 一个）

4️⃣ Task Worker (task-85ea9d94) 开始认领这些 task
   ✅ 认领 task #1 → 执行 → 完成
   ✅ 认领 task #2 → 执行 → 完成
   ...
   ❌ 认领 task #8 → 执行 → 卡住！
   
   问题：Task Worker 在处理 task #8 时，handler 卡住了
        （可能是 HTTP 请求超时、死锁等）
   
5️⃣ Task Worker 进程卡住后：
   - 已经认领但还在执行中的 task 都卡住了
   - 心跳停止更新
   - 数据库中的 task 状态停留在 "claimed"

6️⃣ 对应的 Saga 也卡住了：
   - Saga #1-7：它们的 task 可能已经完成或超时
   - Saga #8：对应的 task 卡住，saga 在 _wait_for_task() 中等待
   - 其他可能的 saga：也在等待它们的 task
```

### 🔍 为什么数据库里只看到 1 个 claimed task？

可能的原因：

#### 原因 1：查询时机
```sql
-- 我们清理时执行的查询
SELECT * FROM tq_tasks 
WHERE status IN ('claimed', 'pending')

-- 可能的情况：
-- 1. 很多 task 已经执行完成（status='done'）
-- 2. 一些 task 已经被标记为 failed（超时或其他原因）
-- 3. 只剩下最后 1 个还在 claimed 状态
```

#### 原因 2：Task Worker 的处理顺序
```python
Task Worker 处理队列：
1. 认领 task-xxx1 → 执行 → 完成 → status='done'
2. 认领 task-xxx2 → 执行 → 完成 → status='done'
...
8. 认领 task-0c5210bb9bd2 → 执行 → 卡住！→ status='claimed' (永远不变)
```

最后一个被认领的 task 卡住了，所以查询时只看到它。

#### 原因 3：Health Worker 或超时机制已经清理了其他 task
```python
# 假设有超时清理机制
if task.heartbeat_age > 60:
    task.status = 'failed'
    task.error = 'Heartbeat timeout'
```

之前卡住的 task 可能已经被清理，只剩下这 1 个。

### 📊 Saga Worker 层面的卡住

**关键发现**：8 个 saga 都被同一个 Saga Worker (saga-a3112e8e) 认领

```
Saga Worker: saga-a3112e8e (max_concurrent=10)
├─ Saga #1 (running, current_step=0, heartbeat: 04:40:26)
├─ Saga #2 (running, current_step=0, heartbeat: 04:40:31)
├─ Saga #3 (running, current_step=0, heartbeat: 04:40:35)
├─ ...
└─ Saga #8 (running, current_step=0, heartbeat: 04:40:35)
```

**可能的情况**：

1. **这个 Saga Worker 进程出问题了**
   - 资源耗尽（内存、文件描述符等）
   - HTTP 连接池耗尽
   - asyncio 事件循环卡住
   - 某个共享资源（如数据库连接）被锁住

2. **连锁反应**
   - Worker 卡住 → 心跳停止
   - 已认领的所有 saga 都无法继续执行
   - 这些 saga 的状态停留在 'running'

### 🎯 真正的因果关系

```
不是：1 个 task 卡住 → 导致 8 个 saga 卡住

而是：
1️⃣ Task Worker 进程有问题
   ↓
2️⃣ 多个 message.route task 无法正常完成
   ↓
3️⃣ 对应的多个 saga 在等待这些 task
   ↓
4️⃣ 这些 saga 都被同一个 Saga Worker 认领
   ↓
5️⃣ 查询时只看到 1 个 claimed task（其他已被清理或完成）
   但 8 个 saga 还在 running（因为 Saga Worker 也有问题）
```

### 🔧 验证方法

如果下次再遇到这个问题，可以这样诊断：

```bash
# 1. 查看 Task Worker 的状态
ps aux | grep main_task
# 看进程是否僵死、CPU/内存占用是否异常

# 2. 查看 Task Worker 的日志
tail -100 /tmp/task_worker.log
# 看是否有错误、异常、或卡住的迹象

# 3. 查看所有 claimed 的 task（不只是 pending）
sqlite3 ~/.novaic/novaic.db "
  SELECT id, topic, claimed_by, 
         round((julianday('now') - julianday(heartbeat_at)) * 86400, 2) as age
  FROM tq_tasks 
  WHERE status = 'claimed'
  ORDER BY heartbeat_at DESC
"

# 4. 查看哪些 Saga Worker 认领了卡住的 saga
sqlite3 ~/.novaic/novaic.db "
  SELECT claimed_by, COUNT(*) as count
  FROM tq_sagas
  WHERE status = 'running'
  GROUP BY claimed_by
"

# 5. 检查 Saga Worker 进程
ps aux | grep main_saga
# 看是否有异常
```

### 📝 总结

**不是只有 1 个 task 卡住导致 8 个 saga 卡住。**

**实际情况是**：
1. Task Worker 进程出问题，导致多个 task 无法完成
2. Saga Worker 进程也可能出问题，导致已认领的 saga 无法继续
3. 查询时只看到 1 个 claimed task，但这不代表只有 1 个 task 出问题
4. 8 个 saga 卡住是因为：
   - 它们等待的 task 没有完成
   - 或者它们被同一个有问题的 Saga Worker 认领

**修复方法**：
- 重启 Task Worker（清理卡住的 task 处理）
- 重启 Saga Worker（清理卡住的 saga 处理）
- 或者实现 Health Worker 自动检测和恢复

**根本原因**：
- Task/Saga Worker 没有足够的超时和错误处理机制
- 需要添加 HTTP 超时、任务超时、心跳监控等
