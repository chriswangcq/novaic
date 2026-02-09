# notebook_write 工具 HTTP 500 错误分析报告

## 错误信息
- **时间**: 2026-02-09 03:20:55 UTC
- **Runtime**: rt-8b72a6172462
- **SubAgent**: main-44c145ec
- **工具**: notebook_write
- **参数**:
  - type: "observation"
  - title: "桌面环境状态观察 - 2026-02-09 03:20 UTC"
  - content: 定时唤醒后的桌面状态描述
  - tags: Array(3)
- **错误**: HTTP 500: Internal Server Error

---

## 调用链分析

### 1. 工具调用入口
**文件**: `novaic-backend/tools_server/executor.py:375-387`

```python
elif tool_name == "notebook_write":
    response = await client.post(
        f"/internal/rt/{self.runtime_id}/notebook/write",
        json={
            "entry_type": arguments.get("entry_type"),
            "title": arguments.get("title"),
            "content": arguments.get("content"),
            "related_topics": arguments.get("related_topics", []),
            "relevance_score": arguments.get("relevance_score", 0.5),
            "expires_at": arguments.get("expires_at"),
        }
    )
    return self._handle_response(response)
```

### 2. API 端点
**文件**: `novaic-backend/gateway/api/internal/runtime.py:829-847`

```python
@router.post("/rt/{runtime_id}/notebook/write")
def rt_notebook_write(runtime_id: str, data: Dict[str, Any]):
    """Write a new notebook entry. Agent ID resolved from runtime."""
    from gateway.db.repositories.notebook import NotebookRepository
    
    _, agent_id, _ = resolve_runtime_ids(runtime_id)
    
    db = get_db()
    repo = NotebookRepository(db)
    return repo.write(
        agent_id=agent_id,
        entry_type=data.get("entry_type", "observation"),
        title=data.get("title", "Untitled"),
        content=data.get("content", ""),
        source=f"runtime:{runtime_id}",
        related_topics=data.get("related_topics"),
        relevance_score=data.get("relevance_score", 0.5),
        expires_at=data.get("expires_at"),
    )
```

### 3. Repository 实现
**文件**: `novaic-backend/gateway/db/repositories/notebook.py:19-53`

```python
def write(
    self,
    agent_id: str,
    entry_type: str,
    title: str,
    content: str,
    source: Optional[str] = None,
    related_topics: Optional[List[str]] = None,
    relevance_score: float = 0.5,
    expires_at: Optional[str] = None,
) -> Dict[str, Any]:
    """Create a new notebook entry."""
    now = datetime.utcnow().isoformat()
    topics_json = json.dumps(related_topics or [], ensure_ascii=False)
    relevance_score = max(0.0, min(1.0, relevance_score))
    
    with self.db.transaction(lock_type="agent", resource_id=agent_id):
        cursor = self.db.execute(
            """INSERT INTO agent_notebook 
               (agent_id, entry_type, title, content, source, 
                related_topics, relevance_score, status, expires_at,
                created_at, updated_at)
               VALUES (?, ?, ?, ?, ?, ?, ?, 'draft', ?, ?, ?)""",
            (agent_id, entry_type, title, content, source,
             topics_json, relevance_score, expires_at, now, now)
        )
        entry_id = cursor.lastrowid
    
    return {
        "success": True,
        "id": entry_id,
        "entry_type": entry_type,
        "title": title,
        "status": "draft",
    }
```

---

## 可能导致 500 错误的原因

### 🔴 问题 1: API 端点缺少异常处理

**位置**: `gateway/api/internal/runtime.py:829-847`

**问题**: `rt_notebook_write` 函数没有任何 try-except 块，任何未捕获的异常都会导致 FastAPI 返回 HTTP 500 错误。

**可能的异常来源**:

1. **`resolve_runtime_ids(runtime_id)`** (line 834)
   - ✅ 如果 runtime 不存在: 抛出 `HTTPException(404)` - 会被 FastAPI 正确处理
   - ❌ 如果数据库连接失败: 抛出 `RuntimeError` - **会导致 500**
   - ❌ 如果数据库查询异常: 抛出 `sqlite3.Error` - **会导致 500**

