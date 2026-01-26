---
name: novaic-context
description: Environment awareness and context tools. Use to understand system state, analyze directories, manage clipboard, and get environment information before starting tasks.
---

# Context & Environment

环境感知工具，在开始任务前了解当前状态。

## 🔍 何时使用

- 开始新任务前，了解系统状态
- 分析项目结构
- 获取环境信息用于决策

## 可用工具

### system_snapshot

获取系统全貌：窗口列表、资源使用、剪贴板内容。

```python
system_snapshot()
# 返回:
# - 所有打开的窗口
# - CPU/内存使用率
# - 剪贴板内容
# - 当前活动窗口
```

### directory_snapshot

分析目录结构，识别项目类型。

```python
# 分析当前目录
directory_snapshot()

# 分析指定目录
directory_snapshot(path="/home/user/project")

# 控制深度
directory_snapshot(path=".", max_depth=5)

# 包含隐藏文件
directory_snapshot(include_hidden=True)

# 返回:
# - 目录树结构
# - 项目类型识别（Python/Node/React 等）
# - 文件统计
```

### app_state

获取特定应用的状态。

```python
app_state(app_name="firefox")
# 返回:
# - 应用窗口列表
# - 进程信息
```

### clipboard_get / clipboard_set

剪贴板操作。

```python
# 获取剪贴板内容
clipboard_get()

# 设置剪贴板内容
clipboard_set(content="要复制的文本")
```

### recent_files

查找最近修改的文件。

```python
# 最近修改的 10 个文件
recent_files()

# 指定数量
recent_files(limit=20)

# 过滤扩展名
recent_files(extensions=[".py", ".ts"])

# 指定目录
recent_files(path="/home/user/project")
```

### environment_info

获取开发环境信息。

```python
environment_info()
# 返回:
# - Shell 类型
# - PATH 内容
# - 已安装的工具（python, node, git 等）
# - 环境变量
```

## 使用模式

### 开始任务前的环境检查

```python
# 1. 了解系统状态
system_snapshot()

# 2. 分析项目结构
directory_snapshot()

# 3. 检查开发环境
environment_info()
```

### 项目分析工作流

```python
# 分析项目
snapshot = directory_snapshot(path="/path/to/project", max_depth=3)

# 查看最近修改的文件
recent_files(path="/path/to/project", extensions=[".py"])

# 检查是否有需要的工具
environment_info()
```

## 最佳实践

1. **任务开始前**：使用 `system_snapshot()` 了解当前状态
2. **新项目**：使用 `directory_snapshot()` 分析结构
3. **调试时**：使用 `recent_files()` 找到最近修改的文件
4. **环境问题**：使用 `environment_info()` 检查工具可用性
