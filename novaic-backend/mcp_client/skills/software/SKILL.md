---
name: novaic-software
description: Guidance for installing, launching, and troubleshooting software on Linux. Use when asked to "open X", "install Y", or when an application fails to start.
---

# Software Management & Operation

本指南教你如何在 Linux 环境下高效地管理和操作软件。

## 核心原则

1. **先检查，后安装**：始终先确认软件是否已存在。
2. **静默启动**：GUI 软件必须在后台启动。
3. **依赖修复**：根据错误输出自动识别并安装缺失的库。
4. **视觉验证**：启动后通过 `list_windows` 或 `screenshot` 确认成功。

## 标准工作流程

### 1. 查找与启动

首先尝试定位软件：
```bash
which <app_name>
```

如果找到路径，直接启动（后台模式）：
```python
run_command(command="<app_name>", background=True)
```

### 2. 处理安装

如果 `which` 找不到命令，尝试安装：
```python
# 1. 更新索引
run_command(command="sudo apt-get update")
# 2. 安装软件
run_command(command="sudo apt-get install -y <package_name>")
```

### 3. 故障排除（关键环节）

如果启动失败（例如 `exit_code: 127`），检查 `stderr`。常见的库缺失错误如下：
`error while loading shared libraries: libxkbcommon-x11.so.0: cannot open shared object file: No such file or directory`

**解决方案**：
搜索并安装对应的 Ubuntu 软件包。
```python
# 常见的底层依赖库安装
run_command(command="sudo apt-get install -y libxkbcommon-x11-0 libxcb-icccm4 libxcb-image0 libxcb-keysyms1 libxcb-render-util0 libxcb-xinerama0")
```

### 4. 验证运行状态

启动后，不要假设它已经成功，必须验证：

```python
# 1. 等待几秒钟
run_command(command="sleep 3")

# 2. 检查窗口列表
windows = list_windows()
# 寻找 title 匹配的窗口

# 3. 如果没找到窗口，检查进程
run_command(command="ps aux | grep <app_name>")
```

## 常见软件映射表

| 软件名称 | 启动命令 | 软件包名 (apt) |
|----------|----------|----------------|
| 微信 | `wechat` | `wechat` (需添加源) |
| 浏览器 | `chromium` | `chromium-browser` |
| 编辑器 | `code` | `code` |
| 终端 | `xfce4-terminal` | `xfce4-terminal` |

## ⚠️ 注意事项

- **sudo**: 安装软件需要 `sudo` 权限，系统通常已配置为免密。
- **背景运行**: 永远不要直接运行 GUI 命令（如 `firefox`），否则会阻塞工具直到超时。始终使用 `background=True`。
- **多窗口应用**: 某些应用启动后会产生多个窗口，使用 `list_windows` 时请注意筛选。
