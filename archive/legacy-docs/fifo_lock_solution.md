# 数据库锁 FIFO 解决方案

## 🔍 问题分析

### SQLite 锁机制的问题

1. **不保证 FIFO**
   - 当多个连接等待同一个锁时，唤醒顺序是**随机的**
   - 可能导致某些请求**饥饿**（starvation）
   - 在高并发场景下，新请求可能插队

2. **当前设置**
   ```python
   self._conn.execute("PRAGMA busy_timeout = 5000")  # 5 秒超时
   ```
   
   **问题**：
   - 如果 5 秒内锁没有释放，会抛出 `sqlite3.OperationalError: database is locked`
   - 但**不保证等待队列的顺序**
   - 可能出现后来的请求先获得锁

3. **高并发场景**
   ```
   时刻 T0: 请求 A 开始等待锁
   时刻 T1: 请求 B 开始等待锁
   时刻 T2: 请求 C 开始等待锁
   时刻 T3: 锁释放
   
   理想（FIFO）: A 获得锁
   实际（SQLite）: B 或 C 可能先获得锁 ← 不公平！
   ```

## 💡 解决方案

### 方案 1: 应用层 FIFO 队列 ⭐ 推荐

在应用层实现 FIFO 队列，确保按顺序执行数据库操作。

```python
import asyncio
import threading
from collections import deque
from contextlib import contextmanager

class FIFODatabaseLock:
    """
    应用层 FIFO 锁，确保数据库操作按顺序执行
    """
    
    def __init__(self):
        self._lock = threading.Lock()
        self._queue = deque()
        self._current_holder = None
    
    @contextmanager
    def acquire(self):
        """
        获取锁（FIFO）
        
        Example:
            with db.fifo_lock.acquire():
                conn.execute("UPDATE ...")
        """
        # 创建一个事件，用于通知轮到我了
        my_event = threading.Event()
        
        # 加入队列
        with self._lock:
            self._queue.append(my_event)
            
            # 如果队列中只有我，立即开始
            if len(self._queue) == 1:
                my_event.set()
        
        # 等待轮到我
        my_event.wait()
        
        try:
            yield
        finally:
            # 释放锁，通知下一个
            with self._lock:
                self._queue.popleft()  # 移除自己
                
                # 通知下一个
                if self._queue:
                    self._queue[0].set()


class Database:
    def __init__(self, db_path: Path):
        self.db_path = db_path
        self._conn = None
        self.fifo_lock = FIFODatabaseLock()  # ← 添加 FIFO 锁
    
    def execute_fifo(self, sql: str, params: tuple = ()):
        """
        使用 FIFO 锁执行 SQL
        """
        with self.fifo_lock.acquire():
            return self._conn.execute(sql, params)
    
    @contextmanager
    def transaction_fifo(self):
        """
        FIFO 事务
        """
        with self.fifo_lock.acquire():
            try:
                yield self._conn
                self._conn.commit()
            except Exception as e:
                self._conn.rollback()
                raise
```

**使用示例**：

```python
# 方式 1: 单条语句
db.execute_fifo(
    "UPDATE chat_messages SET status='sent' WHERE id=?",
    (message_id,)
)

# 方式 2: 事务
with db.transaction_fifo() as conn:
    conn.execute("UPDATE chat_messages ...")
    conn.execute("INSERT INTO tq_sagas ...")
```

**优点**：
- ✅ 保证 FIFO 顺序
- ✅ 避免饥饿
- ✅ 在应用层实现，不依赖数据库
- ✅ 可以添加优先级（扩展）

**缺点**：
- ❌ 只对单个进程有效（多进程需要其他方案）
- ❌ 增加了内存开销（队列）

---

### 方案 2: 分片锁（减少竞争）

将不同类型的操作分到不同的锁，减少竞争。

```python
class ShardedFIFOLock:
    """
    分片 FIFO 锁
    
    不同类型的操作使用不同的锁，减少竞争
    """
    
    def __init__(self, num_shards: int = 4):
        self.locks = [FIFODatabaseLock() for _ in range(num_shards)]
    
    def get_lock(self, key: str) -> FIFODatabaseLock:
        """
        根据 key 选择锁（哈希分片）
        """
        shard = hash(key) % len(self.locks)
        return self.locks[shard]


class Database:
    def __init__(self, db_path: Path):
        self.db_path = db_path
        self._conn = None
        self.sharded_lock = ShardedFIFOLock(num_shards=4)
    
    def execute_with_key(self, key: str, sql: str, params: tuple = ()):
        """
        根据 key 选择锁执行
        
        Example:
            # 不同的 message_id 可以并发
            db.execute_with_key(message_id, "UPDATE chat_messages ...")
            
            # 同一个 message_id 保证顺序
            db.execute_with_key(message_id, "UPDATE chat_messages ...")
        """
        lock = self.sharded_lock.get_lock(key)
        with lock.acquire():
            return self._conn.execute(sql, params)
```

