---
name: novaic-shell
description: Shell command execution with unified task tracking. All commands return task_id + tail format.
---

# Shell Commands

Shell 命令执行。**统一返回格式：task_id + stdout/stderr tail**。

## 核心机制

```
run_command("任意命令")
    │
    └─ 始终返回: { task_id, status, stdout_tail, stderr_tail, ... }
           │
           ├─ <3秒完成 → status="completed", 包含 exit_code
           │
           └─ >3秒未完成 → status="running", 用 query_task 继续查询
```

**所有命令返回统一格式，需要更多输出就 query_task。**

## 可用工具

### run_command

执行 Shell 命令，返回 task_id + tail。

```python
# 所有命令都返回统一格式
result = run_command(command="ls -la")
# → { task_id: "abc123", status: "completed", stdout_tail: "...", exit_code: 0 }

result = run_command(command="pip install tensorflow")
# → { task_id: "def456", status: "running", stdout_tail: "", message: "..." }

# 指定工作目录
run_command(command="npm install", cwd="/home/user/project")

# 设置超时
run_command(command="build_project", timeout=300)

# 在 xterm 窗口中显示
run_command(command="htop", visible=True)
```

### query_task

查询任务状态，获取更多输出（tail）。

```python
# 查询任务
query_task(task_id="abc123")
# → { status: "running", stdout_tail: "Installing...", elapsed_seconds: 15.2 }

# 查询更多行
query_task(task_id="abc123", tail_lines=100)

# 完成后
# → { status: "completed", stdout_tail: "...", exit_code: 0, duration_seconds: 45.3 }
```

### list_tasks / clear_tasks

```python
list_tasks()      # 列出所有任务
clear_tasks()     # 清理已完成的任务
```

### run_python

执行 Python 代码（同样返回 task_id + tail）。

```python
run_python(code="""
import os
for f in os.listdir('.'):
    print(f)
""")
```

## 使用模式

```python
# 执行命令
result = run_command(command="pip install pandas")

# 检查状态
if result["status"] == "completed":
    print(result["stdout_tail"])
    print(f"Exit code: {result['exit_code']}")
else:
    # 还在运行，继续查询
    while True:
        status = query_task(result["task_id"])
        print(status["stdout_tail"])
        if status["status"] != "running":
            break
```

## 常见用例

```python
# 快速命令
run_command(command="ls -la")
run_command(command="ps aux | grep python")

# 慢命令（自动后台）
result = run_command(command="pip install tensorflow")
query_task(result["task_id"])  # 查看进度

# GUI 应用（会一直 running）
run_command(command="firefox")
# 不需要等它完成，继续做其他事
```
