# Queue Service v2.0 架构迁移状态报告

**日期：** 2026-02-04  
**状态：** ⚠️ **进行中 - Gateway 启动失败**

---

## 📊 迁移进度

### ✅ 已完成的工作

1. **✅ Queue Service 创建和启动**
   - Queue Service 可以成功启动（端口 19997）
   - queue.db 数据库已创建
   - API 端点正常工作

2. **✅ 清理 Gateway 中的队列代码**
   - ✅ 删除 `gateway/task_queue/` 目录
   - ✅ 从 `gateway/db/schema.py` 删除 `tq_tasks` 和 `tq_sagas` 表定义
   - ✅ 修改 `gateway/api/internal.py` - 改用 HTTP 调用 Queue Service (2处)
   - ✅ 修改 `gateway/api/routes.py` - `/interrupt` 改用 HTTP 调用
   - ✅ 修复所有 `gateway.db.database` 导入改为 `common.db.database` (8个文件)
   - ✅ 复制 `exceptions.py` 到 `task_queue/` 目录

3. **✅ 修复 AI 回复 Bug**
   - ✅ 修复 `task_queue/sagas/message_process.py` 中的 `decide_action` 路径错误

4. **✅ 数据清理**
   - ✅ 删除旧的 queue.db
   - ✅ 从 novaic.db 删除 tq_tasks 和 tq_sagas 表

### ❌ 当前阻塞问题

#### 问题：Gateway 启动失败

**错误：**
```python
File "/Users/wangchaoqun/novaic/novaic-backend/main_gateway.py", line 363, in lifespan
    task_queue = await init_task_queue(db)
                       ~~~~~~~~~~~~~~~^^^^
TypeError: 'NoneType' object is not callable
```

**根本原因：**
- `main_gateway.py` 仍然尝试初始化本地的 TaskQueue 和 SagaOrchestrator
- 在 v2.0 架构中，这些应该由 Queue Service 管理
- Gateway 不应该再直接操作队列

**影响：** 🔴 **阻塞** - Gateway 无法启动，整个系统无法运行

---

## 🏗️ 架构设计

### 目标架构 (v2.0)

```
┌─────────────────┐         ┌──────────────────┐
│  Gateway        │         │  Queue Service   │
│  (19999)        │         │  (19997)         │
│                 │         │                  │
│  • 业务逻辑     │─HTTP──▶ │  • TaskQueue     │
│  • Agent管理    │         │  • SagaRepo      │
│  • Runtime管理  │         │  • FIFO Lock     │
│                 │         │                  │
│  novaic.db      │         │  queue.db        │
└─────────────────┘         └────────┬─────────┘
                                     │ HTTP
                                ┌────┴────┐
                                │ Workers │
                                └─────────┘
```

### 当前问题

`main_gateway.py` 的 `lifespan` 函数中还有：

```python
# Line 349-364
from task_queue import (
    init_task_queue, 
    init_saga_orchestrator,
    ...
)

task_queue = await init_task_queue(db)  # ❌ 应该删除
saga_orchestrator = await init_saga_orchestrator(db)  # ❌ 应该删除
```

这些初始化在 v2.0 中应该：
- 不再由 Gateway 执行
- Queue Service 独立管理队列和 Saga
- Gateway 通过 HTTP API 与 Queue Service 交互

---

## 🔧 需要的修复

### 修复方案选项

#### 方案 A：完全移除 Gateway 中的队列初始化（推荐）

1. 修改 `main_gateway.py` 的 `lifespan` 函数
2. 移除 `init_task_queue` 和 `init_saga_orchestrator` 调用
3. 移除相关的路由挂载（如果有）
4. 保留业务逻辑路由

**优点：**
- 符合 v2.0 架构设计
- 完全解耦

**缺点：**
- 需要仔细检查所有依赖
- 可能影响其他功能

#### 方案 B：让初始化函数返回空实现

1. 修改 `task_queue/__init__.py` 中的 `init_task_queue`
2. 返回一个空的 Mock 对象而不是 None
3. 保持接口兼容

**优点：**
- 最小改动
- 快速修复

**缺点：**
- 不彻底，留下技术债务

### 推荐步骤

1. **检查依赖**
   ```bash
   cd /Users/wangchaoqun/novaic/novaic-backend
   grep -r "get_task_queue\|get_saga_orchestrator" gateway/
   ```

