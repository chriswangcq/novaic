# 任务卡住问题分析报告

## 🔍 问题现象

测试运行120秒后超时，系统状态：
- ✅ 消息处理完成：1112/1112
- ✅ Runtime 正常完成并休眠
- ❌ **8个 message_process saga 卡在 running 状态**
- ❌ **1个 message.route task 卡在 claimed 状态**

## 📊 详细分析

### 1. 卡住的 Task

**Task ID**: `task-0c5210bb9bd2`
**Topic**: `message.route`
**Status**: `claimed`

```
创建时间: 2026-02-04T04:41:49.371264
开始时间: 2026-02-04T04:41:49.946858
结束时间: NULL
认领者: task-85ea9d94
心跳时间: 2026-02-04T04:41:49.946858
心跳超时: 188.47秒 ⚠️
```

**关键发现**:
- Task 被 claim 后，`started_at` 有值，但 `finished_at` 为空
- 心跳超过 **188 秒**没有更新
- **Task Worker 在执行 message.route handler 时卡住或崩溃了**

### 2. 卡住的 Saga

**8个 message_process saga** 都卡在 `current_step = 0`（第一步）

示例：
```
Saga ID: saga-fdec74ef26f1
状态: running
当前步骤: 0
心跳时间: 2026-02-04T04:40:26.680858
认领者: saga-a3112e8e
```

**关键发现**:
- 所有卡住的 saga 都由同一个 Saga Worker (`saga-a3112e8e`) 认领
- 都卡在第一步（message.route task）
- 心跳时间停留在 04:40:26-35

### 3. Gateway 日志

反复出现对同一个 task 的查询：
```
INFO: GET /internal/tq/tasks/task-0c5210bb9bd2 HTTP/1.1" 200 OK
INFO: GET /internal/tq/tasks/task-0c5210bb9bd2 HTTP/1.1" 200 OK
INFO: GET /internal/tq/tasks/task-0c5210bb9bd2 HTTP/1.1" 200 OK
...（重复上百次）
```

**说明**: Saga Worker 在轮询等待这个 task 完成，但 task 永远不会完成。

### 4. 对应的消息

```
Message ID: d5a4c604-9b9
内容: [SingleRT] 消息#1101 (t=59.83s)
状态: sent
已读: 1
```

**矛盾点**: 消息已经是 `sent` 状态且 `read=1`，说明被 Agent Loop 处理了，但 message.route task 还在运行中。

## 🎯 根本原因

### message.route Handler 可能卡住的位置

查看代码 `task_queue/handlers/message_handlers.py:150-237`：

```python
def handle_message_route(payload: Dict[str, Any], ctx: dict) -> Dict[str, Any]:
    biz = SubAgentBusiness(ctx["gateway_url"], client=ctx.get("gateway_client"))
    client = ctx.get("gateway_client") or GatewayInternalClient(ctx["gateway_url"])
    
    # 可能卡住的地方：
    status = biz.get_status(agent_id, subagent_id)           # HTTP 调用
    active_runtime = client.get_subagent_runtime(...)        # HTTP 调用
    client.set_subagent_sleeping(agent_id, subagent_id)      # HTTP 调用
    result = biz.wake(agent_id, subagent_id)                 # HTTP 调用
```

**可能的原因**:
1. **HTTP 请求超时/卡住**: 对 Gateway 的 HTTP 请求没有响应
2. **数据库死锁**: 多个并发请求导致 SQLite 死锁
3. **异常未捕获**: Handler 抛出异常，但没有被正确处理
4. **Task Worker 进程问题**: Worker 线程卡住或崩溃

## 🔧 诊断步骤

### 1. 检查 Task Worker 进程状态

```bash
ps aux | grep main_task
# 进程还在运行，PID 66800
```

**结论**: 进程在运行，但可能某个线程卡住了。

### 2. 查看 Task Worker 日志

建议：
```bash
tail -f /tmp/task_worker.log  # 或其他日志位置
```

查找：
- message.route 相关的错误
- HTTP 请求超时
- 数据库错误

### 3. 检查 Gateway 健康状态

```bash
curl http://127.0.0.1:19999/health
```

### 4. 查看数据库锁状态

```sql
-- 检查是否有长时间运行的连接
SELECT * FROM pragma_database_list;
```

## 💡 解决方案

### 方案 1: 重启 Task Worker（临时解决）

