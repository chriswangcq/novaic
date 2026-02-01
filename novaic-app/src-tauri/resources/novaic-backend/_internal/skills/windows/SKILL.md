---
name: novaic-windows
description: Window management for listing, focusing, resizing and controlling desktop windows. Use for managing application windows and launching apps.
---

# Window Management

桌面窗口管理工具。

## 可用工具

### list_windows

列出所有桌面窗口。

```python
list_windows()
# 返回:
# - window_id (十六进制格式: 0x1234567)
# - title
# - position (x, y)
# - size (width, height)
```

### focus_window

将窗口置于前台。

```python
# 使用 window_id（从 list_windows 获取）
focus_window(window_id="0x1234567")
```

### maximize_window

最大化窗口。

```python
maximize_window(window_id="0x1234567")
```

### minimize_window

最小化窗口。

```python
minimize_window(window_id="0x1234567")
```

### close_window

关闭窗口。

```python
close_window(window_id="0x1234567")
```

### resize_window

调整窗口大小。

```python
resize_window(window_id="0x1234567", width=1280, height=720)
```

### launch_app

启动应用程序（非阻塞）。

```python
# 启动常用应用
launch_app(app_name="firefox")
launch_app(app_name="chromium")
launch_app(app_name="code")      # VSCode
launch_app(app_name="terminal")
launch_app(app_name="files")     # 文件管理器
```

## 使用流程

### 操作特定窗口

```python
# 1. 列出所有窗口
windows = list_windows()

# 2. 找到目标窗口的 window_id
# 例如找到标题包含 "Firefox" 的窗口

# 3. 操作窗口
focus_window(window_id="0x1234567")
maximize_window(window_id="0x1234567")
```

### 启动并操作应用

```python
# 1. 启动应用
launch_app(app_name="firefox")

# 2. 等待应用启动后列出窗口
list_windows()

# 3. 找到新窗口并操作
focus_window(window_id="0xnewwindow")
```

## 常见用例

### 整理工作区

```python
# 列出所有窗口
list_windows()

# 最大化主工作窗口
maximize_window(window_id="0x...")

# 最小化不需要的窗口
minimize_window(window_id="0x...")
```

### 切换应用

```python
# 查找目标应用窗口
list_windows()

# 切换到该窗口
focus_window(window_id="0x...")
```

## 注意事项

1. `window_id` 使用十六进制格式，如 `0x1234567`
2. `launch_app` 是非阻塞的，应用启动需要时间
3. 操作前先使用 `list_windows()` 获取最新窗口列表
