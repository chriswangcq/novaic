# Saga vs Task 心跳机制分析

## 🔍 核心问题

**Saga 需要心跳超时吗？还是只要 Task 就好了？**

---

## 📊 架构分析

### 执行层级

```
┌────────────────────────────────────────────────────┐
│  Saga Worker (编排器)                               │
│  - 认领 Saga                                        │
│  - 执行步骤（TASK, PARALLEL, DECISION, SAGA）       │
│  - 发布 Task                                        │
│  - ⏰ 等待 Task 完成（关键！）                       │
└────────────────────────────────────────────────────┘
                    ↓ publish Task
┌────────────────────────────────────────────────────┐
│  Task Worker (执行器)                               │
│  - 认领 Task                                        │
│  - 执行工具（shell_exec, mobile_tap, etc.）         │
│  - 返回结果                                         │
└────────────────────────────────────────────────────┘
```

---

## 🔑 关键代码：Saga 等待 Task

### `saga_worker_sync.py:475-508`

```python
def _wait_for_task(self, task_id: str, step_name: str) -> Dict[str, Any]:
    """等待任务完成（同步，带超时）"""
    start_time = time.time()
    
    while True:
        # 检查超时
        elapsed = time.time() - start_time
        if elapsed > self.step_timeout:  # 默认 1500 秒 (25 分钟)
            raise TimeoutError(...)
        
        # 查询任务状态
        task = self.task_client.get_task(task_id)
        
        if status == "done":
            return result
        elif status == "failed":
            return {"success": False, ...}
        
        # ⏰ 继续等待（每 0.1 秒轮询一次）
        time.sleep(0.1)
```

**关键事实：**
- ⏰ Saga Worker 在**同步轮询**等待 Task 完成
- ⏰ 等待时间可能长达 **25 分钟**（step_timeout）
- ⏰ 在等待期间，**Saga Worker 线程一直在运行**

---

## ❓ 两种超时的作用

### 1️⃣ Task 心跳超时 (120 秒)

**保护对象**: Task Worker 进程

**场景**:
```
Task Worker 执行工具时崩溃
  ↓
120 秒没心跳
  ↓
Health Worker 重置 Task → pending
  ↓
另一个 Task Worker 重新执行
```

**检测**: Task Worker 崩溃/卡死

---

### 2️⃣ Saga 心跳超时 (600 秒)

**保护对象**: Saga Worker 进程

**场景 A - Saga Worker 崩溃（等待 Task 时）**:
```
Saga Worker 发布 Task
  ↓
进入 _wait_for_task() 等待
  ↓
💥 Saga Worker 进程崩溃（网络/内存/bug）
  ↓
600 秒没心跳
  ↓
Health Worker 重置 Saga → pending
  ↓
另一个 Saga Worker 重新执行（从断点继续）
```

**场景 B - Saga Worker 卡死（轮询时）**:
```
Saga Worker 进入 _wait_for_task()
  ↓
💥 轮询逻辑卡死（数据库锁/死循环/bug）
  ↓
600 秒没心跳（心跳线程无法更新）
  ↓
Health Worker 重置 Saga → pending
  ↓
另一个 Saga Worker 重新执行
```

**检测**: Saga Worker 崩溃/卡死

---

## 🎯 结论

### ✅ Saga **必须**有心跳超时！

**理由 1: Saga Worker 长时间运行**
- Saga 会等待 Task 完成（最长 25 分钟）
- 这期间 Saga Worker 需要证明自己还活着

**理由 2: 双层防护**
```
Task Worker 崩溃 → Task 心跳超时 (120s) → Task 重试
Saga Worker 崩溃 → Saga 心跳超时 (600s) → Saga 重试
```

**理由 3: 断点恢复**
- Saga 可以从 `current_step` 继续
- 如果 Saga Worker 崩溃，必须有机制重新启动 Saga

---

## 🚨 如果只有 Task 心跳会怎样？

### ❌ 问题场景 1: Saga Worker 崩溃

```
1. Saga Worker 发布 Task A
2. Task A 成功完成（2 分钟）
3. Saga Worker 准备发布 Task B
4. 💥 Saga Worker 崩溃
5. Task B 永远不会被发布
6. Saga 卡在 step 2，没人检测
```

**结果**: Saga 永久卡住 ❌

---

### ❌ 问题场景 2: Saga 等待时崩溃

```
1. Saga Worker 发布 Task A
2. Saga Worker 进入 _wait_for_task()
3. 💥 Saga Worker 崩溃（等待时）
4. Task A 可能完成，也可能失败
5. 但 Saga 没人继续执行
```

**结果**: Saga 永久卡住，Task 结果丢失 ❌

---

### ✅ 有 Saga 心跳时

```
1. Saga Worker 崩溃
2. Health Worker 检测到 600 秒没心跳
3. 重置 Saga → pending
4. 新的 Saga Worker 认领
5. 从 current_step 继续（断点恢复）
```

**结果**: Saga 自动恢复 ✅

---

## 📈 完整心跳架构

```
┌─────────────────────────────────────────────┐
│  Layer 1: Saga 心跳（600s）                  │
│  - Saga Worker 每 10 秒发心跳                │
│  - Health Worker 检测 600 秒没心跳 → 重试    │
│  - 保护：Saga 编排逻辑                       │
└─────────────────────────────────────────────┘
                    ↓
┌─────────────────────────────────────────────┐
│  Layer 2: Task 心跳（120s）                  │
│  - Task Worker 每 10 秒发心跳                │
│  - Health Worker 检测 120 秒没心跳 → 重试    │
│  - 保护：Task 工具执行                       │
└─────────────────────────────────────────────┘
                    ↓
┌─────────────────────────────────────────────┐
│  Layer 3: HTTP 传输（无超时）                │
│  - Tools Server → Gateway/Mobile/etc.        │
│  - 只要 Task Worker 发心跳，工具可无限执行   │
└─────────────────────────────────────────────┘
```

---

## 🎓 总结

| 特性 | Task 心跳 | Saga 心跳 |
|------|----------|----------|
| **保护对象** | Task Worker 进程 | Saga Worker 进程 |
| **超时时间** | 120 秒 | 600 秒 |
| **检测问题** | 工具执行崩溃/卡死 | 编排逻辑崩溃/卡死 |
| **恢复机制** | 重新执行 Task | 从断点继续 Saga |
| **是否必需** | ✅ 必需 | ✅ 必需 |

**不能只有 Task 心跳，因为：**
1. Saga Worker 运行时间可能远超 Task（等待多个 Task）
2. Saga Worker 崩溃时，Task 可能完成了但 Saga 没继续
3. 需要双层防护：Worker 层（Saga/Task）+ 传输层（HTTP）

**现有设计是正确的！** ✅

---

*最后更新: 2026-02-15*