2. **`get_db()`** (line 836)
   - ❌ 如果 `NOVAIC_DATA_DIR` 环境变量未设置: 抛出 `RuntimeError` - **会导致 500**
   - ❌ 如果数据库文件不存在或无法访问: 抛出异常 - **会导致 500**

3. **`NotebookRepository.write()`** (line 838-847)
   - ❌ 如果 `agent_notebook` 表不存在: `sqlite3.OperationalError` - **会导致 500**
   - ❌ 如果字段类型不匹配: `sqlite3.InterfaceError` - **会导致 500**
   - ❌ 如果外键约束违反 (agent_id 不存在): `sqlite3.IntegrityError` - **会导致 500**
   - ❌ 如果 JSON 序列化失败: `TypeError` 或 `ValueError` - **会导致 500**
   - ❌ 如果数据库锁超时: `sqlite3.OperationalError` (busy timeout) - **会导致 500**

### 🔴 问题 2: 数据库事务异常处理

**位置**: `common/db/database.py:168-198`

```python
@contextmanager
def transaction(self, lock_type: str = "global", **lock_kwargs):
    # ...
    try:
        yield self
        conn.commit()
    except Exception:
        conn.rollback()
        raise  # ⚠️ 异常会被重新抛出
```

**问题**: 虽然事务会回滚，但异常会被重新抛出到调用者。如果调用者没有异常处理，就会导致 500 错误。

### 🔴 问题 3: 参数验证不足

**位置**: `gateway/api/internal/runtime.py:838-847`

**问题**: 
- `data.get("related_topics")` 可能返回 `None`，但代码假设它是列表或 `None`
- 如果 `related_topics` 不是列表类型，`json.dumps()` 可能失败
- `expires_at` 没有格式验证，如果格式错误可能导致数据库错误

---

## 最可能的原因

基于错误信息和代码分析，**最可能的原因是**:

### 1. **数据库表不存在或 schema 不匹配** (高概率)
   - `agent_notebook` 表可能未创建
   - 表结构可能与代码期望的不一致
   - 数据库迁移未执行

### 2. **agent_id 不存在导致外键约束违反** (中概率)
   - `resolve_runtime_ids()` 返回的 `agent_id` 在 `agents` 表中不存在
   - 外键约束 `FOREIGN KEY (agent_id) REFERENCES agents(id)` 被违反

### 3. **数据库连接或锁问题** (中概率)
   - 数据库文件被锁定
   - 连接池耗尽
   - 事务超时

### 4. **参数类型错误** (低概率)
   - `related_topics` 不是列表类型
   - `expires_at` 格式错误

---

## 建议的修复方案

### 方案 1: 添加异常处理和错误日志 (推荐)

**修改文件**: `novaic-backend/gateway/api/internal/runtime.py`

```python
@router.post("/rt/{runtime_id}/notebook/write")
def rt_notebook_write(runtime_id: str, data: Dict[str, Any]):
    """Write a new notebook entry. Agent ID resolved from runtime."""
    import logging
    from fastapi import HTTPException
    
    logger = logging.getLogger(__name__)
    
    try:
        from gateway.db.repositories.notebook import NotebookRepository
        
        _, agent_id, _ = resolve_runtime_ids(runtime_id)
        
        db = get_db()
        repo = NotebookRepository(db)
        
        # 参数验证
        related_topics = data.get("related_topics")
        if related_topics is not None and not isinstance(related_topics, list):
            raise HTTPException(
                status_code=400, 
                detail=f"related_topics must be a list, got {type(related_topics)}"
            )
        
        return repo.write(
            agent_id=agent_id,
            entry_type=data.get("entry_type", "observation"),
            title=data.get("title", "Untitled"),
            content=data.get("content", ""),
            source=f"runtime:{runtime_id}",
            related_topics=related_topics,
            relevance_score=data.get("relevance_score", 0.5),
            expires_at=data.get("expires_at"),
        )
    except HTTPException:
        raise  # 重新抛出 HTTP 异常
    except Exception as e:
        logger.error(
            f"[notebook_write] Failed to write notebook entry: runtime_id={runtime_id}, "
            f"error={type(e).__name__}: {str(e)}",
            exc_info=True
        )
        raise HTTPException(
            status_code=500,
            detail=f"Failed to write notebook entry: {str(e)}"
        )
```

