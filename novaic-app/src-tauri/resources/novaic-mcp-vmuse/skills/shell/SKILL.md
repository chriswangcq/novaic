---
name: novaic-shell
description: Shell command execution and Python code running. Use for executing terminal commands, running scripts, and system operations.
---

# Shell Commands

Shell 命令执行和 Python 代码运行。

## 可用工具

### run_command

执行 Shell 命令。

```python
# 基本执行
run_command(command="ls -la")

# 指定工作目录
run_command(command="npm install", cwd="/home/user/project")

# 设置超时（秒）
run_command(command="long_running_task", timeout=120)

# GUI 应用必须后台运行！
run_command(command="firefox", background=True)

# 在 xterm 窗口中显示
run_command(command="htop", visible=True)
```

### run_python

直接执行 Python 代码。

```python
# 执行 Python 代码
run_python(code="""
import os
print(os.getcwd())
for f in os.listdir('.'):
    print(f)
""")

# 在可见窗口中执行
run_python(code="print('Hello')", visible=True)
```

## ⚠️ 重要注意事项

### GUI 应用必须后台运行

```python
# ❌ 错误 - 会阻塞
run_command(command="firefox")

# ✅ 正确 - 后台运行
run_command(command="firefox", background=True)
```

### 长时间命令设置超时

```python
# 默认超时 60 秒
run_command(command="some_long_task")

# 延长超时
run_command(command="build_project", timeout=300)
```

## 常见用例

### 项目操作

```python
# 安装依赖
run_command(command="pip install -r requirements.txt", cwd="/path/to/project")

# 运行测试
run_command(command="pytest", cwd="/path/to/project", timeout=120)

# 启动开发服务器（后台）
run_command(command="npm run dev", cwd="/path/to/frontend", background=True)
```

### 系统操作

```python
# 查看进程
run_command(command="ps aux | grep python")

# 查看磁盘使用
run_command(command="df -h")

# 查看网络连接
run_command(command="netstat -tlnp")
```

### Python 脚本

```python
# 数据处理
run_python(code="""
import json
with open('data.json') as f:
    data = json.load(f)
print(f"Records: {len(data)}")
""")

# 文件操作
run_python(code="""
from pathlib import Path
for p in Path('.').glob('**/*.py'):
    print(p)
""")
```
