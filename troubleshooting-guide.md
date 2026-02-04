# Worker 故障排查指南

## 🔧 排查工具

我创建了三个工具来排查和验证 Worker 卡住的问题：

### 1. 诊断工具 - `diagnose_workers.py`

**用途**: 一键检查系统健康状态

**使用方法**:
```bash
cd /Users/wangchaoqun/novaic
python diagnose_workers.py
```

**检查内容**:
- ✅ Worker 进程状态（CPU、内存、运行时间）
- ✅ 卡住的 Task（心跳超过 60 秒）
- ✅ 卡住的 Saga（心跳超过 60 秒）
- ✅ 最近活动情况（是否有任务完成）
- ✅ 自动分析并给出建议

**输出示例**:
```
================================================================================
🔍 Worker 健康诊断
================================================================================

📊 进程状态
✅ Task Worker: 1 个进程
   PID 79233: CPU 0.6%, Memory 55.0MB, Uptime 9.0min

✅ Saga Worker: 3 个进程
   PID 68993: CPU 0.6%, Memory 65.4MB, Uptime 55.4min
   ...

📋 卡住的 Task (心跳 > 60s)
❌ 发现 8 个卡住的 task

Worker: task-85ea9d94 (8 个 task 卡住)
  • task-0c5210bb9bd2 (message.route)
    心跳超时: 188s
    ...

🎯 诊断结论
⚠️  Worker task-85ea9d94 有 8 个 task 卡住（可能进程有问题）

💡 建议操作：
1. 清理卡住的 task 和 saga
2. 重启有问题的 Worker
```

### 2. 清理工具 - `cleanup_stuck.py`

**用途**: 自动清理心跳超时的 Task 和 Saga

**使用方法**:

```bash
# 1. 先试运行，看看有多少卡住的任务（不会实际清理）
python cleanup_stuck.py --dry-run

# 2. 确认后执行清理
python cleanup_stuck.py --execute
```

**功能**:
- 自动查找心跳超时的 Task（> 60s）
- 自动查找心跳超时的 Saga（> 60s）
- 将它们标记为 `failed` 状态
- 按 Worker 分组显示

**输出示例**:
```
🧹 清理卡住的 Task 和 Saga
================================================================================

🔍 发现 8 个卡住的 task:
  • task-0c5210bb9bd2 (message.route) - 心跳超时 188s - Worker: task-85ea9d94
  ...

✅ 已清理 8 个 task

🔍 发现 3 个卡住的 saga:
  • saga-fdec74ef26f1 (message_process) - 步骤 0 - 心跳超时 165s
  ...

✅ 已清理 3 个 saga
```

### 3. 实时监控 - `monitor_workers.py`

**用途**: 持续监控 Worker 状态，实时发现问题

**使用方法**:
```bash
python monitor_workers.py
```

**监控内容**:
- 📋 Task/Saga 队列状态（每 5 秒刷新）
- ⏱️  最近活动情况
- ⚠️  卡住的任务数量
- 🚨 自动告警（堆积、卡住、无活动等）

**界面示例**:
```
================================================================================
⏱️  Worker 实时监控 - 2026-02-04 12:55:46
================================================================================

📋 Task 队列 (最近 10 分钟):
  Pending:   12  Claimed:    3  Done:  156  Failed:    2

📊 Saga 队列 (最近 10 分钟):
  Pending:    5  Running:    2  Completed:   89  Failed:    1

⏱️  最近活动 (1 分钟内):
  Task 完成: 23 个
  Saga 完成: 12 个

⚠️  卡住的任务 (心跳 > 60s):
  Task: 0
  Saga: 0

✅ 系统运行正常

按 Ctrl+C 停止监控
```

---

## 🔍 排查流程

### 场景 1: 发现系统变慢或卡住

```bash
# 第 1 步：运行诊断工具
python diagnose_workers.py

# 如果发现卡住的任务：
# 第 2 步：清理卡住的任务
python cleanup_stuck.py --execute

# 第 3 步：重启有问题的 Worker
# （根据诊断工具的建议）
pkill -f main_task && python main_task.py &
```

### 场景 2: 验证 Worker 进程是否有问题

运行诊断工具后，重点关注：

#### 🔴 Worker 进程有问题的迹象：
1. **同一个 Worker 有多个（≥5）卡住的任务**
   ```
   Worker: task-85ea9d94 (8 个 task 卡住)  ← 这个 Worker 有问题！
   ```

2. **CPU 或内存异常**
   ```
   PID 79233: CPU 95.0%, Memory 1200MB  ← CPU 过高！
   ```

3. **最近无活动**
   ```
   最近 5 分钟没有 task 完成（系统可能停滞）
   ```

#### ✅ 正常情况：
```
Worker: task-abc123 (1 个 task 卡住)  ← 偶尔有个别任务超时，正常
Worker: task-def456 (1 个 task 卡住)
```

### 场景 3: 持续监控生产环境

```bash
# 在后台启动监控
nohup python monitor_workers.py > /tmp/worker_monitor.log 2>&1 &

# 或者在 screen/tmux 中运行
screen -S worker-monitor
python monitor_workers.py
# Ctrl+A, D 离开 screen
```

---

## 📊 如何验证 "Worker 进程卡住" 假设？

### 方法 1: 看卡住任务的分布

```bash
python diagnose_workers.py
```

