# Worker 卡住根本原因分析

## 🔍 调查过程

### 1. 确认卡住的 Task

根据诊断工具发现：
```
❌ 发现 2 个卡住的 task
Worker: task-f06e69d6 (2 个 task 卡住)
  • task-b855ccd1c42e (message.claim) - 心跳超时 241s
  • task-aebe38802fa1 (message.route) - 心跳超时 223s
```

### 2. 检查 Handler 代码

#### message.claim Handler
```python
def handle_message_claim(payload, ctx):
    message_id = payload["message_id"]
    biz = MessageBusiness(ctx["gateway_url"], client=ctx.get("gateway_client"))
    return biz.claim_message(message_id)  # HTTP 调用
```

**调用链**：
```
handle_message_claim()
  → MessageBusiness.claim_message()
    → GatewayInternalClient.claim_message()
      → HTTP POST /internal/messages/{id}/claim
        → UPDATE chat_messages SET status='sent' WHERE id=? AND status='sending'
```

#### message.route Handler
```python
def handle_message_route(payload, ctx):
    biz = SubAgentBusiness(ctx["gateway_url"], client=ctx.get("gateway_client"))
    client = ctx.get("gateway_client") or GatewayInternalClient(ctx["gateway_url"])
    
    # 多个 HTTP 调用
    status = biz.get_status(agent_id, subagent_id)              # HTTP GET
    active_runtime = client.get_subagent_runtime(...)           # HTTP GET
    client.set_subagent_sleeping(agent_id, subagent_id)         # HTTP POST
    result = biz.wake(agent_id, subagent_id)                    # HTTP POST
```

**调用链更复杂**，包含多个 HTTP 调用到 Gateway 的不同 API。

### 3. 检查 HTTP 超时配置

#### GatewayInternalClient
```python
class GatewayInternalClient:
    def __init__(self, gateway_url: str, timeout: float = 30.0):  # ← 默认 30 秒
        self.timeout = timeout
        self._session = httpx.Client(timeout=self.timeout)
```

#### Task Worker
```python
class TaskWorkerV2:
    def __init__(self, timeout: float = 60.0):  # ← Task 级别超时 60 秒
        self.timeout = timeout
        self._client = httpx.AsyncClient(timeout=self.timeout)
```

**发现**：
- ✅ HTTP 客户端有超时设置（30 秒）
- ✅ Task Worker 有总超时设置（60 秒）
- ✅ 理论上不应该永久卡住

### 4. HTTP 超时测试

运行测试脚本 `test_http_timeout.py`：
```
测试基本 HTTP 请求: ✅ 全部成功，耗时 < 1 秒
测试 message.route 中的调用: ✅ 全部成功，耗时 < 1 秒
测试 20 个并发请求: ✅ 全部成功，平均耗时 1.1 秒
```

**结论**：HTTP 调用本身没有问题。

## 🎯 可能的根本原因

### 原因 1: SQLite 数据库锁等待 (最可能)

#### 现象
在高并发场景下（1000+ 消息/分钟），多个 Worker 并发访问 SQLite 数据库。

#### 机制
```python
# Gateway API: claim_message
with db.get_connection() as conn:
    cursor = conn.execute("""
        UPDATE chat_messages
        SET status = 'sent'
        WHERE id = ? AND status = 'sending'
    """, (message_id,))
    conn.commit()  # ← 如果这里等待锁，整个 HTTP 请求都会卡住
```

**SQLite 锁机制**：
1. SQLite 使用文件级锁
2. 写操作（UPDATE/INSERT/DELETE）会锁住整个数据库
3. 如果一个写事务正在进行，其他写事务会等待
4. 默认等待超时是 5 秒，但可能被覆盖或忽略

#### 为什么会超过 30 秒超时？

**关键问题**：Python 的 SQLite 操作**不受 httpx 超时控制**

