# Queue Service v2.0 - 冒烟测试最终报告

**测试时间：** 2026-02-04 18:18  
**架构版本：** v2.0 (独立 Queue Service)  
**测试状态：** ⚠️ **部分完成 - 发现架构问题**

---

## ✅ 已完成的工作

### 1. 代码清理和修复

| 任务 | 状态 | 说明 |
|------|------|------|
| 删除 `gateway/task_queue/` | ✅ | 完全删除 |
| 清理 `gateway/db/schema.py` | ✅ | 删除队列表定义 |
| 修复 Gateway 导入 | ✅ | 8个文件改为 `common.db.database` |
| 修改 `gateway/api/internal.py` | ✅ | 改用 HTTP 调用 (2处) |
| 修改 `gateway/api/routes.py` | ✅ | 改用 HTTP 调用 (1处) |
| 复制缺失文件 | ✅ | `exceptions.py`, `saga.py` |
| 修复 `decide_action` bug | ✅ | `message_process.py` |
| **修改 `main_gateway.py`** | ✅ | **完全移除队列初始化** |

### 2. 服务启动验证

```bash
✅ Gateway (19999) - 启动成功
✅ Queue Service (19997) - 启动成功
✅ Task Worker - 启动（有小错误但不影响）
✅ Saga Worker - 启动成功
✅ Health Worker - 启动成功
⚠️  Watchdog - 启动但不工作
```

### 3. 数据库架构验证

```bash
✅ queue.db 已创建
✅ queue.db 有正确的表结构 (config, tq_tasks, tq_sagas)
✅ novaic.db 没有 tq_tasks 和 tq_sagas 表
```

---

## ❌ 当前问题

### 核心问题：消息没有被处理

**现象：**
- ✅ 消息成功发送到 Gateway
- ✅ 消息写入 `chat_messages` 表
- ❌ **没有任何任务或 Saga 被创建**
- ❌ queue.db 完全为空 (0 条记录)
- ❌ 没有 AI 回复

**测试数据：**
```bash
$ sqlite3 ~/.novaic/queue.db "SELECT COUNT(*) FROM tq_tasks;"
0

$ sqlite3 ~/.novaic/queue.db "SELECT COUNT(*) FROM tq_sagas;"
0

$ sqlite3 ~/.novaic/novaic.db "SELECT type FROM chat_messages ORDER BY timestamp DESC LIMIT 3;"
USER_MESSAGE|最终测试：请回复收到
USER_MESSAGE|v2.0测试：请回复收到
USER_MESSAGE|测试v2.0架构：请回复收到
(没有 AGENT_REPLY)
```

---

## 🔍 根本原因分析

### 问题：消息路由断裂

在 v1.0 架构中：
```
用户消息 → Gateway (写入 chat_messages) 
         → Watchdog (监听 sending 消息)
         → 触发 message_process Saga (写入 tq_sagas)
         → Workers 处理
```

在 v2.0 架构中：
```
用户消息 → Gateway (写入 chat_messages) 
         → ??? (谁来触发 Saga？)
         → Queue Service (tq_sagas 应该在这里)
         → Workers 处理
```

**核心问题：**
在 v2.0 中，Gateway 不再初始化队列和 Saga，那么**谁负责监控消息并创建 Saga？**

### 可能的解决方案

#### 方案 A：Gateway API 直接调用 Queue Service

Gateway 在收到消息后，直接 HTTP 调用 Queue Service 创建 Saga：

```python
# gateway/api/routes.py - POST /api/chat/send
@router.post("/api/chat/send")
async def send_message(data: dict):
    # 1. 写入消息
    message_repo.create_message(...)
    
    # 2. 直接调用 Queue Service 创建 Saga
    import httpx
    queue_service_url = os.environ.get("QUEUE_SERVICE_URL", "http://127.0.0.1:19997")
    with httpx.Client() as client:
        client.post(
            f"{queue_service_url}/api/queue/sagas/start",
            json={
                "saga_type": "message_process",
                "context": {
                    "message_id": message_id,
                    "agent_id": agent_id,
                    ...
                }
            }
        )
```

