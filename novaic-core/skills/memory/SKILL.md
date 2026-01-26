---
name: novaic-memory
description: Persistent memory and goal tracking system. Use for saving context across sessions, tracking multi-step tasks, and maintaining project state.
---

# Memory System

持久化记忆和目标追踪系统，用于跨会话保持上下文。

## 🧠 何时使用记忆

- 重要上下文：项目信息、用户偏好
- 多步骤任务的中间状态
- 需要跨会话保持的信息

## 可用工具

### 基础记忆操作

```python
# 保存记忆
memory_save(
    key="project_context",
    value={"name": "xxx", "tech_stack": ["Python", "React"]},
    namespace="default",  # 可选，默认 "default"
    persistent=True       # 可选，默认 True，保存到磁盘
)

# 读取记忆
memory_recall(key="project_context")

# 读取命名空间下所有记忆
memory_recall(namespace="default")

# 删除记忆
memory_delete(key="project_context")
```

### 任务日志

记录操作历史，便于追踪和调试。

```python
# 记录任务
task_log(
    action="完成用户认证模块",
    details="实现了 JWT token 验证",
    status="completed"  # "completed" | "failed" | "in_progress"
)

# 查看历史
task_history(limit=20)
task_history(status_filter="failed")  # 只看失败的
```

### 目标追踪

适用于复杂的多步骤任务。

```python
# 设置目标
goal_set(
    goal="完成用户认证模块",
    subtasks=["设计数据库", "实现API", "编写测试"]
)

# 更新进度
goal_progress(completed_subtask="设计数据库")
goal_progress(progress_note="API 实现中，已完成 50%")

# 完成目标
goal_complete(summary="已完成所有子任务，认证模块上线")
```

### 会话状态

获取当前会话的整体状态。

```python
# 获取会话概览
session_state()
# 返回: 当前目标、最近操作、统计信息
```

## 使用模式

### 项目上下文保存

```python
# 开始新项目时保存上下文
memory_save("project", {
    "name": "电商平台",
    "tech_stack": ["FastAPI", "React", "PostgreSQL"],
    "current_phase": "开发中",
    "key_files": ["src/main.py", "frontend/App.tsx"]
})

# 下次对话时恢复
context = memory_recall(key="project")
```

### 多步骤任务追踪

```python
# 1. 设置目标
goal_set(
    goal="重构数据库层",
    subtasks=[
        "分析现有表结构",
        "设计新的 schema",
        "编写迁移脚本",
        "测试数据迁移"
    ]
)

# 2. 完成每个子任务后更新
goal_progress(completed_subtask="分析现有表结构")
task_log(action="分析表结构", details="发现 3 个需要优化的表")

# 3. 最终完成
goal_complete(summary="数据库重构完成，性能提升 40%")
```

## 最佳实践

1. **语义化 key**：使用有意义的 key 名，如 `project_context` 而非 `data1`
2. **合理分命名空间**：不同项目使用不同 namespace
3. **及时清理**：任务完成后清理不再需要的记忆
4. **定期检查**：使用 `session_state()` 查看当前状态