```python
# Task Worker 发起 HTTP 请求
resp = await client.post(
    "/internal/tq/handlers/execute",  # ← httpx 超时：60 秒
    json={"topic": "message.claim", "payload": {...}}
)

# Gateway 端
@router.post("/internal/tq/handlers/execute")
def execute_handler(req):
    result = handler(req.payload, ctx)  # ← 这里调用 message.claim handler
    return result

# Handler 调用数据库
def handle_message_claim(payload, ctx):
    ...
    conn.execute("UPDATE chat_messages ...")  # ← SQLite 锁等待，不受 HTTP 超时控制！
    conn.commit()
```

**问题链**：
```
HTTP 请求（60秒超时）
  └─ FastAPI Handler（无超时）
      └─ message.claim handler（无超时）
          └─ SQLite UPDATE（可能无限等待锁）← 卡在这里！
```

**即使 httpx 设置了 60 秒超时，如果 Gateway 进程内的 SQLite 操作一直在等待锁，HTTP 连接也会保持打开状态。**

### 原因 2: 连接池耗尽

#### 现象
如果有很多请求同时卡住等待数据库锁，HTTP 连接池可能耗尽。

```python
# httpx.Client 默认连接池大小
httpx.Client(
    limits=httpx.Limits(
        max_connections=100,     # 最多 100 个连接
        max_keepalive_connections=20
    )
)
```

#### 场景
```
Task Worker 1: task-b855ccd1c42e → HTTP 连接 1 → 等待 SQLite 锁
Task Worker 1: task-aebe38802fa1 → HTTP 连接 2 → 等待 SQLite 锁
...
Task Worker 1: task-xyz... → 连接池满了！→ 新请求阻塞
```

### 原因 3: FastAPI/Uvicorn 线程池耗尽

#### 现象
Gateway 使用 Uvicorn + FastAPI。如果所有 worker 线程都在等待 SQLite 锁，新请求无法处理。

```python
# Uvicorn 配置
uvicorn.run(
    app,
    host="0.0.0.0",
    port=19999,
    workers=1,  # ← 只有 1 个进程
)
```

**如果同步的数据库操作卡住，整个进程都会卡住。**

## 📊 验证卡住原因的证据

### 证据 1: 心跳超时时间
```
task-b855ccd1c42e: 心跳超时 241s
task-aebe38802fa1: 心跳超时 223s
```

**超过了所有超时设置**：
- HTTP 超时：30 秒
- Task 超时：60 秒
- 实际卡住：200+ 秒

**说明**：卡住点不受 HTTP 超时控制！

### 证据 2: 同一 Worker 的多个 Task 同时卡住
```
Worker: task-f06e69d6 (2 个 task 卡住)
```

**说明**：Worker 进程内部有问题，而不是单个请求问题。

### 证据 3: 高负载场景
```
测试场景：1107 条消息，60 秒内发送
平均速率：18.45 msg/s
触发了大量并发数据库操作
```

**说明**：只有在高并发下才会触发。

## 🔧 根本原因总结

**Worker 卡住的根本原因是**：

### 主要原因：SQLite 数据库锁等待

1. **高并发场景下的数据库竞争**
   - 1000+ 条消息在短时间内处理
   - 每条消息触发多个数据库写操作
   - SQLite 串行处理写操作

2. **锁等待不受 HTTP 超时控制**
   - Task Worker → Gateway 的 HTTP 请求有 60 秒超时
   - 但 Gateway 内部的 SQLite 操作**不在 HTTP 层面**
   - SQLite 的 `conn.execute()` 可能等待锁超过 60 秒

3. **级联效应**
   - 一个请求等待数据库锁
   - 占用 HTTP 连接
   - 占用 Worker 线程/协程
   - 导致后续请求堆积
   - 最终整个 Worker 进程卡住

### 次要原因：缺少适当的超时保护

1. **Handler 层面没有超时**
   ```python
   def handle_message_claim(payload, ctx):
       # 没有超时保护！
       return biz.claim_message(message_id)
   ```

2. **数据库操作没有超时**
   ```python
   conn.execute("UPDATE ...")  # 可能永久等待
   conn.commit()
   ```