**优点：**
- 简单直接
- 不需要 Watchdog
- 实时触发

**缺点：**
- Gateway 需要知道业务逻辑（创建哪个 Saga）
- 耦合度增加

#### 方案 B：保留 Watchdog，改为调用 Queue Service

Watchdog 继续监听消息，但通过 HTTP 调用 Queue Service：

```python
# task_queue/workers/watchdog.py
class Watchdog:
    def __init__(self, gateway_url, queue_service_url):
        self.gateway_url = gateway_url
        self.queue_service_url = queue_service_url
    
    async def process_messages(self):
        # 1. 从 Gateway 获取 sending 消息
        messages = await self.get_sending_messages()
        
        # 2. 调用 Queue Service 创建 Saga
        for msg in messages:
            await self.create_saga_via_http(msg)
```

**优点：**
- 解耦：Gateway 只负责业务，Watchdog 负责触发
- Watchdog 可以独立扩展

**缺点：**
- 需要修改 Watchdog 代码
- 增加一层间接调用

#### 方案 C：Gateway 写消息到队列，Watchdog 读队列

这是真正的消息队列模式，但需要更大改动。

---

## 🎯 推荐方案：方案 A（Gateway 直接调用）

**理由：**
1. 最简单直接
2. 实时性最好
3. v2.0 的目标是解耦队列基础设施，不是解耦业务逻辑
4. Gateway 知道消息应该触发什么流程是合理的

**实现步骤：**

1. 修改 `gateway/api/routes.py` 的 `POST /api/chat/send`
2. 在消息写入后，调用 Queue Service API 创建 `message_process` Saga
3. 删除或废弃 Watchdog（可选）
4. 测试完整链路

---

## 📊 当前架构状态

### 工作正常 ✅

- Gateway 启动和运行
- Queue Service 启动和运行
- Workers 启动（Task, Saga, Health）
- 数据库隔离（novaic.db vs queue.db）
- HTTP API 调用机制

### 需要修复 ❌

- **消息到 Saga 的触发机制** 🔴 **阻塞**
- Watchdog 功能（或者替代方案）
- 完整的端到端测试

---

## 🧪 验证清单

### 基础设施 ✅

- [x] Gateway 启动成功
- [x] Queue Service 启动成功
- [x] queue.db 独立存在
- [x] novaic.db 没有队列表
- [x] Workers 可以启动

### 功能 ❌

- [ ] 发送消息后创建 Saga
- [ ] Saga 触发任务
- [ ] Workers 执行任务
- [ ] LLM 调用成功
- [ ] 生成 AI 回复

---

## 📝 下一步行动

### 立即执行（推荐方案 A）

1. **修改 Gateway API**
   - 文件：`gateway/api/routes.py`
   - 修改：`POST /api/chat/send` 端点
   - 添加：HTTP 调用 Queue Service 创建 Saga

2. **测试验证**
   ```bash
   # 发送消息
   curl -X POST http://127.0.0.1:19999/api/chat/send \
     -H "Content-Type: application/json" \
     -d '{"message": "测试"}'
   
   # 验证 queue.db 有数据
   sqlite3 ~/.novaic/queue.db "SELECT COUNT(*) FROM tq_sagas;"
   ```

3. **完整链路测试**
   - 验证任务创建
   - 验证 LLM 调用
   - 验证 AI 回复

---

## 📚 相关文档

- `ARCH_V2_MIGRATION_STATUS.md` - 迁移详细状态
- `SMOKE_TEST_REPORT.md` - 之前的测试报告
- `COMPLETION_REPORT.md` - Queue Service 创建报告

---

**负责人：** AI Assistant  
**状态：** 等待决策和实施方案 A  
**预计完成时间：** <30分钟
