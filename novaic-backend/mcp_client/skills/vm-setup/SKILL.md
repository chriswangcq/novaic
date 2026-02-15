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
| `subagent_spawn` | 异步执行任务（派生子 Agent） |
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

> **Note**: task_async/task_query 已移除，改用 subagent_spawn 执行长任务。

```python
chat_notify("📥 检查 Ubuntu 云镜像...", level="info")

# 派生子 Agent 下载镜像
spawn = subagent_spawn(
    task="使用 qemu_download_image 工具下载 Ubuntu 24.04 云镜像到共享目录。完成后报告结果。",
    share_context=False,
    timeout_minutes=10,
)
subagent_id = spawn["subagent_id"]

chat_notify("⏳ 下载镜像中，这可能需要几分钟... 您可以问我其他问题！", level="info")

# 轮询等待
while True:
    result = subagent_query(target_subagent_id=subagent_id)
    if result.get("completed"):
        if result.get("status") == "completed":
            chat_notify("✅ 镜像下载完成！", level="success")
        else:
            chat_notify(f"❌ 下载失败", level="error")
        break
    # 等待后重试
```

### 阶段 1: 创建 VM (约30秒)

```python
chat_notify("🔧 创建 VM 磁盘和配置...", level="info")

result = qemu_create_vm(disk_size="40G", memory="4096", cpus=4)
if result.get("success"):
    chat_notify("✅ VM 创建完成！", level="success")
else:
    chat_notify(f"❌ 创建失败: {result.get('error')}", level="error")
    return
```

### 阶段 2: 启动 VM (约5秒)

```python
chat_notify("🚀 启动 VM...", level="info")

result = qemu_start_vm(memory="4096", cpus=4, daemon=True)
if result.get("success"):
    ports = result.get("ports", {})
    chat_notify(
        f"✅ VM 已启动！\n"
        f"- SSH: localhost:{ports.get('ssh')}\n"
        f"- VNC: localhost:{ports.get('vnc')}\n"
        f"- MCP: localhost:{ports.get('mcp')}",
        level="success"
    )
else:
    chat_notify(f"❌ 启动失败: {result.get('error')}", level="error")
    return
```

### 阶段 3: 等待 SSH 可用 (约2-3分钟)

```python
chat_notify("⏳ 等待 SSH 可用，这可能需要 2-3 分钟...", level="info")

max_retries = 30
for retry_count in range(max_retries):
    result = qemu_status()
    if result.get("ssh_reachable"):
        chat_notify("✅ SSH 已就绪！", level="success")
        break
    if retry_count % 6 == 0:
        chat_notify(f"⏳ 仍在等待 SSH... ({retry_count * 10}秒)", level="info")
    time.sleep(10)
else:
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

max_retries = 60
for retry_count in range(max_retries):
    result = qemu_ssh_exec(
        command="test -f /var/log/novaic-init-done.log && echo 'DONE' || echo 'PENDING'",
        timeout=10,
    )
    stdout = str(result.get("stdout", ""))
    if "DONE" in stdout:
        chat_notify("✅ 系统初始化完成！", level="success")
        break
    if retry_count % 6 == 0:
        chat_notify(f"⏳ cloud-init 仍在运行... ({retry_count * 10}秒)", level="info")
    time.sleep(10)
else:
    chat_notify("⚠️ cloud-init 超时，但可以尝试继续", level="warning")
```

### 阶段 5: 部署 MCP Server 代码 (约30秒)

```python
chat_notify("📦 部署 MCP Server 代码...", level="info")

result = qemu_deploy_vmuse_code(restart_service=True)
if result.get("success"):
    files = ", ".join(result.get("files_copied", []))
    chat_notify(f"✅ 代码部署完成！\n已复制: {files}", level="success")
else:
    chat_notify(f"❌ 部署失败: {result.get('error')}", level="error")
    return
```

### 阶段 6: 验证 MCP Server

```python
chat_notify("🔍 验证 MCP Server...", level="info")

status = qemu_status()

if status.get("mcp_reachable"):
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