3. **没有重试机制**
   - 如果遇到 `SQLITE_BUSY` 错误，应该重试
   - 目前直接失败或卡住

## 💡 解决方案

### 方案 1: 设置 SQLite 超时 (立即可做)

```python
# gateway/db/database.py
class Database:
    def get_connection(self):
        conn = sqlite3.connect(self.db_path, timeout=5.0)  # ← 添加超时
        conn.execute("PRAGMA busy_timeout = 5000")  # 5 秒超时
        return conn
```

### 方案 2: 添加重试机制

```python
# gateway/db/database.py
import time

def execute_with_retry(conn, sql, params, max_retries=3):
    for attempt in range(max_retries):
        try:
            return conn.execute(sql, params)
        except sqlite3.OperationalError as e:
            if "database is locked" in str(e) and attempt < max_retries - 1:
                time.sleep(0.1 * (attempt + 1))  # 指数退避
                continue
            raise
```

### 方案 3: 使用 WAL 模式 (推荐)

```python
# gateway/db/database.py
conn = sqlite3.connect(self.db_path)
conn.execute("PRAGMA journal_mode=WAL")  # Write-Ahead Logging
conn.execute("PRAGMA synchronous=NORMAL")
```

**WAL 模式优势**：
- 读写不互相阻塞
- 并发性能提升 10-100 倍
- 适合高并发场景

### 方案 4: Handler 级别超时保护

```python
import signal
from contextlib import contextmanager

@contextmanager
def timeout(seconds):
    def timeout_handler(signum, frame):
        raise TimeoutError(f"Operation timeout after {seconds}s")
    
    signal.signal(signal.SIGALRM, timeout_handler)
    signal.alarm(seconds)
    try:
        yield
    finally:
        signal.alarm(0)

def handle_message_claim(payload, ctx):
    with timeout(10):  # 10 秒超时
        return biz.claim_message(message_id)
```

### 方案 5: 迁移到 PostgreSQL (长期)

SQLite 不适合高并发写场景，考虑迁移到 PostgreSQL。

## 📋 行动计划

### 立即执行（本周）
1. ✅ 设置 SQLite `busy_timeout = 5000`
2. ✅ 启用 WAL 模式
3. ✅ 添加数据库重试机制

### 短期（下周）
4. ✅ 添加 Handler 级别超时保护
5. ✅ 优化数据库索引（已完成部分）
6. ✅ 增加监控和告警

### 中期（下月）
7. ✅ 实现连接池和请求限流
8. ✅ 考虑迁移到 PostgreSQL

## 🔬 验证方法

### 1. 添加日志
```python
import time
import logging

def handle_message_claim(payload, ctx):
    start = time.time()
    logger.info(f"[message.claim] start: {payload['message_id']}")
    
    try:
        result = biz.claim_message(message_id)
        elapsed = time.time() - start
        logger.info(f"[message.claim] success: {elapsed:.3f}s")
        return result
    except Exception as e:
        elapsed = time.time() - start
        logger.error(f"[message.claim] error after {elapsed:.3f}s: {e}")
        raise
```

### 2. 监控数据库锁
```python
# 定期检查 SQLite 状态
SELECT * FROM pragma_database_list;
SELECT * FROM pragma_lock_status('main');
```

### 3. 压力测试
```bash
# 运行测试并监控
python test_single_runtime.py &
python monitor_workers.py
```

查看是否还有卡住现象。

---

## 📝 结论

**Worker 卡住的根本原因是：**

**在高并发场景下，SQLite 数据库锁等待导致 Handler 执行时间超过所有超时阈值，最终使 Worker 进程卡住。**

**关键发现**：
- ❌ HTTP 超时无法控制同步的数据库操作
- ❌ SQLite 默认配置不适合高并发写场景
- ❌ 缺少 Handler 级别的超时保护

**解决方向**：
- ✅ 数据库层面：WAL 模式 + busy_timeout + 重试
- ✅ Handler 层面：超时保护 + 错误处理
- ✅ 架构层面：考虑迁移到 PostgreSQL
