# Case Study: "system" agent_id 导致的系统异常

## 背景

2026-02-02 调试过程中发现系统出现以下异常行为：
1. 消息没有被标记为已读
2. SubAgent 状态异常
3. 系统不断创建新的 Runtime

## 问题现象

### 现象 1：消息永远不被标记已读

```sql
-- 发送消息后检查
SELECT type, read, substr(content, 1, 30) FROM chat_messages;

-- 结果：read 始终为 0
type          read  content
------------  ----  ----------------
USER_MESSAGE  0     你好！
USER_MESSAGE  0     测试消息
```

### 现象 2：Runtime 不断被创建

```sql
SELECT runtime_id, status, created_at FROM agent_runtimes ORDER BY created_at DESC LIMIT 5;

-- 结果：每隔几秒就有新的 Runtime
runtime_id       status     created_at
---------------  ---------  -------------------
rt-abc123...     completed  2026-02-02 10:05:00
rt-def456...     completed  2026-02-02 10:04:55
rt-ghi789...     completed  2026-02-02 10:04:50
```

### 现象 3：SubAgent 快速切换状态

```
sleeping → awake → running → sleeping → awake → ...
```

## 根因分析

### 核心问题：agent_id 不一致

```
┌─────────────────────────────────────────────────────────────────┐
│  launcher_main.py (bootstrap)                                   │
│                                                                 │
│  create_task(                                                   │
│      task_type="launcher",                                      │
│      task_subtype="monitor_launcher",                           │
│      agent_id="system",  ← 问题根源！                            │
│      ...                                                        │
│  )                                                              │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼ 这个 "system" 被传递给后续所有任务
┌─────────────────────────────────────────────────────────────────┐
│  monitor_collector                                              │
│  runtime_launcher                                               │
│  runtime_collector                                              │
│  think_launcher  ← 使用 agent_id="system" 查询消息               │
│  ...                                                            │
└─────────────────────────────────────────────────────────────────┘
```

### 问题流程图

```
┌─────────────────────────────────────────────────────────────────────────────┐
│  Monitor (使用正确的 agent_id 查询)                                          │
├─────────────────────────────────────────────────────────────────────────────┤
│  SELECT * FROM chat_messages                                                │
│  WHERE agent_id = 'e17eb1c2-...' AND read = 0                              │
│                    ^^^^^^^^^^^^^^                                           │
│  结果: ✅ 找到 3 条未读消息                                                   │
└─────────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│  ThinkLauncher (使用 "system" agent_id 查询)                                 │
├─────────────────────────────────────────────────────────────────────────────┤
│  SELECT * FROM chat_messages                                                │
│  WHERE agent_id = 'system' AND read = 0                                    │
│                   ^^^^^^^^                                                  │
│  结果: ❌ 0 条消息 (没有 agent_id='system' 的消息)                            │
│                                                                             │
│  context = []  ← LLM 收到空消息列表                                          │
└─────────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│  ActionsCollector (使用 "system" 检查未读)                                   │
├─────────────────────────────────────────────────────────────────────────────┤
│  has_unread_messages("system") → False                                      │
│                                                                             │
│  判断: 没有工具结果 + 没有未读消息 → 结束循环，进入 summarize                   │
└─────────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│  结果                                                                        │
├─────────────────────────────────────────────────────────────────────────────┤
│  • 消息从未被标记已读 (因为查的是 agent_id='system')                          │
│  • SubAgent 被设为 sleeping                                                  │
│  • Monitor 再次发现未读消息                                                   │
│  • 循环重复...                                                               │
└─────────────────────────────────────────────────────────────────────────────┘
```

## 危险的 Fallback 模式

### 问题代码

```python
# 这种 fallback 会掩盖问题
actual_runtime_id = args.get("runtime_id") or runtime_id  # runtime_id 可能是 "system"
actual_agent_id = runtime.get("agent_id") or agent_id      # agent_id 可能是 "system"
```

### 为什么危险

1. **静默失败**: 代码不会报错，但使用了错误的值
2. **难以调试**: 系统"看起来正常"，但行为完全错误
3. **问题传播**: 一个错误的值会影响整个流程

### 正确做法