**使用示例**：

```python
# 按 message_id 分片
db.execute_with_key(
    key=message_id,  # 同一个消息的操作顺序执行
    sql="UPDATE chat_messages SET status='sent' WHERE id=?",
    params=(message_id,)
)

# 按 agent_id 分片
db.execute_with_key(
    key=agent_id,  # 同一个 agent 的操作顺序执行
    sql="UPDATE subagents SET status='awake' WHERE agent_id=?",
    params=(agent_id,)
)
```

**优点**：
- ✅ 减少锁竞争（不同分片并发）
- ✅ 保持 FIFO（同一分片内）
- ✅ 性能更好

**缺点**：
- ❌ 需要选择合适的分片键
- ❌ 跨分片事务仍需全局锁

---

### 方案 3: 使用 Redis 实现分布式 FIFO 锁

如果需要多进程/多机器支持，使用 Redis。

```python
import redis
import time
import uuid

class RedisDistributedFIFOLock:
    """
    基于 Redis 的分布式 FIFO 锁
    """
    
    def __init__(self, redis_client: redis.Redis, key_prefix: str = "db_lock"):
        self.redis = redis_client
        self.key_prefix = key_prefix
    
    @contextmanager
    def acquire(self, resource: str, timeout: float = 30.0):
        """
        获取分布式 FIFO 锁
        
        Args:
            resource: 资源标识（如 "message_claim"）
            timeout: 超时时间（秒）
        """
        queue_key = f"{self.key_prefix}:{resource}:queue"
        lock_key = f"{self.key_prefix}:{resource}:lock"
        
        # 生成唯一 token
        token = str(uuid.uuid4())
        
        # 加入队列
        position = self.redis.rpush(queue_key, token)
        
        start_time = time.time()
        
        try:
            # 等待轮到我（FIFO）
            while True:
                # 检查队首是否是我
                first_token = self.redis.lindex(queue_key, 0)
                
                if first_token and first_token.decode() == token:
                    # 轮到我了，获取锁
                    acquired = self.redis.set(
                        lock_key,
                        token,
                        nx=True,
                        ex=int(timeout)
                    )
                    
                    if acquired:
                        break
                
                # 检查超时
                if time.time() - start_time > timeout:
                    raise TimeoutError(f"Failed to acquire lock after {timeout}s")
                
                # 等待一小段时间
                time.sleep(0.1)
            
            yield
            
        finally:
            # 释放锁
            # 使用 Lua 脚本保证原子性
            release_script = """
            if redis.call("get", KEYS[1]) == ARGV[1] then
                redis.call("del", KEYS[1])
                redis.call("lpop", KEYS[2])
                return 1
            else
                return 0
            end
            """
            self.redis.eval(release_script, 2, lock_key, queue_key, token)
```

**优点**：
- ✅ 支持多进程/多机器
- ✅ 保证 FIFO
- ✅ 分布式环境下的一致性

**缺点**：
- ❌ 需要额外的 Redis 依赖
- ❌ 网络延迟
- ❌ 复杂度增加

---

### 方案 4: 优先级队列（更灵活）

在 FIFO 基础上支持优先级。

```python
import heapq
import time

class PriorityFIFOLock:
    """
    优先级 FIFO 锁
    
    同优先级按 FIFO，不同优先级高的先执行
    """
    
    def __init__(self):
        self._lock = threading.Lock()
        self._heap = []  # (priority, timestamp, event)
        self._counter = 0  # 用于打破平手
    
    @contextmanager
    def acquire(self, priority: int = 0):
        """
        获取锁
        
        Args:
            priority: 优先级（越小越高）
                0 = 高优先级（如 Agent Loop 的操作）
                10 = 普通优先级（如 message.route）
                20 = 低优先级（如 summary）
        """
        my_event = threading.Event()
        
        with self._lock:
            # 加入堆（优先级，时间戳，事件）
            timestamp = time.time()
            counter = self._counter
            self._counter += 1
            
            heapq.heappush(self._heap, (priority, timestamp, counter, my_event))
            
            # 如果堆顶是我，立即开始
            if len(self._heap) == 1:
                my_event.set()
        
        # 等待轮到我
        my_event.wait()
        
        try:
            yield
        finally:
            with self._lock:
                # 移除自己（应该在堆顶）
                heapq.heappop(self._heap)
                
                # 通知下一个
                if self._heap:
                    _, _, _, next_event = self._heap[0]
                    next_event.set()


# 使用示例
db.priority_lock = PriorityFIFOLock()

# 高优先级：Agent Loop 的操作
with db.priority_lock.acquire(priority=0):
    conn.execute("UPDATE agent_runtimes ...")

# 普通优先级：消息路由
with db.priority_lock.acquire(priority=10):
    conn.execute("UPDATE chat_messages ...")

# 低优先级：摘要生成
with db.priority_lock.acquire(priority=20):
    conn.execute("UPDATE agent_runtimes SET summary=...")
```