### 方案 2: 在 Repository 层添加异常处理

**修改文件**: `novaic-backend/gateway/db/repositories/notebook.py`

```python
def write(
    self,
    agent_id: str,
    entry_type: str,
    title: str,
    content: str,
    source: Optional[str] = None,
    related_topics: Optional[List[str]] = None,
    relevance_score: float = 0.5,
    expires_at: Optional[str] = None,
) -> Dict[str, Any]:
    """Create a new notebook entry."""
    import logging
    logger = logging.getLogger(__name__)
    
    try:
        now = datetime.utcnow().isoformat()
        topics_json = json.dumps(related_topics or [], ensure_ascii=False)
        relevance_score = max(0.0, min(1.0, relevance_score))
        
        with self.db.transaction(lock_type="agent", resource_id=agent_id):
            cursor = self.db.execute(
                """INSERT INTO agent_notebook 
                   (agent_id, entry_type, title, content, source, 
                    related_topics, relevance_score, status, expires_at,
                    created_at, updated_at)
                   VALUES (?, ?, ?, ?, ?, ?, ?, 'draft', ?, ?, ?)""",
                (agent_id, entry_type, title, content, source,
                 topics_json, relevance_score, expires_at, now, now)
            )
            entry_id = cursor.lastrowid
        
        return {
            "success": True,
            "id": entry_id,
            "entry_type": entry_type,
            "title": title,
            "status": "draft",
        }
    except Exception as e:
        logger.error(
            f"[NotebookRepository.write] Failed: agent_id={agent_id}, "
            f"entry_type={entry_type}, error={type(e).__name__}: {str(e)}",
            exc_info=True
        )
        raise  # 重新抛出，让上层处理
```

### 方案 3: 验证数据库 schema

**检查步骤**:
1. 确认 `agent_notebook` 表存在
2. 确认表结构与 `schema.py` 中定义的一致
3. 确认数据库迁移已执行

```sql
-- 检查表是否存在
SELECT name FROM sqlite_master WHERE type='table' AND name='agent_notebook';

-- 检查表结构
PRAGMA table_info(agent_notebook);

-- 检查外键约束
PRAGMA foreign_key_list(agent_notebook);
```

---

## 调试建议

### 1. 查看 Gateway 日志
检查 Gateway 服务的日志文件，查找相关的错误堆栈信息：
```bash
# 查找错误日志
grep -i "notebook_write\|500\|Internal Server Error" <gateway_log_file>
```

### 2. 检查数据库状态
```python
# 在 Python 中检查
from gateway.db.access import get_db
db = get_db()

# 检查表是否存在
tables = db.fetchall("SELECT name FROM sqlite_master WHERE type='table'")
print([t['name'] for t in tables])

# 检查 agent_notebook 表结构
schema = db.fetchall("PRAGMA table_info(agent_notebook)")
print(schema)
```

### 3. 验证 Runtime 和 Agent
```python
from gateway.db.repositories import RuntimeRepository
from gateway.db.access import get_db

db = get_db()
runtime_repo = RuntimeRepository(db)
runtime = runtime_repo.get_by_id("rt-8b72a6172462")

if runtime:
    print(f"Runtime found: agent_id={runtime.agent_id}, subagent_id={runtime.subagent_id}")
else:
    print("Runtime not found!")
```

---

## 总结

**根本原因**: API 端点缺少异常处理，导致任何数据库或业务逻辑异常都会返回 HTTP 500 错误，且没有详细的错误信息。

**优先级修复**:
1. ✅ **高优先级**: 添加异常处理和日志记录
2. ✅ **中优先级**: 添加参数验证
3. ✅ **低优先级**: 在 Repository 层添加防御性检查

**预期效果**: 
- 错误会被正确捕获和记录
- 返回有意义的错误信息（400/404/500）
- 便于调试和问题定位
