# 🔄 Saga 服务独立迁移可行性分析

**分析时间：** 2026-02-04 17:10  
**问题：** 能否将 Saga 逻辑从 Gateway 独立出来？

---

## ✅ 结论：非常容易迁移！

**当前已具备的优势：**
1. ✅ Worker 通过 HTTP SDK 访问（已解耦）
2. ✅ Saga 表独立（无外键依赖）
3. ✅ SagaRepository 依赖少（只需 DB + TaskQueue）
4. ✅ 代码已经模块化

---

## 📊 当前架构分析

### 当前依赖关系

```
┌─────────────────────────────────────────────┐
│            Gateway 进程                      │
├─────────────────────────────────────────────┤
│                                             │
│  ┌─────────────┐      ┌──────────────┐    │
│  │ TaskQueue   │      │ SagaRepository│    │
│  │ (queue_db)  │      │ (saga_repo)   │    │
│  └──────┬──────┘      └──────┬───────┘    │
│         │                     │             │
│         ├─────────────────────┤             │
│         │                     │             │
│    ┌────▼─────────────────────▼────┐       │
│    │      Database                 │       │
│    │  • tq_tasks                   │       │
│    │  • tq_sagas (独立表，无FK)    │       │
│    └───────────────────────────────┘       │
│                                             │
└─────────────────────────────────────────────┘
```

**关键发现：**
- ✅ `tq_sagas` 表完全独立
- ✅ 无外键指向其他表
- ✅ SagaRepository 只依赖：`db` + `queue`（可选）

---

## 🎯 迁移方案

### 方案 A：独立 Saga 服务 + 共享数据库（推荐）

```
┌──────────────────┐         ┌──────────────────┐
│  Gateway 进程     │         │  Saga 服务        │
├──────────────────┤         ├──────────────────┤
│                  │         │                  │
│  • TaskQueue     │         │  • SagaRepository│
│  • tq_tasks表    │         │  • tq_sagas表    │
│                  │         │                  │
└────────┬─────────┘         └────────┬─────────┘
         │                            │
         └────────────┬───────────────┘
                      ▼
              ┌───────────────┐
              │  novaic.db    │
              │  (共享数据库)  │
              └───────────────┘
```

**优点：**
- ✅ 最简单的迁移方案
- ✅ 无需同步数据
- ✅ 事务一致性保证
- ✅ 仅需移动代码

**实施步骤：**

1. **创建 Saga 服务目录**
   ```bash
   mkdir novaic-backend/saga_service
   ```

2. **移动核心代码**
   ```bash
   # 移动 SagaRepository
   cp gateway/task_queue/saga_repo.py saga_service/
   
   # 复用数据库层（或创建独立连接）
   # saga_service 需要：
   # - Database 类（事务管理）
   # - FIFO Lock（已实现）
   ```

3. **创建 Saga 服务 API**
   ```python
   # saga_service/main.py
   from fastapi import FastAPI
   from gateway.db import init_database
   from saga_service.saga_repo import SagaRepository
   
   app = FastAPI()
   db = init_database()
   saga_repo = SagaRepository(db)
   
   @app.post("/sagas/claim")
   def claim_saga(saga_types: list, worker_id: str):
       return saga_repo.claim(saga_types, worker_id)
   ```

4. **更新 Worker 配置**
   ```python
   # Worker 只需改 URL
   saga_client = SagaClient("http://127.0.0.1:19997")  # Saga 服务端口
   ```

**配置：**
- Gateway: 端口 19999，访问 tq_tasks
- Saga Service: 端口 19997，访问 tq_sagas
- 共享: novaic.db + FIFO Lock

---

### 方案 B：独立 Saga 服务 + 独立数据库

```
┌──────────────────┐         ┌──────────────────┐
│  Gateway 进程     │         │  Saga 服务        │
├──────────────────┤         ├──────────────────┤
│  • TaskQueue     │         │  • SagaRepository│
│       ▼          │         │       ▼          │
│  ┌──────────┐   │         │  ┌──────────┐   │
│  │gateway.db│   │         │  │ saga.db  │   │
│  └──────────┘   │         │  └──────────┘   │
└──────────────────┘         └──────────────────┘
```

