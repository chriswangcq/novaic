# FIFO Lock 修复报告

## 📋 概述

修复了 Gateway 在高并发下间歇性返回 500 错误的问题。根本原因是数据库事务管理不当。

**修复时间：** 2026-02-04  
**影响范围：** TaskQueue 和 Saga 数据库操作  
**验证结果：** ✅ 50个Worker并发15秒无错误

---

## 🐛 问题描述

### 错误现象

```bash
# Worker请求收到500错误
TaskQueueError: Failed to parse JSON from http://127.0.0.1:19999/internal/tq/tasks/claim: 
Expecting value: line 1 column 1 (char 0), content: Internal Server Error
```

### 根本原因

Gateway日志显示：

```python
sqlite3.OperationalError: cannot commit - no transaction is active
```

**分析：**
- 使用 Python 的 `threading.Lock()` (`self._lock`) 管理并发
- 手动调用 `self.db.commit()`
- 在高并发下，SQLite事务状态混乱，导致commit失败

---

## ✅ 解决方案

### 修复策略

1. **移除手动事务管理**
   - 删除所有 `self._lock` 使用
   - 删除所有手动 `self.db.commit()` 调用

2. **使用FIFO Lock事务管理器**
   - 使用 `self.db.transaction()` 上下文管理器
   - 自动处理 commit/rollback
   - 使用分片锁提高并发性能

### 锁类型选择规则

| 操作类型 | 锁类型 | resource_id | 说明 |
|---------|--------|-------------|------|
| `claim()` | `global` | 无 | 不知道要操作哪个资源 |
| `publish()` | `global` | 无 | 创建新资源 |
| `complete()` | `task` | task_id | 已知task_id，使用分片锁 |
| `fail()` | `task` | task_id | 已知task_id，使用分片锁 |
| `heartbeat()` | `task` | task_id | 已知task_id，使用分片锁 |
| `recover_stale()` | `global` | 无 | 批量操作 |
| `get()` | 无锁 | - | 只读操作 |

---

## 📝 修改清单

### gateway/task_queue/queue_db.py

修复了 **7个方法**：

#### 1. `publish()` - 发布任务

**修改前：**
```python
with self._lock:
    self.db.execute(...)
    self.db.commit()
    return task_id
```

**修改后：**
```python
with self.db.transaction(lock_type="global"):
    self.db.execute(...)
    return task_id
```

#### 2. `claim()` - 认领任务

**修改后：**
```python
with self.db.transaction(lock_type="global"):  # 不知道task_id，用global
    cursor = self.db.execute("""
        UPDATE tq_tasks SET ...
        WHERE id = (SELECT id FROM tq_tasks WHERE status = 'pending' ...)
        RETURNING *
    """)
    row = cursor.fetchone()
    cursor.close()
    return self._row_to_dict(row) if row else None
```

#### 3. `complete()` - 完成任务

**修改后：**
```python
with self.db.transaction(lock_type="task", resource_id=task_id):  # 已知task_id
    cursor = self.db.execute("UPDATE tq_tasks SET status = 'done' ...")
    rowcount = cursor.rowcount
    cursor.close()
    return rowcount > 0
```

#### 4. `fail()` - 失败任务

**修改后：**
```python
with self.db.transaction(lock_type="task", resource_id=task_id):
    # 根据retry参数决定是重试还是标记失败
    ...
```

#### 5. `heartbeat()` - 心跳更新

**修改后：**
```python
with self.db.transaction(lock_type="task", resource_id=task_id):
    cursor = self.db.execute("UPDATE tq_tasks SET heartbeat_at = ? ...")
    return cursor.rowcount > 0
```

#### 6. `recover_stale()` - 恢复超时任务

**修改后：**
```python
with self.db.transaction(lock_type="global"):  # 批量操作
    cursor = self.db.execute("UPDATE tq_tasks SET status = ... WHERE ...")
    rows = cursor.fetchall()
    cursor.close()
    return len(rows) if rows else 0
```

#### 7. 只读方法 - 移除锁

```python
# get_task(), get_task_by_idempotency_key(), count_by_status()
# 移除 with self._lock，直接执行查询
```

---

### gateway/task_queue/saga_repo.py

修复了 **9个方法**：

#### 1. `create()` - 创建Saga

**修改后：**
```python
with self.db.transaction(lock_type="global"):
    self.db.execute("INSERT INTO tq_sagas ...")
    return saga_id
```

#### 2. `claim()` - 认领Saga

**修改后：**
```python
with self.db.transaction(lock_type="global"):  # 不知道saga_id
    cursor = self.db.execute("UPDATE tq_sagas SET status = 'running' ...")
    row = cursor.fetchone()
    cursor.close()
    return self._row_to_dict(row) if row else None
```

#### 3. `heartbeat()` - Saga心跳