```python
# 严格检查，失败时立即报错
actual_runtime_id = args.get("runtime_id")
if not actual_runtime_id:
    raise ValueError(f"runtime_id not found in args: {args}")

actual_agent_id = runtime.get("agent_id")
if not actual_agent_id:
    raise ValueError(f"agent_id not found in Runtime {actual_runtime_id}")
```

## 修复方案

### 1. 移除所有 Fallback 逻辑

**修改的文件**:
- `services/launchers/think.py`
- `services/launchers/actions.py`
- `services/launchers/summarize.py`
- `services/launchers/runtime.py`
- `services/collectors/summarize.py`
- `services/collectors/actions.py`
- `services/collectors/think.py`
- `services/executors/think.py`
- `services/executors/tool_call.py`

### 2. 从 Runtime 获取真实 agent_id

```python
# 所有 Handler 都必须从 Runtime 对象获取真实的 agent_id
runtime = await self.client.get_runtime(actual_runtime_id)
if not runtime:
    raise ValueError(f"Runtime not found: {actual_runtime_id}")

actual_agent_id = runtime.get("agent_id")
if not actual_agent_id:
    raise ValueError(f"agent_id not found in Runtime")
```

### 3. 修复缺少 commit 的数据库操作

```python
# 修复前 (update 不生效)
await db.execute("UPDATE chat_messages SET read = 1 WHERE id IN (...)", ids)

# 修复后 (确保 commit)
async with db.get_connection() as conn:
    await conn.execute("UPDATE chat_messages SET read = 1 WHERE id IN (...)", ids)
    await conn.commit()
```

## 调试过程

### 1. 发现问题

```bash
# 发送消息
curl -X POST http://127.0.0.1:19999/api/chat -d '{"message": "hello"}'

# 检查消息状态
sqlite3 novaic.db "SELECT type, read FROM chat_messages"
# 发现 read 始终为 0
```

### 2. 跟踪任务流

```bash
# 检查 pipeline_tasks
sqlite3 novaic.db "SELECT task_subtype, status, args FROM pipeline_tasks ORDER BY created_at DESC LIMIT 10"

# 发现 think_launcher 的 args 中 agent_id 是 "system"
```

### 3. 添加调试日志

```python
# 在 ThinkLauncher 中添加
print(f"[DEBUG] task agent_id: {agent_id}")
print(f"[DEBUG] runtime agent_id: {runtime.get('agent_id')}")
print(f"[DEBUG] actual_agent_id: {actual_agent_id}")
```

### 4. 验证修复

```bash
# 重启服务后测试
curl -X POST http://127.0.0.1:19999/api/chat -d '{"message": "hello"}'

# 等待处理完成
sleep 20

# 检查结果
sqlite3 novaic.db "SELECT type, read FROM chat_messages"
# read = 1 ✅

sqlite3 novaic.db "SELECT status FROM subagents"
# status = sleeping ✅
```

## 经验教训

### 1. 不要使用 Fallback 掩盖问题

```python
# ❌ 错误: 静默使用默认值
value = args.get("key") or default

# ✅ 正确: 明确失败
value = args.get("key")
if not value:
    raise ValueError("key is required")
```

### 2. 数据一致性检查

```python
# 在关键路径添加断言
assert runtime.get("agent_id") != "system", "Invalid agent_id"
assert runtime.get("runtime_id") is not None, "runtime_id is required"
```

### 3. 数据库操作必须 commit

```python
# 所有 UPDATE/INSERT/DELETE 必须 commit
async with db.get_connection() as conn:
    await conn.execute(sql, params)
    await conn.commit()  # 别忘了！
```

### 4. 使用 SQL 快速诊断

```sql
-- 检查消息状态
SELECT type, read, agent_id FROM chat_messages ORDER BY timestamp DESC LIMIT 5;

-- 检查 SubAgent 状态
SELECT subagent_id, status FROM subagents;

-- 检查失败的任务
SELECT task_subtype, status, error FROM pipeline_tasks WHERE status = 'failed';

-- 检查任务参数
SELECT task_subtype, json_extract(args, '$.agent_id') as agent_id FROM pipeline_tasks;
```

## 相关文件

- `launcher_main.py` - bootstrap 任务创建
- `services/collector_worker.py` - 任务传递逻辑
- `services/launchers/*.py` - 各 Launcher 实现
- `services/collectors/*.py` - 各 Collector 实现
- `api/internal.py` - 内部 API (包含数据库操作)