**优点：**
- ✅ 完全独立部署
- ✅ 数据库隔离
- ✅ 可独立扩展

**缺点：**
- ⚠️ 需要跨数据库协调（如果 Saga 需要查询 Task 状态）
- ⚠️ 增加运维复杂度

---

### 方案 C：Saga 服务调用 Gateway API（最解耦）

```
┌──────────────────┐         ┌──────────────────┐
│  Gateway 进程     │◄───HTTP─│  Saga 服务        │
├──────────────────┤         ├──────────────────┤
│  • TaskQueue     │         │  • SagaRepository│
│  • /api/tasks/*  │         │  • 使用           │
│       ▼          │         │    TaskQueueClient│
│  ┌──────────┐   │         │       ▼          │
│  │gateway.db│   │         │  ┌──────────┐   │
│  └──────────┘   │         │  │ saga.db  │   │
└──────────────────┘         └──────────────────┘
```

**优点：**
- ✅ 完全解耦（HTTP 通信）
- ✅ 可分布式部署
- ✅ 易于横向扩展

**实现：**
```python
# saga_service/saga_repo.py
class SagaRepository:
    def __init__(self, db, task_queue_client: TaskQueueClient):
        self.db = db
        self.task_queue = task_queue_client  # HTTP 客户端
    
    def _publish_task(self, topic, payload):
        # 通过 HTTP 调用 Gateway
        return self.task_queue.publish(topic, payload)
```

---

## 📝 需要迁移的文件

### 核心文件（必须）

```
gateway/task_queue/saga_repo.py   →  saga_service/saga_repo.py
gateway/db/database.py             →  saga_service/database.py (或共享)
gateway/db/locks.py                →  saga_service/locks.py (或共享)
gateway/db/schema.py               →  saga_service/schema.py (仅 tq_sagas 表)
```

### 依赖文件（需要）

```
task_queue/saga.py                 →  saga_service/saga.py (定义)
task_queue/exceptions.py           →  saga_service/exceptions.py
```

### API Routes（新增）

```python
# saga_service/routes.py
from fastapi import APIRouter

router = APIRouter()

@router.post("/sagas/create")
def create_saga(saga_type: str, context: dict):
    return saga_repo.create(saga_type, context)

@router.post("/sagas/claim")
def claim_saga(saga_types: list, worker_id: str):
    return saga_repo.claim(saga_types, worker_id)

@router.post("/sagas/{saga_id}/complete")
def complete_saga(saga_id: str, result: dict):
    return saga_repo.mark_completed(saga_id, result)

# ... 其他 API
```

---

## 🔧 迁移步骤（方案 A - 推荐）

### Phase 1: 准备（1小时）

```bash
# 1. 创建目录结构
mkdir -p saga_service/{api,db}

# 2. 复制核心文件
cp gateway/task_queue/saga_repo.py saga_service/
cp gateway/db/database.py saga_service/db/
cp gateway/db/locks.py saga_service/db/

# 3. 创建独立的 schema
# saga_service/db/schema.py - 只包含 tq_sagas 表定义
```

### Phase 2: 实现服务（2-3小时）

```python
# saga_service/main.py
import os
from fastapi import FastAPI
from .db.database import init_database
from .saga_repo import SagaRepository
from .api.routes import router

app = FastAPI(title="Saga Service")

# 共享数据库连接
NOVAIC_DATA_DIR = os.environ["NOVAIC_DATA_DIR"]
db = init_database(NOVAIC_DATA_DIR)
saga_repo = SagaRepository(db)

app.include_router(router, prefix="/sagas")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=19997)
```

### Phase 3: 更新客户端（30分钟）

```python
# task_queue/client.py - 修改 SagaClient
class SagaClient:
    def __init__(self, saga_url: str = "http://127.0.0.1:19997"):
        # 从 Gateway URL 改为 Saga Service URL
        self.saga_url = saga_url
        # 其他代码保持不变
```