**关键指标**:
- 如果 8 个卡住的 task 都属于**同一个 Worker**
  → 证明是 Worker 进程问题 ✅
  
- 如果 8 个卡住的 task 属于**不同的 Worker**
  → 可能是其他问题（如数据库、Gateway）

**示例**:
```
# 场景 A: Worker 进程问题（验证假设）
Worker: task-85ea9d94 (8 个 task 卡住)  ← 全部集中在一个 Worker
  • task-xxx1 (message.route) 心跳超时: 188s
  • task-xxx2 (message.route) 心跳超时: 183s
  ...

# 场景 B: 不是 Worker 问题
Worker: task-85ea9d94 (1 个 task 卡住)
Worker: task-abc1234 (1 个 task 卡住)
Worker: task-def5678 (1 个 task 卡住)
...
```

### 方法 2: 看进程 CPU/内存

```bash
python diagnose_workers.py
```

**关键指标**:
- CPU > 90%: Worker 可能陷入死循环
- Memory > 500MB: 可能内存泄漏
- Uptime 很长但无活动: 进程僵死

### 方法 3: 查看进程线程状态（高级）

```bash
# 查看进程的线程和堆栈（需要 py-spy 或 gdb）
pip install py-spy

# 查看 Task Worker 的堆栈
py-spy dump --pid <task_worker_pid>

# 如果看到大量线程卡在同一个位置，说明确实卡住了
```

### 方法 4: 时间线分析

```bash
# 查看 task 的时间线
sqlite3 ~/.novaic/novaic.db "
  SELECT 
    id, 
    claimed_by,
    claimed_at, 
    heartbeat_at,
    round((julianday('now') - julianday(heartbeat_at)) * 86400, 2) as age
  FROM tq_tasks 
  WHERE status = 'claimed' 
  ORDER BY claimed_at
"
```

**关键指标**:
- 如果多个 task 的 `claimed_at` 时间接近，`heartbeat_at` 也接近
  → 说明 Worker 在某个时刻集体卡住 ✅

---

## 🚨 实战案例

### 案例: 8 个 Saga 卡住

#### 步骤 1: 运行诊断
```bash
$ python diagnose_workers.py

📋 卡住的 Task (心跳 > 60s)
❌ 发现 1 个卡住的 task
Worker: task-85ea9d94 (1 个 task 卡住)
  • task-0c5210bb9bd2 (message.route)
    心跳超时: 188s

📋 卡住的 Saga (心跳 > 60s)
❌ 发现 8 个卡住的 saga
Worker: saga-a3112e8e (8 个 saga 卡住)  ← 关键！
  • saga-fdec74ef26f1 (message_process)
    当前步骤: 0
    心跳超时: 165s
  ...
```

**分析**:
- ✅ 8 个 saga 都被同一个 Saga Worker 认领
- ✅ 说明这个 Saga Worker 进程有问题
- ✅ 虽然只看到 1 个 claimed task，但可能有更多 task 已经超时被清理
- ✅ **假设成立！**

#### 步骤 2: 清理
```bash
$ python cleanup_stuck.py --execute
✅ 已清理 1 个 task
✅ 已清理 8 个 saga
```

#### 步骤 3: 重启 Worker
```bash
$ pkill -f main_task && python novaic-backend/main_task.py &
$ pkill -f main_saga && python novaic-backend/main_saga.py &
```

#### 步骤 4: 验证
```bash
$ python diagnose_workers.py
✅ 系统运行正常！
```

---

## 💡 预防措施

### 1. 定期运行监控
```bash
# 添加到 crontab
*/5 * * * * cd /path/to/novaic && python diagnose_workers.py >> /tmp/worker_check.log 2>&1
```

### 2. 自动清理（可选）
```bash
# 每小时自动清理卡住的任务
0 * * * * cd /path/to/novaic && python cleanup_stuck.py --execute >> /tmp/cleanup.log 2>&1
```

### 3. 实现 Health Worker（推荐）
创建一个独立的 Health Worker 进程，定期检查并恢复卡住的任务。

---

## 📚 总结

### ✅ 可以验证的假设

1. **Worker 进程卡住**
   - 工具: `diagnose_workers.py`
   - 指标: 多个任务被同一个 Worker 认领且卡住

2. **某个 Handler 卡住**
   - 工具: 查看 task 的 topic（都是 message.route）
   - 指标: 卡住的 task 都是同一个 topic

3. **资源耗尽**
   - 工具: `diagnose_workers.py` 看 CPU/内存
   - 指标: CPU > 90% 或 Memory 异常高

### 🔧 排查工具箱

| 工具 | 用途 | 何时使用 |
|------|------|----------|
| `diagnose_workers.py` | 健康检查 | 发现问题时立即运行 |
| `cleanup_stuck.py` | 清理卡住的任务 | 诊断后发现卡住时 |
| `monitor_workers.py` | 实时监控 | 持续监控生产环境 |

### 📋 排查清单

- [ ] 运行 `diagnose_workers.py`
- [ ] 检查是否有多个任务被同一个 Worker 认领
- [ ] 检查 Worker 进程的 CPU/内存
- [ ] 查看最近是否有任务完成（系统是否活跃）
- [ ] 如果发现问题，运行 `cleanup_stuck.py`
- [ ] 重启有问题的 Worker
- [ ] 再次运行 `diagnose_workers.py` 验证

**现在你有完整的工具链来验证假设了！** 🎉
