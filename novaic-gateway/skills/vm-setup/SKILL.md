---
name: vm-setup
description: VM setup tools reference. Download image, create VM, start VM are handled by UI. Agent uses agent-bootstrap skill after VM starts.
---

# VM Setup Skill

> **注意**: 这是工具参考文档。实际流程分工：
> - **UI 控制**: 下载镜像 → 创建 VM → 启动 VM
> - **Agent 接手**: VM 启动后使用 `agent-bootstrap` skill

## 流程分工

```
┌─────────────────────────────────────────────────────────────┐
│  UI 控制（Tauri App 前端）                                   │
│  1. 用户选配置（版本、磁盘大小、内存）                         │
│  2. 下载镜像页面（显示进度条）                                │
│  3. 创建 VM                                                 │
│  4. 启动 VM                                                 │
└─────────────────────────────────────────────────────────────┘
                              ↓
                         VM 启动完成
                              ↓
┌─────────────────────────────────────────────────────────────┐
│  Agent 接手（使用 agent-bootstrap skill）                    │
│  1. 检查 SSH 是否可用                                        │
│  2. 监控 cloud-init 日志，向用户报告进度                      │
│  3. 部署代码（qemu_deploy_vmuse_code）                       │
│  4. 验证 MCP Server                                         │
└─────────────────────────────────────────────────────────────┘
```

## 前提条件

- QEMU 已安装 (`brew install qemu`)
- QEMU Debug MCP 已启用 (`NOVAIC_MCP_QEMUDEBUG_ENABLED=true`)

## 工具列表

### VM 设置工具 (QemuDebug MCP)

| 工具 | 用途 | 耗时 |
|------|------|------|
| `qemu_download_image` | 下载 Ubuntu 云镜像 | ~5分钟 |
| `qemu_create_vm` | 创建 VM 磁盘 + cloud-init | ~30秒 |
| `qemu_start_vm` | 启动 VM | ~5秒 |
| `qemu_deploy_vmuse_code` | 部署 MCP Server 代码 | ~30秒 |

### VM 调试工具

| 工具 | 用途 |
|------|------|
| `qemu_status` | 检查 VM/SSH/VNC/MCP 状态 |
| `qemu_ssh_exec` | 在 VM 内执行命令 |
| `qemu_restart` | 重启 VM |

### 异步和通信

| 工具 | 用途 |
|------|------|
| `task_async` | 异步执行工具 |
| `task_query` | 查询任务状态 |
| `chat_notify` | 通知用户 |
| `chat_ask` | 询问用户 |

## 目录结构

```
~/.novaic/
├── shared/                              # 共享资源 (所有 agent 共用)
│   ├── images/                          # 源镜像
│   │   └── noble-server-cloudimg-arm64.img
│   └── firmware/                        # UEFI 固件
│
└── agents/{agent_id}/                   # Agent 独立资源
    └── vm/
        ├── disk/                        # VM 磁盘
        │   └── novaic-vm.qcow2
        ├── iso/                         # cloud-init ISO
        └── config/                      # cloud-init 配置
```

## 执行流程

### 阶段 0: 下载镜像 (首次，约5分钟)

```python
chat_notify("📥 检查 Ubuntu 云镜像...", level="info")

# 异步下载镜像 (下载到共享目录，所有 agent 共用)
task_id = task_async(
    tool="qemu_download_image",
    args={"version": "24.04"},
    label="下载 Ubuntu 镜像"
)["task_id"]

chat_notify("⏳ 下载镜像中，这可能需要几分钟... 您可以问我其他问题！", level="info")

# 轮询等待
while True:
    result = task_query(task_id=task_id)
    if result["status"] == "completed":
        if result["result"]["success"]:
            if result["result"]["downloaded"]:
                size = result["result"]["size_mb"]
                chat_notify(f"✅ 镜像下载完成！({size} MB)", level="success")
            else:
                chat_notify("✅ 镜像已存在，跳过下载", level="success")
        else:
            chat_notify(f"❌ 下载失败: {result['result']['error']}", level="error")
            return
        break
    # 等待后重试
```

### 阶段 1: 创建 VM (约30秒)

```python
chat_notify("🔧 创建 VM 磁盘和配置...", level="info")

task_id = task_async(
    tool="qemu_create_vm",
    args={"disk_size": "40G", "memory": "4096", "cpus": 4},
    label="创建 VM"
)["task_id"]

result = task_query(task_id=task_id)
if result["result"]["success"]:
    chat_notify("✅ VM 创建完成！", level="success")
else:
    chat_notify(f"❌ 创建失败: {result['result']['error']}", level="error")
    return
```

### 阶段 2: 启动 VM (约5秒)

```python
chat_notify("🚀 启动 VM...", level="info")

task_id = task_async(
    tool="qemu_start_vm",
    args={"memory": "4096", "cpus": 4, "daemon": True},
    label="启动 VM"
)["task_id"]

result = task_query(task_id=task_id)
if result["result"]["success"]:
    ports = result["result"]["ports"]
    chat_notify(
        f"✅ VM 已启动！\n"
        f"- SSH: localhost:{ports['ssh']}\n"
        f"- VNC: localhost:{ports['vnc']}\n"
        f"- MCP: localhost:{ports['mcp']}",
        level="success"
    )
else:
    chat_notify(f"❌ 启动失败: {result['result']['error']}", level="error")
    return
```

### 阶段 3: 等待 SSH 可用 (约2-3分钟)