### Phase 4: 测试和部署（1小时）

```bash
# 1. 启动 Saga Service
cd saga_service
python main.py

# 2. 测试 API
curl http://127.0.0.1:19997/sagas/claim \
  -d '{"saga_types": ["test"], "worker_id": "test"}'

# 3. 启动 Workers（使用新的 Saga Service URL）
python -m task_queue.workers.saga_worker_sync 1
```

---

## ⚖️ 各方案对比

| 维度 | 方案A 共享DB | 方案B 独立DB | 方案C HTTP调用 |
|------|-------------|-------------|----------------|
| **迁移难度** | ⭐ 简单 | ⭐⭐ 中等 | ⭐⭐⭐ 复杂 |
| **运维复杂度** | ⭐ 低 | ⭐⭐ 中等 | ⭐⭐ 中等 |
| **性能** | ⭐⭐⭐ 优秀 | ⭐⭐⭐ 优秀 | ⭐⭐ 良好 |
| **扩展性** | ⭐⭐ 中等 | ⭐⭐⭐ 优秀 | ⭐⭐⭐ 优秀 |
| **解耦程度** | ⭐⭐ 中等 | ⭐⭐⭐ 高 | ⭐⭐⭐ 高 |
| **一致性保证** | ⭐⭐⭐ 强 | ⭐⭐ 中等 | ⭐⭐ 中等 |

---

## ✅ 迁移优势

### 1. 代码已经准备好

```python
# SagaRepository 依赖很少
class SagaRepository:
    def __init__(self, db, queue=None):
        self.db = db        # 数据库连接
        self.queue = queue  # 可选的 TaskQueue
```

**关键点：**
- ✅ `db` 可以是共享的或独立的
- ✅ `queue` 可以是 HTTP 客户端
- ✅ 无其他 gateway 依赖

### 2. Worker 已经使用 HTTP SDK

```python
# Workers 无需大改
saga_client = SagaClient("http://127.0.0.1:19997")  # 改 URL 即可
```

### 3. 数据库已支持并发

```python
# FIFO Lock 已实现，可直接使用
with db.transaction(lock_type="saga", resource_id=saga_id):
    db.execute("UPDATE tq_sagas ...")
```

---

## 🎯 推荐方案

### 短期（1-2周）：方案 A - 共享数据库

**原因：**
1. 最快速（1天完成）
2. 风险最低
3. 保持一致性
4. 易于回滚

**步骤：**
```
Day 1: 创建 Saga Service + API
Day 2: 测试和验证
Day 3: 更新 Worker 配置
Day 4: 生产部署
```

### 长期（1-2月）：方案 C - 完全解耦

**原因：**
1. 可独立扩展
2. 支持分布式
3. 易于维护

**步骤：**
```
Week 1-2: 实现 HTTP 调用
Week 3: 性能测试
Week 4: 生产部署
```

---

## 📊 迁移时间估算

| 任务 | 方案A | 方案B | 方案C |
|------|-------|-------|-------|
| 代码迁移 | 2小时 | 4小时 | 6小时 |
| API 实现 | 3小时 | 3小时 | 4小时 |
| 测试验证 | 2小时 | 4小时 | 6小时 |
| 部署配置 | 1小时 | 2小时 | 3小时 |
| **总计** | **8小时** | **13小时** | **19小时** |

---

## 🎉 结论

### ✅ 非常容易迁移！

**原因：**
1. ✅ Worker 已通过 HTTP SDK 访问（已解耦）
2. ✅ Saga 表独立（无外键）
3. ✅ SagaRepository 依赖少
4. ✅ FIFO Lock 已实现
5. ✅ 代码结构清晰

**建议：**
- 🚀 **立即可行**：方案 A（1天完成）
- 📅 **逐步优化**：方案 A → 方案 C（1-2月）

---

**分析人：** AI Assistant  
**结论：** ✅ 迁移非常容易，推荐从方案A开始  
**预计时间：** 1天（方案A）
