---
name: vm-setup
description: Setup NovAIC VM - wait for boot, deploy MCP Server. Use when setting up a new agent environment or redeploying code after updates.
---

# VM Setup Skill

完整的 VM 安装流程：等待启动 → 部署 MCP Server → 验证。

## 前提条件

- VM 已通过 NovAIC App 创建并启动
- QEMU Debug MCP 已启用 (`NOVAIC_MCP_QEMUDEBUG_ENABLED=true`)

## 核心原则

### 1. 异步执行
所有长时间操作都用 `task_async` + `task_query`，不阻塞对话。

### 2. 勤与用户沟通
每个阶段都用 `chat_notify` 告知进度，让用户知道发生了什么。

### 3. 耐心等待
VM 启动和 cloud-init 需要时间，多给用户安慰。

## 工具列表

| 工具 | 用途 |
|------|------|
| `qemu_status` | 检查 VM/SSH/MCP 状态 |
| `qemu_ssh_exec` | 在 VM 内执行命令 |
| `qemu_deploy_vmuse_code` | 部署 MCP Server 代码 |
| `qemu_restart` | 重启 VM |
| `task_async` | 异步执行工具 |
| `task_query` | 查询任务状态 |
| `chat_notify` | 通知用户 |
| `chat_ask` | 询问用户 |

## 执行流程

### 阶段 1: 检查 VM 状态

```python
# 通知用户开始
chat_notify("🚀 开始检查 VM 状态...", level="info")

# 异步检查状态
task_id = task_async(
    tool="qemu_status",
    args={},
    label="检查 VM 状态"
)["task_id"]

# 查询结果
result = task_query(task_id=task_id)
status = result["result"]

if not status["vm_running"]:
    chat_notify(
        "❌ VM 未运行。请在 NovAIC App 中启动 VM，或手动运行：\n"
        "```bash\ncd novaic-vm && ./scripts/start-vm.sh -d\n```",
        level="error"
    )
    return
```

### 阶段 2: 等待 SSH 可用

```python
chat_notify("⏳ 等待 SSH 可用，这可能需要 2-3 分钟...", level="info")
chat_notify("别担心，我会持续检查状态。您可以问我其他问题！", level="info")

max_retries = 30
retry_count = 0

while retry_count < max_retries:
    # 异步检查
    task_id = task_async(
        tool="qemu_status",
        args={},
        label="检查 SSH"
    )["task_id"]
    
    # 等待 10 秒
    # (Agent 可以在这期间响应用户)
    
    result = task_query(task_id=task_id)
    if result["result"]["ssh_reachable"]:
        chat_notify("✅ SSH 已就绪！", level="success")
        break
    
    retry_count += 1
    if retry_count % 6 == 0:  # 每分钟提示一次
        chat_notify(f"⏳ 仍在等待 SSH... ({retry_count * 10}秒)", level="info")
```

### 阶段 3: 等待 cloud-init 完成 (首次启动)

```python
chat_notify(
    "☁️ 检查系统初始化状态 (cloud-init)...\n"
    "首次启动需要 5-10 分钟安装桌面环境和依赖。",
    level="info"
)

# 检查 cloud-init 完成标记
task_id = task_async(
    tool="qemu_ssh_exec",
    args={
        "command": "test -f /var/log/novaic-init-done.log && echo 'DONE' || echo 'PENDING'",
        "timeout": 10
    },
    label="检查 cloud-init"
)["task_id"]

result = task_query(task_id=task_id)
if "DONE" in str(result.get("result", {}).get("stdout", "")):
    chat_notify("✅ 系统初始化已完成！", level="success")
else:
    chat_notify("⏳ cloud-init 正在运行，请耐心等待...", level="info")
    # 继续轮询等待...
```

### 阶段 4: 部署 MCP Server 代码

```python
chat_notify("📦 正在部署 MCP Server 代码...", level="info")

task_id = task_async(
    tool="qemu_deploy_vmuse_code",
    args={"restart_service": True},
    label="部署 MCP Server"
)["task_id"]

# 等待部署完成
while True:
    result = task_query(task_id=task_id)
    
    if result["status"] == "completed":
        deploy_result = result["result"]
        if deploy_result.get("success"):
            files = ", ".join(deploy_result.get("files_copied", []))
            chat_notify(f"✅ 代码部署完成！\n已复制: {files}", level="success")
        else:
            chat_notify(f"❌ 部署失败: {deploy_result.get('error')}", level="error")
        break
    
    # 等待后重试
```

### 阶段 5: 验证

```python
chat_notify("🔍 验证 MCP Server 状态...", level="info")

# 等待服务启动
# (服务重启需要几秒)

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
        "请稍后再试，或检查日志：\n"
        "```bash\n"
        "qemu_ssh_exec(command='journalctl -u novaic -f')\n"
        "```",
        level="warning"
    )
```

## 快速部署 (代码更新后)

如果只是更新代码，不需要等待 cloud-init：

```python
# 直接部署
chat_notify("⚡ 快速部署：更新 MCP Server 代码...", level="info")

qemu_deploy_vmuse_code(restart_service=True)

chat_notify("✅ 代码已更新，服务已重启！", level="success")
```

## 常见问题

### SSH 连接失败
```python
# 检查 VM 是否运行
qemu_status()

# 如果 VM 未运行，需要用户启动
chat_ask("VM 未运行，请在 NovAIC App 中启动 VM。完成后告诉我。")
```

### cloud-init 卡住
```python
# 查看 cloud-init 日志
qemu_ssh_exec(command="tail -50 /var/log/cloud-init-output.log")

# 可能需要重启 VM
qemu_restart(force=False, wait_ready=True)
```

### MCP Server 启动失败
```python
# 查看服务日志
qemu_ssh_exec(command="journalctl -u novaic --no-pager -n 50")

# 手动重启服务
qemu_ssh_exec(command="sudo systemctl restart novaic")
```

## 用户沟通示例

好的沟通方式：
- "⏳ 正在等待，这可能需要几分钟..."
- "别担心，我会持续检查。您可以问我其他问题！"
- "✅ 完成！现在可以..."
- "❌ 遇到问题，让我看看怎么解决..."

避免的方式：
- 长时间沉默
- 只说"等待中"不给进度
- 出错后不给解决方案