```python
chat_notify("⏳ 等待 SSH 可用，这可能需要 2-3 分钟...", level="info")
chat_notify("别担心，我会持续检查状态。您可以问我其他问题！", level="info")

max_retries = 30
retry_count = 0

while retry_count < max_retries:
    task_id = task_async(
        tool="qemu_status",
        args={},
        label="检查 SSH"
    )["task_id"]
    
    # 等待 10 秒后查询
    result = task_query(task_id=task_id)
    if result["result"]["ssh_reachable"]:
        chat_notify("✅ SSH 已就绪！", level="success")
        break
    
    retry_count += 1
    if retry_count % 6 == 0:  # 每分钟提示一次
        chat_notify(f"⏳ 仍在等待 SSH... ({retry_count * 10}秒)", level="info")

if retry_count >= max_retries:
    chat_notify("❌ SSH 连接超时，请检查 VM 状态", level="error")
    return
```

### 阶段 4: 等待 cloud-init (首次启动，约5-10分钟)

```python
chat_notify(
    "☁️ 系统初始化中 (cloud-init)...\n"
    "首次启动需要 5-10 分钟安装桌面环境和依赖。",
    level="info"
)

max_retries = 60  # 最多等待 10 分钟
retry_count = 0

while retry_count < max_retries:
    task_id = task_async(
        tool="qemu_ssh_exec",
        args={
            "command": "test -f /var/log/novaic-init-done.log && echo 'DONE' || echo 'PENDING'",
            "timeout": 10
        },
        label="检查 cloud-init"
    )["task_id"]
    
    result = task_query(task_id=task_id)
    stdout = str(result.get("result", {}).get("stdout", ""))
    
    if "DONE" in stdout:
        chat_notify("✅ 系统初始化完成！", level="success")
        break
    
    retry_count += 1
    if retry_count % 6 == 0:  # 每分钟提示一次
        chat_notify(f"⏳ cloud-init 仍在运行... ({retry_count * 10}秒)", level="info")

if retry_count >= max_retries:
    chat_notify("⚠️ cloud-init 超时，但可以尝试继续", level="warning")
```

### 阶段 5: 部署 MCP Server 代码 (约30秒)

```python
chat_notify("📦 部署 MCP Server 代码...", level="info")

task_id = task_async(
    tool="qemu_deploy_vmuse_code",
    args={"restart_service": True},
    label="部署 MCP Server"
)["task_id"]

while True:
    result = task_query(task_id=task_id)
    
    if result["status"] == "completed":
        deploy_result = result["result"]
        if deploy_result.get("success"):
            files = ", ".join(deploy_result.get("files_copied", []))
            chat_notify(f"✅ 代码部署完成！\n已复制: {files}", level="success")
        else:
            chat_notify(f"❌ 部署失败: {deploy_result.get('error')}", level="error")
            return
        break
```

### 阶段 6: 验证 MCP Server

```python
chat_notify("🔍 验证 MCP Server...", level="info")

# 等待服务启动 (几秒)
task_id = task_async(
    tool="qemu_status",
    args={},
    label="验证 MCP"
)["task_id"]

result = task_query(task_id=task_id)
status = result["result"]

if status["mcp_reachable"]:
    chat_notify(
        "🎉 安装完成！MCP Server 已就绪！\n\n"
        "现在可以使用 VM 内的工具了：\n"
        "- `screenshot()` - 截取屏幕\n"
        "- `mouse()` - 鼠标操作\n"
        "- `keyboard()` - 键盘输入\n"
        "- `browser_navigate()` - 浏览器导航",
        level="success"
    )
else:
    chat_notify(
        "⚠️ MCP Server 未响应，可能还在启动中。\n"
        "请稍后重试 `qemu_status()`",
        level="warning"
    )
```

## 快速部署 (代码更新后)

如果 VM 已运行，只需更新代码：

```python
chat_notify("⚡ 快速部署：更新 MCP Server 代码...", level="info")

result = qemu_deploy_vmuse_code(restart_service=True)

if result["success"]:
    chat_notify("✅ 代码已更新，服务已重启！", level="success")
else:
    chat_notify(f"❌ 部署失败: {result['error']}", level="error")
```

## 常见问题

### SSH 连接失败

```python
# 检查 VM 状态
status = qemu_status()

if not status["vm_running"]:
    chat_ask("VM 未运行。请在 NovAIC App 中启动 VM，完成后告诉我。")
elif not status["ssh_reachable"]:
    chat_notify("SSH 不可达，可能还在启动中，等待 30 秒后重试...", level="info")
```

### cloud-init 卡住

```python
# 查看 cloud-init 日志
result = qemu_ssh_exec(command="tail -50 /var/log/cloud-init-output.log")
print(result["stdout"])

# 如果卡住，可以重启 VM
qemu_restart(force=False, wait_ready=True)
```

### MCP Server 启动失败

```python
# 查看服务日志
result = qemu_ssh_exec(command="journalctl -u novaic --no-pager -n 50")
print(result["stdout"])

# 手动重启服务
qemu_ssh_exec(command="sudo systemctl restart novaic")
```

## 时间估算

| 阶段 | 首次安装 | 后续启动 |
|------|---------|---------|
| 下载镜像 | ~5分钟 | 跳过 |
| 创建 VM | ~30秒 | 跳过 |
| 启动 VM | ~5秒 | ~5秒 |
| 等待 SSH | ~2-3分钟 | ~1分钟 |
| cloud-init | ~5-10分钟 | 跳过 |
| 部署代码 | ~30秒 | ~30秒 |
| **总计** | **~15-20分钟** | **~2分钟** |