**修改后：**
```python
with self.db.transaction(lock_type="saga", resource_id=saga_id):  # 已知saga_id
    cursor = self.db.execute("UPDATE tq_sagas SET heartbeat_at = ? ...")
    return cursor.rowcount > 0
```

#### 4. `update_progress()` - 更新进度

**修改后：**
```python
with self.db.transaction(lock_type="saga", resource_id=saga_id):
    self.db.execute("UPDATE tq_sagas SET current_step = ?, step_results = ? ...")
```

#### 5. `mark_completed()` - 标记完成

**修改后：**
```python
with self.db.transaction(lock_type="saga", resource_id=saga_id):
    cursor = self.db.execute("UPDATE tq_sagas SET status = 'completed' ...")
    cursor.close()
```

#### 6. `mark_failed()` - 标记失败

**修改后：**
```python
with self.db.transaction(lock_type="saga", resource_id=saga_id):
    self.db.execute("UPDATE tq_sagas SET status = 'failed', error = ? ...")
```

#### 7. `recover_stale()` - 恢复超时Saga

**修改后：**
```python
with self.db.transaction(lock_type="global"):  # 批量操作
    cursor = self.db.execute("UPDATE tq_sagas SET status = 'pending' ...")
    rows = cursor.fetchall()
    cursor.close()
    return len(rows) if rows else 0
```

#### 8. `start()` - 启动Saga（测试用）

**修改后：**
```python
with self.db.transaction(lock_type="global"):
    self.db.execute("INSERT INTO tq_sagas ...")
# 后续步骤调用其他方法（已修复）
```

#### 9. 只读方法

```python
# get(), get_by_idempotency_key(), get_pending()
# 移除 with self._lock，直接执行查询
```

---

## 🧪 测试验证

### 测试1: 基本功能

```bash
curl -X POST http://127.0.0.1:19999/internal/tq/tasks/claim \
  -H "Content-Type: application/json" \
  -d '{"topics": ["test"], "worker_id": "test"}'
```

**结果：** ✅ 返回 `{"task":null}` (200 OK)

### 测试2: 并发测试（20 Workers）

```bash
python -m task_queue.workers.task_worker_sync 20
```

**运行时间：** 10秒  
**结果：** ✅ 无错误

### 测试3: 高并发压力测试（50 Workers）

```bash
python -m task_queue.workers.task_worker_sync 50
```

**运行时间：** 15秒  
**结果：** ✅ 无错误

### Gateway 日志验证

```bash
grep -i "error\|exception" gateway.log | tail -20
```

**结果：** ✅ 无新增错误（只有之前的历史错误）

---

## 📊 性能对比

| 指标 | 修复前 | 修复后 |
|------|--------|--------|
| 20 Workers 并发 | ❌ 间歇性500错误 | ✅ 稳定运行 |
| 50 Workers 并发 | ❌ 大量500错误 | ✅ 稳定运行 |
| Gateway 响应 | ❌ "Internal Server Error" | ✅ 正确JSON响应 |
| SQLite 事务 | ❌ "cannot commit" 错误 | ✅ 无事务错误 |

---

## ⚠️ 遗留任务

以下文件仍使用手动 `self.db.commit()`，但不在高并发关键路径上：

### 低优先级修复

1. **gateway/core/task_manager.py** (3处)
   - 影响：内部任务管理，非高并发
   
2. **gateway/vm/repository.py** (6处)
   - 影响：VM管理，低频操作
   
3. **gateway/db/repositories/*.py** (多处)
   - 影响：业务逻辑层，已有应用层事务控制

**建议：** 观察运行，如发现问题再修复

---

## 🎯 最佳实践

### ✅ 推荐做法

```python
# 1. 已知resource_id的操作（使用分片锁）
with self.db.transaction(lock_type="task", resource_id=task_id):
    self.db.execute("UPDATE tq_tasks SET status = 'done' WHERE id = ?", (task_id,))

# 2. 不知道resource_id的操作（使用全局锁）
with self.db.transaction(lock_type="global"):
    cursor = self.db.execute("SELECT id FROM tq_tasks WHERE status = 'pending' LIMIT 1")
    row = cursor.fetchone()

# 3. 只读操作（无需锁）
cursor = self.db.execute("SELECT * FROM tq_tasks WHERE id = ?", (task_id,))
row = cursor.fetchone()
```

### ❌ 避免做法

```python
# ❌ 不要手动管理事务
with self._lock:
    self.db.execute(...)
    self.db.commit()

# ❌ 不要在事务外手动commit
self.db.execute(...)
self.db.commit()
```

---

## 📚 相关文档

- `gateway/db/locks.py` - FIFO Lock 实现
- `gateway/db/database.py` - Database 事务管理
- `STATUS.md` - 当前状态报告
- `MIGRATION_COMPLETE.md` - 同步迁移完整报告

---

**修复完成时间：** 2026-02-04 16:45  
**验证状态：** ✅ 通过  
**可以部署：** ✅ 是