**优点**：
- ✅ 保证重要操作优先执行
- ✅ 同优先级保证 FIFO
- ✅ 减少关键路径延迟

---

## 📊 方案对比

| 方案 | FIFO | 多进程 | 性能 | 复杂度 | 推荐场景 |
|------|------|--------|------|--------|----------|
| 应用层 FIFO | ✅ | ❌ | ⭐⭐⭐ | ⭐ | 单进程，简单场景 |
| 分片锁 | ✅ | ❌ | ⭐⭐⭐⭐⭐ | ⭐⭐ | 单进程，高并发 |
| Redis 分布式锁 | ✅ | ✅ | ⭐⭐⭐ | ⭐⭐⭐ | 多进程/分布式 |
| 优先级队列 | ✅ | ❌ | ⭐⭐⭐⭐ | ⭐⭐ | 需要区分优先级 |

## 🎯 推荐方案

### 当前场景（单进程 Gateway）

**推荐：方案 1（应用层 FIFO）+ 方案 2（分片锁）组合**

```python
# gateway/db/database.py

class Database:
    def __init__(self, db_path: Path):
        self.db_path = db_path
        self._conn = None
        
        # 全局 FIFO 锁（用于跨表事务）
        self.global_lock = FIFODatabaseLock()
        
        # 分片锁（用于单表操作）
        self.message_locks = ShardedFIFOLock(num_shards=8)   # 按 message_id
        self.agent_locks = ShardedFIFOLock(num_shards=4)     # 按 agent_id
        self.task_locks = ShardedFIFOLock(num_shards=8)      # 按 task_id
    
    def claim_message(self, message_id: str):
        """认领消息（使用分片锁）"""
        lock = self.message_locks.get_lock(message_id)
        with lock.acquire():
            cursor = self._conn.execute(
                "UPDATE chat_messages SET status='sent' WHERE id=? AND status='sending'",
                (message_id,)
            )
            self._conn.commit()
            return cursor.rowcount > 0
    
    def route_message(self, agent_id: str, subagent_id: str):
        """路由消息（使用 agent 分片锁）"""
        lock = self.agent_locks.get_lock(agent_id)
        with lock.acquire():
            # 多个操作在同一个锁内
            status = self._conn.execute(
                "SELECT status FROM subagents WHERE agent_id=? AND subagent_id=?",
                (agent_id, subagent_id)
            ).fetchone()
            
            if status and status['status'] == 'awake':
                runtime = self._conn.execute(
                    "SELECT runtime_id FROM agent_runtimes WHERE agent_id=? AND status='active'",
                    (agent_id,)
                ).fetchone()
                ...
            
            self._conn.commit()
```

### 如果需要多进程支持

**推荐：方案 3（Redis 分布式锁）**

但当前是单进程 Gateway，不需要。

## 💡 立即可行的改进

```python
# gateway/db/database.py

import threading
from collections import deque
from contextlib import contextmanager

class FIFOLock:
    def __init__(self):
        self._lock = threading.Lock()
        self._queue = deque()
    
    @contextmanager
    def acquire(self):
        event = threading.Event()
        
        with self._lock:
            self._queue.append(event)
            if len(self._queue) == 1:
                event.set()
        
        event.wait()
        
        try:
            yield
        finally:
            with self._lock:
                self._queue.popleft()
                if self._queue:
                    self._queue[0].set()


class Database:
    def __init__(self, db_path: Path):
        self.db_path = db_path
        self._conn = None
        self._initialized = False
        
        # 添加 FIFO 锁
        self.write_lock = FIFOLock()  # ← 新增
    
    @contextmanager
    def write_transaction(self):
        """
        FIFO 写事务
        """
        with self.write_lock.acquire():  # ← FIFO 保证
            try:
                yield self._conn
                self._conn.commit()
            except Exception as e:
                self._conn.rollback()
                raise
```

**修改 API**：

```python
# gateway/api/internal.py

@router.post("/messages/{message_id}/claim")
def claim_message(message_id: str):
    db = get_db()
    
    # 使用 FIFO 事务
    with db.write_transaction() as conn:
        cursor = conn.execute(
            "UPDATE chat_messages SET status='sent' WHERE id=? AND status='sending'",
            (message_id,)
        )
        claimed = cursor.rowcount > 0
    
    if claimed:
        return {"success": True, "message_id": message_id, "claimed": True}
    ...
```

这样就能保证 **FIFO 顺序**，避免饥饿问题！