2. **修改 main_gateway.py**
   - 注释或删除队列初始化代码
   - 保留必要的业务逻辑路由

3. **测试启动**
   ```bash
   export NOVAIC_DATA_DIR=~/.novaic
   venv/bin/python3 main_gateway.py
   ```

4. **验证完整架构**
   ```bash
   # Gateway 健康检查
   curl http://127.0.0.1:19999/api/health
   
   # Queue Service 健康检查
   curl http://127.0.0.1:19997/health
   
   # 验证队列数据在 queue.db
   sqlite3 ~/.novaic/queue.db "SELECT COUNT(*) FROM tq_tasks;"
   
   # 验证 novaic.db 没有队列表
   sqlite3 ~/.novaic/novaic.db ".tables" | grep tq
   ```

---

## 📋 修复清单

### 已修复 ✅

- [x] 删除 `gateway/task_queue/` 目录
- [x] 清理 `gateway/db/schema.py` 队列表定义
- [x] 修改 `gateway/api/internal.py` 使用 HTTP 调用
- [x] 修改 `gateway/api/routes.py` 使用 HTTP 调用
- [x] 修复所有 `gateway.db.database` 导入
- [x] 复制 `exceptions.py` 到 `task_queue/`
- [x] 修复 `decide_action` bug

### 待修复 ❌

- [ ] **修改 `main_gateway.py` - 移除队列初始化** 🔴 **阻塞**
- [ ] 验证 Gateway 启动成功
- [ ] 验证完整测试链路
- [ ] 更新文档

---

## 🧪 测试计划

修复完成后，执行以下测试：

### 1. 服务启动测试
```bash
cd /Users/wangchaoqun/novaic/novaic-backend
./stop_all_services.sh
rm -f ~/.novaic/queue.db
./start_all_services.sh

# 验证所有服务运行
ps aux | grep "python.*main" | grep -v grep
```

### 2. 架构验证
```bash
# 队列数据应该在 queue.db
sqlite3 ~/.novaic/queue.db ".tables"  # 应该有 tq_tasks, tq_sagas

# novaic.db 不应该有队列表
sqlite3 ~/.novaic/novaic.db ".tables" | grep tq  # 应该为空
```

### 3. 消息流程测试
```bash
# 发送测试消息
curl -s -X POST http://127.0.0.1:19999/api/chat/send \
  -H "Content-Type: application/json" \
  -d '{"message": "测试：请回复收到"}'

# 等待处理
sleep 15

# 验证 AI 回复
sqlite3 ~/.novaic/novaic.db "
  SELECT type, content 
  FROM chat_messages 
  ORDER BY timestamp DESC 
  LIMIT 2;
"

# 验证队列任务在 queue.db
sqlite3 ~/.novaic/queue.db "
  SELECT topic, status, COUNT(*) 
  FROM tq_tasks 
  GROUP BY topic, status;
"
```

---

## 📝 文件修改记录

| 文件 | 修改类型 | 状态 |
|------|---------|------|
| `gateway/task_queue/` | 删除目录 | ✅ |
| `gateway/db/schema.py` | 删除队列表定义 | ✅ |
| `gateway/api/internal.py` | 改用 HTTP 调用（2处） | ✅ |
| `gateway/api/routes.py` | 改用 HTTP 调用（1处） | ✅ |
| `gateway/config/manager_db.py` | 修改导入 | ✅ |
| `gateway/config/agents_db.py` | 修改导入 | ✅ |
| `gateway/db/repositories/*.py` | 修改导入（5个文件） | ✅ |
| `task_queue/exceptions.py` | 复制文件 | ✅ |
| `task_queue/sagas/message_process.py` | 修复 bug | ✅ |
| **`main_gateway.py`** | **移除队列初始化** | ❌ **待修复** |

---

## 🎯 下一步行动

1. **立即处理：** 修改 `main_gateway.py` 移除队列初始化
2. **验证启动：** 确保 Gateway 可以成功启动
3. **完整测试：** 执行冒烟测试验证完整链路
4. **更新文档：** 更新 SMOKE_TEST_REPORT.md

---

**负责人：** AI Assistant  
**更新时间：** 2026-02-04 18:15  
**预计完成：** 需要人工决策修复方案