```bash
# 找到 Task Worker 进程
ps aux | grep main_task

# 杀掉进程
kill -9 66800

# 重新启动
cd /Users/wangchaoqun/novaic/novaic-backend
python main_task.py > /tmp/task_worker.log 2>&1 &
```

**效果**: 清理卡住的 task，让系统恢复正常。

### 方案 2: 实现 Health Worker 自动恢复

创建一个 Health Worker 监控和恢复卡住的 task/saga：

```python
# 检查超时的 task
SELECT * FROM tq_tasks 
WHERE status = 'claimed' 
  AND (julianday('now') - julianday(heartbeat_at)) * 86400 > 60

# 重置为 pending
UPDATE tq_tasks 
SET status = 'pending', claimed_by = NULL, claimed_at = NULL
WHERE id = 'task-xxx'
```

### 方案 3: 添加超时和重试机制（根本解决）

#### 3.1 Task Worker 端

```python
# task_queue/workers/task_worker_v2.py
async def _execute_task(self, task):
    try:
        # 设置超时
        async with asyncio.timeout(self.task_timeout):  # 例如 60 秒
            result = await handler(payload, ctx)
    except asyncio.TimeoutError:
        logger.error(f"Task {task_id} timeout after {self.task_timeout}s")
        await self._fail_task(task_id, "Execution timeout")
    except Exception as e:
        logger.error(f"Task {task_id} failed: {e}")
        await self._fail_task(task_id, str(e))
```

#### 3.2 HTTP 客户端端

```python
# task_queue/business/subagent.py
class SubAgentBusiness:
    def __init__(self, gateway_url: str, timeout: float = 10.0):
        self.client = httpx.Client(
            base_url=gateway_url,
            timeout=timeout,  # 设置超时
            trust_env=False
        )
```

#### 3.3 Handler 端

```python
# task_queue/handlers/message_handlers.py
def handle_message_route(payload, ctx):
    try:
        # 添加重试逻辑
        for attempt in range(3):
            try:
                status = biz.get_status(agent_id, subagent_id)
                break
            except httpx.TimeoutException:
                if attempt == 2:
                    raise
                time.sleep(0.5 * (attempt + 1))
        
        # ... 原有逻辑
    except Exception as e:
        logger.error(f"message.route failed: {e}")
        return {"success": False, "error": str(e)}
```

### 方案 4: 优化并发和数据库访问

#### 4.1 减少 message.route 的 HTTP 调用

```python
# 优化前：每个 message.route 都要查询 SubAgent 状态
status = biz.get_status(agent_id, subagent_id)

# 优化后：批量查询或缓存
status = ctx.get("subagent_status_cache", {}).get(subagent_id)
if status is None:
    status = biz.get_status(agent_id, subagent_id)
```

#### 4.2 使用连接池

```python
# 为每个 Worker 维护一个 HTTP 连接池
self.gateway_client = httpx.Client(
    base_url=gateway_url,
    timeout=10.0,
    limits=httpx.Limits(max_connections=100, max_keepalive_connections=20)
)
```

## 📋 行动计划

### 立即执行（修复当前问题）

1. ✅ 手动清理卡住的 task 和 saga
2. ✅ 重启 Task Worker

### 短期（本周内）

3. ✅ 添加 HTTP 请求超时（10秒）
4. ✅ 添加 Task 执行超时（60秒）
5. ✅ 改进错误处理和日志

### 中期（下周）

6. ✅ 实现 Health Worker 自动恢复
7. ✅ 添加重试机制
8. ✅ 优化数据库并发访问

## 🚨 临时修复命令

```bash
# 1. 清理卡住的 task
sqlite3 ~/.novaic/novaic.db "UPDATE tq_tasks SET status='failed', error='Manual cleanup: timeout' WHERE status='claimed' AND (julianday('now') - julianday(heartbeat_at)) * 86400 > 60"

# 2. 清理卡住的 saga
sqlite3 ~/.novaic/novaic.db "UPDATE tq_sagas SET status='failed', error='Manual cleanup: timeout' WHERE status='running' AND (julianday('now') - julianday(heartbeat_at)) * 86400 > 60"

# 3. 重启 Task Worker
pkill -f main_task
cd /Users/wangchaoqun/novaic/novaic-backend
nohup python main_task.py > /tmp/task_worker.log 2>&1 &
```

## 📊 监控建议

添加监控指标：
- Task 平均执行时间
- Task 超时次数
- Saga 卡住次数
- HTTP 请求超时次数
- 数据库锁等待时间

当异常指标超过阈值时告警。
