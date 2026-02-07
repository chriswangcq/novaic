# 数据一致性与级联删除

> 基于 2026-02-07 Agent 删除残留数据问题的诊断与修复经验总结

## 目录

1. [问题发现：删除后的残留数据](#1-问题发现删除后的残留数据)
2. [外键约束的重要性](#2-外键约束的重要性)
3. [级联删除策略](#3-级联删除策略)
4. [孤立数据检测与清理](#4-孤立数据检测与清理)
5. [删除操作最佳实践](#5-删除操作最佳实践)

---

## 1. 问题发现：删除后的残留数据

### 实战案例

**用户反馈**：删除了 agent，但前端还显示旧的聊天记录和执行日志。

**诊断过程**：

#### 步骤 1：检查前端状态

```javascript
// 浏览器控制台
useAppStore.getState().agents  // []
localStorage.getItem('novaic-current-agent-id')  // "79b813e8-..."
```

**发现**：localStorage 有残留，但这不是主要问题。

#### 步骤 2：检查数据库

```sql
-- 检查 agents 表
SELECT COUNT(*) FROM agents;  -- 1（只有一个新 agent）

-- 检查 chat_messages 表
SELECT COUNT(*) FROM chat_messages;  -- 502

-- 检查孤立的消息
SELECT COUNT(*) FROM chat_messages 
WHERE agent_id NOT IN (SELECT id FROM agents);  -- 501 ❌
```

**发现**：**501 条聊天记录是孤立的**（agent 已删除）！

#### 步骤 3：全面检查所有表

```sql
-- 检查所有可能残留的表
SELECT 
    'chat_messages' as table_name,
    COUNT(*) as total,
    (SELECT COUNT(*) FROM chat_messages 
     WHERE agent_id NOT IN (SELECT id FROM agents)) as orphaned
FROM chat_messages

UNION ALL

SELECT 
    'execution_logs',
    COUNT(*),
    (SELECT COUNT(*) FROM execution_logs 
     WHERE agent_id NOT IN (SELECT id FROM agents))
FROM execution_logs

UNION ALL

SELECT 
    'tasks',
    COUNT(*),
    (SELECT COUNT(*) FROM tasks 
     WHERE agent_id NOT IN (SELECT id FROM agents))
FROM tasks;
```

**结果**：
| 表名 | 总数 | 孤立数据 |
|------|------|---------|
| chat_messages | 502 | 501 |
| execution_logs | 2570 | 2570 |
| tasks | 2 | 2 |

**结论**：几乎所有历史数据都是孤立的！❌

---

## 2. 外键约束的重要性

### 什么是外键约束

外键约束确保数据库中的引用完整性：

```sql
CREATE TABLE chat_messages (
    id INTEGER PRIMARY KEY,
    agent_id TEXT NOT NULL,
    content TEXT,
    -- 外键约束
    FOREIGN KEY (agent_id) REFERENCES agents(id) ON DELETE CASCADE
);
```

**含义**：
- `FOREIGN KEY (agent_id)` - agent_id 是外键
- `REFERENCES agents(id)` - 引用 agents 表的 id 列
- `ON DELETE CASCADE` - 删除 agent 时，自动删除相关的 chat_messages

### CASCADE 删除选项

| 选项 | 行为 | 使用场景 |
|------|------|---------|
| `ON DELETE CASCADE` | 自动删除相关数据 | 强关联数据（消息、日志）|
| `ON DELETE SET NULL` | 设置为 NULL | 弱关联数据（会话）|
| `ON DELETE RESTRICT` | 禁止删除（有引用时）| 防止误删 |
| `ON DELETE NO ACTION` | 默认行为（通常报错）| 不推荐 |

### 本项目的外键约束现状

#### 有 CASCADE 约束的表 ✅

```sql
-- 这些表会自动清理
agent_state          -- FOREIGN KEY (agent_id) ... ON DELETE CASCADE
agent_memory         -- FOREIGN KEY (agent_id) ... ON DELETE CASCADE
agent_task_history   -- FOREIGN KEY (agent_id) ... ON DELETE CASCADE
vm_processes         -- FOREIGN KEY (agent_id) ... ON DELETE CASCADE
subagents            -- FOREIGN KEY (agent_id) ... ON DELETE CASCADE
agent_runtimes       -- FOREIGN KEY (agent_id) ... ON DELETE CASCADE
```

#### 缺少约束的表 ❌（问题根源）

```sql
-- 这些表不会自动清理，导致数据残留
chat_messages        -- 只有 agent_id 字段，没有外键约束
execution_logs       -- 只有 agent_id 字段，没有外键约束
tasks                -- 只有 agent_id 字段，没有外键约束
pipeline_tasks       -- 只有 agent_id 字段，没有外键约束
pending_questions    -- 只有 agent_id 字段，没有外键约束
agent_runtime_state  -- 只有 agent_id 字段，没有外键约束
```

### 为什么缺少外键约束

可能的原因：
1. **历史遗留**：早期开发时没有添加
2. **逐步演化**：表是后来添加的，忘记加约束
3. **手动管理**：假设应用层会处理删除
4. **迁移困难**：SQLite 不支持 `ALTER TABLE ADD CONSTRAINT`

---

## 3. 级联删除策略

### 策略 A：数据库级 CASCADE（推荐）

**原理**：利用数据库的外键约束自动级联删除

**优点**：
- ✅ 可靠（数据库保证）
- ✅ 自动（无需应用层代码）
- ✅ 原子性（在事务中）
- ✅ 性能好（数据库优化）

**实现**：

```sql
-- 新建表时添加外键约束
CREATE TABLE chat_messages (
    id INTEGER PRIMARY KEY,
    agent_id TEXT NOT NULL,
    content TEXT,
    timestamp TEXT,
    FOREIGN KEY (agent_id) REFERENCES agents(id) ON DELETE CASCADE
);
```

**限制**：
- SQLite 不支持直接 `ALTER TABLE ADD CONSTRAINT`
- 需要重建表或使用数据库迁移

### 策略 B：应用层手动删除（兼容方案）

**原理**：在应用层代码中手动删除相关数据

**优点**：
- ✅ 兼容旧数据库（无需迁移）
- ✅ 灵活（可以有复杂逻辑）
- ✅ 可控（可以记录日志）

**缺点**：
- ❌ 容易遗漏（需要人工维护列表）
- ❌ 不可靠（代码可能有 bug）
- ❌ 性能略差（多次 SQL 调用）

**实现**：

```python
def delete_agent(self, agent_id: str) -> bool:
    """Delete an agent and all related data."""
    
    # 获取数据库连接
    db = get_db()
    
    # 在事务中删除所有相关数据
    with db.transaction("agent_deletion", resource_id=agent_id):
        # 手动删除相关数据
        db.execute("DELETE FROM chat_messages WHERE agent_id = ?", (agent_id,))
        db.execute("DELETE FROM execution_logs WHERE agent_id = ?", (agent_id,))
        db.execute("DELETE FROM tasks WHERE agent_id = ?", (agent_id,))
        db.execute("DELETE FROM pending_questions WHERE agent_id = ?", (agent_id,))
        db.execute("DELETE FROM agent_runtime_state WHERE agent_id = ?", (agent_id,))
        db.execute("DELETE FROM pipeline_tasks WHERE agent_id = ?", (agent_id,))
        
        # 最后删除 agent 本身（会触发 CASCADE 删除其他表）
        success = self.repo.delete_agent(agent_id)
    
    return success
```

### 策略 C：混合方案（最佳实践）

**策略**：
1. **新表**：使用数据库级 CASCADE
2. **旧表**：应用层手动删除（兼容）
3. **双重保险**：应用层删除 + 数据库 CASCADE

**优点**：
- ✅ 新数据库自动级联
- ✅ 旧数据库手动清理
- ✅ 双重保障（更可靠）

**实现**：

```python
# schema.py - 新表添加外键约束
CREATE TABLE chat_messages (
    ...
    FOREIGN KEY (agent_id) REFERENCES agents(id) ON DELETE CASCADE
);

# agents_db.py - 应用层手动删除（兼容旧数据库）
def delete_agent(self, agent_id: str) -> bool:
    db = get_db()
    with db.transaction("agent_deletion", resource_id=agent_id):
        # 手动清理（兼容旧数据库）
        db.execute("DELETE FROM chat_messages WHERE agent_id = ?", (agent_id,))
        # ... 其他表
        
        # 删除 agent（新数据库会触发 CASCADE，手动删除作为冗余）
        success = self.repo.delete_agent(agent_id)
    return success
```

---

## 4. 孤立数据检测与清理

### 检测孤立数据

**通用查询模板**：

```sql
-- 检测单个表的孤立数据
SELECT COUNT(*) 
FROM {table_name}
WHERE agent_id NOT IN (SELECT id FROM agents);

-- 检测所有表的孤立数据
SELECT 
    '{table_name}' as table_name,
    COUNT(*) as total,
    (SELECT COUNT(*) FROM {table_name} 
     WHERE agent_id NOT IN (SELECT id FROM agents)) as orphaned
FROM {table_name};
```

**实战脚本**：

```bash
#!/bin/bash
# check_orphaned_data.sh

DB_PATH=~/Library/Application\ Support/com.novaic.app/novaic.db

sqlite3 "$DB_PATH" << 'SQL'
.headers on
.mode column

SELECT 'Table' as table_name, 'Total' as total, 'Orphaned' as orphaned
UNION ALL
SELECT 'chat_messages', 
       COUNT(*), 
       (SELECT COUNT(*) FROM chat_messages 
        WHERE agent_id NOT IN (SELECT id FROM agents))
FROM chat_messages
UNION ALL
SELECT 'execution_logs', 
       COUNT(*), 
       (SELECT COUNT(*) FROM execution_logs 
        WHERE agent_id NOT IN (SELECT id FROM agents))
FROM execution_logs
UNION ALL
SELECT 'tasks', 
       COUNT(*), 
       (SELECT COUNT(*) FROM tasks 
        WHERE agent_id NOT IN (SELECT id FROM agents))
FROM tasks;
SQL
```

### 清理孤立数据

**一次性清理脚本**：

```sql
-- 在事务中清理所有孤立数据
BEGIN TRANSACTION;

-- 删除孤立的 chat_messages
DELETE FROM chat_messages 
WHERE agent_id NOT IN (SELECT id FROM agents);

-- 删除孤立的 execution_logs
DELETE FROM execution_logs 
WHERE agent_id NOT IN (SELECT id FROM agents);

-- 删除孤立的 tasks
DELETE FROM tasks 
WHERE agent_id NOT IN (SELECT id FROM agents);

-- 删除孤立的 pipeline_tasks（保留系统级任务）
DELETE FROM pipeline_tasks 
WHERE agent_id NOT IN (SELECT id FROM agents) 
  AND agent_id IS NOT NULL;

-- 删除孤立的 pending_questions
DELETE FROM pending_questions 
WHERE agent_id NOT IN (SELECT id FROM agents);

-- 删除孤立的 agent_runtime_state
DELETE FROM agent_runtime_state 
WHERE agent_id NOT IN (SELECT id FROM agents);

COMMIT;

-- 验证清理结果
SELECT 'After cleanup:' as status;
SELECT 
    'chat_messages' as table_name,
    COUNT(*) as remaining,
    (SELECT COUNT(*) FROM chat_messages 
     WHERE agent_id NOT IN (SELECT id FROM agents)) as orphaned
FROM chat_messages;
```

### 定期检测机制

**应用层定时任务**：

```python
# novaic-backend/gateway/maintenance.py

import asyncio
from gateway.db import get_db

async def cleanup_orphaned_data():
    """定期清理孤立数据（防御性编程）"""
    db = get_db()
    
    tables = [
        "chat_messages",
        "execution_logs",
        "tasks",
        "pending_questions",
        "agent_runtime_state",
    ]
    
    with db.transaction("orphan_cleanup"):
        for table in tables:
            result = db.execute(
                f"DELETE FROM {table} WHERE agent_id NOT IN (SELECT id FROM agents)"
            )
            if result.rowcount > 0:
                logger.warning(f"Cleaned {result.rowcount} orphaned rows from {table}")

# 在后台定期执行（例如每小时）
async def background_maintenance():
    while True:
        await asyncio.sleep(3600)  # 1 小时
        await cleanup_orphaned_data()
```

---

## 5. 删除操作最佳实践

### 完整的删除流程

```python
def delete_agent(self, agent_id: str) -> bool:
    """Delete an agent and all related resources."""
    
    agent = self.get_agent(agent_id)
    if not agent:
        return False
    
    # 1. 停止 VM 进程和服务
    try:
        from gateway.vm.manager import get_vm_manager
        vm_manager = get_vm_manager()
        vm_manager.stop(agent_id, graceful=True, quick=False)
    except Exception as e:
        logger.warning(f"Failed to stop VM for agent {agent_id}: {e}")
    
    # 2. 清理数据库中的数据
    db = get_db()
    with db.transaction("agent_deletion", resource_id=agent_id):
        # 手动删除没有外键约束的表
        db.execute("DELETE FROM chat_messages WHERE agent_id = ?", (agent_id,))
        db.execute("DELETE FROM execution_logs WHERE agent_id = ?", (agent_id,))
        db.execute("DELETE FROM tasks WHERE agent_id = ?", (agent_id,))
        db.execute("DELETE FROM pipeline_tasks WHERE agent_id = ?", (agent_id,))
        db.execute("DELETE FROM pending_questions WHERE agent_id = ?", (agent_id,))
        db.execute("DELETE FROM agent_runtime_state WHERE agent_id = ?", (agent_id,))
        
        # 删除 agent 记录（会触发 CASCADE 删除有外键的表）
        success = self.repo.delete_agent(agent_id)
    
    # 3. 清理文件系统资源
    if success:
        # 删除 VM 目录
        vm_dir = self._get_agent_vm_dir(agent_id)
        if vm_dir.exists():
            shutil.rmtree(vm_dir)
        
        # 删除 socket 文件
        for sock_file in [
            f"/tmp/novaic/novaic-qmp-{agent_id}.sock",
            f"/tmp/novaic/novaic-vnc-{agent_id}.sock",
        ]:
            if Path(sock_file).exists():
                Path(sock_file).unlink()
    
    # 4. 通知其他服务（如果需要）
    try:
        await vmcontrol_client.unregister_vm(agent_id)
    except Exception as e:
        logger.warning(f"Failed to unregister VM from vmcontrol: {e}")
    
    return success
```

### 删除操作 Checklist

**数据库层**：
- [ ] 使用事务（保证原子性）
- [ ] 删除所有相关表的数据
- [ ] 检查是否有孤立数据

**进程层**：
- [ ] 停止 VM 进程
- [ ] 清理 socket 文件
- [ ] 断开网络连接

**文件系统层**：
- [ ] 删除 VM 磁盘文件
- [ ] 删除配置文件
- [ ] 删除临时文件

**状态同步层**：
- [ ] 通知其他服务（vmcontrol）
- [ ] 清理内存缓存
- [ ] 断开 SSE 连接

### 常见陷阱

#### 陷阱 1：忘记清理文件系统

```python
# ❌ 只删除数据库记录
db.execute("DELETE FROM agents WHERE id = ?", (agent_id,))

# ✅ 同时清理文件系统
db.execute("DELETE FROM agents WHERE id = ?", (agent_id,))
vm_dir = f"/path/to/vms/{agent_id}"
if os.path.exists(vm_dir):
    shutil.rmtree(vm_dir)
```

#### 陷阱 2：没有使用事务

```python
# ❌ 没有事务，可能部分成功
db.execute("DELETE FROM chat_messages WHERE agent_id = ?", (agent_id,))
# 如果这里出错，chat_messages 已删除但 agent 还在
db.execute("DELETE FROM agents WHERE id = ?", (agent_id,))

# ✅ 使用事务，要么全成功，要么全失败
with db.transaction("agent_deletion"):
    db.execute("DELETE FROM chat_messages WHERE agent_id = ?", (agent_id,))
    db.execute("DELETE FROM agents WHERE id = ?", (agent_id,))
```

#### 陷阱 3：删除顺序错误

```python
# ❌ 先删除 agent，CASCADE 可能不完整
db.execute("DELETE FROM agents WHERE id = ?", (agent_id,))
# 这些表没有外键约束，不会自动删除
db.execute("DELETE FROM chat_messages WHERE agent_id = ?", (agent_id,))

# ✅ 先删除子表，最后删除主表
db.execute("DELETE FROM chat_messages WHERE agent_id = ?", (agent_id,))
db.execute("DELETE FROM execution_logs WHERE agent_id = ?", (agent_id,))
# 最后删除 agent（触发 CASCADE 删除有外键的表）
db.execute("DELETE FROM agents WHERE id = ?", (agent_id,))
```

---

## 总结：数据一致性最佳实践

### 设计阶段

1. **新表必须添加外键约束**
   ```sql
   FOREIGN KEY (agent_id) REFERENCES agents(id) ON DELETE CASCADE
   ```

2. **选择合适的 CASCADE 策略**
   - 强关联：`ON DELETE CASCADE`
   - 弱关联：`ON DELETE SET NULL`
   - 防误删：`ON DELETE RESTRICT`

3. **避免循环引用**
   - 注意外键依赖关系
   - 可能需要软删除

### 开发阶段

1. **删除操作使用事务**
   ```python
   with db.transaction("deletion"):
       # 所有删除操作
   ```

2. **手动清理 + 外键双保险**
   ```python
   # 手动清理（兼容旧数据库）
   db.execute("DELETE FROM child WHERE parent_id = ?", (id,))
   # 删除主记录（新数据库会 CASCADE）
   db.execute("DELETE FROM parent WHERE id = ?", (id,))
   ```

3. **清理所有资源**
   - 数据库记录
   - 文件系统
   - 进程和连接
   - 内存状态

### 运维阶段

1. **定期检测孤立数据**
   ```sql
   SELECT COUNT(*) FROM child 
   WHERE parent_id NOT IN (SELECT id FROM parent);
   ```

2. **定期清理孤立数据**
   ```python
   # 后台定时任务
   async def cleanup_orphaned_data():
       # 清理逻辑
   ```

3. **监控删除操作**
   - 记录删除日志
   - 统计删除数量
   - 异常告警

### 关键原则

1. **外键约束优先**：利用数据库保证一致性
2. **防御性编程**：应用层手动清理作为冗余
3. **全面清理**：不只是数据库，还有文件、进程
4. **原子操作**：使用事务保证一致性
5. **定期检查**：发现和修复数据不一致

---

*最后更新：2026-02-07*
*案例：Agent 删除数据残留问题修复*
