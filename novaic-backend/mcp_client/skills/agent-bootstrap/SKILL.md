---
name: agent-bootstrap
description: Agent bootstrap after VM startup. Intelligent deployment with automatic cloud-init detection and service management.
---

# Agent Bootstrap Skill

VM 启动后，Agent 接手进行初始化和部署。

## 触发时机

当 UI 完成 VM 启动后，Agent 被唤醒执行 bootstrap。

## 核心任务

1. **等待 SSH** - 确保可以连接到 VM
2. **部署并启动** - 调用 `qemu_deploy_vmuse_code` 一步完成
3. **验证** - 确认 MCP Server 可用

## 工具列表

| 工具 | 用途 |
|------|------|
| `qemu_status` | 检查 VM/SSH/MCP 状态 |
| `qemu_deploy_vmuse_code` | **智能部署工具** - 自动检查 cloud-init、部署代码、启动服务 |
| `chat_notify` | 向用户发送通知 |

## `qemu_deploy_vmuse_code` 返回值说明

| 字段 | 类型 | 说明 |
|------|------|------|
| `success` | bool | 部署是否成功 |
| `status` | str | `"wait"` / `"deployed"` / `"error"` |
| `cloudinit_complete` | bool | cloud-init 是否完成 |
| `cloudinit_progress` | str | 当前阶段（如 "Installing desktop environment..."）|
| `cloudinit_percent` | int | 进度百分比（5-95）|
| `cloudinit_eta_minutes` | int | 预计剩余时间（分钟）|
| `cloudinit_last_activity` | str | 最近的日志行 |
| `venv_ready` | bool | Python venv 是否就绪 |
| `files_copied` | list | 复制的文件列表 |
| `service_status` | str | 服务状态（active/inactive/start_failed）|
| `mcp_reachable` | bool | MCP 是否可达 |

### 返回状态处理

| status | 含义 | Agent 应对 |
|--------|------|-----------|
| `wait` | cloud-init 或 venv 未就绪 | 通知用户等待，1 分钟后重试 |
| `deployed` | 部署成功 | 继续验证 MCP |
| `error` | 部署失败 | 显示错误信息，可能需要调试 |

## 执行流程

### 阶段 1: 确认 SSH 可用

```python
chat_notify("🚀 VM 已启动，正在连接...", level="info")

max_retries = 30
for i in range(max_retries):
    status = qemu_status()
    
    if status["ssh_reachable"]:
        chat_notify("✅ SSH 已连接！", level="success")
        break
    
    if i % 6 == 0 and i > 0:  # 每分钟通知一次
        chat_notify(f"⏳ 等待 SSH... ({i * 10}秒)", level="info")
    
    # 等待 10 秒

if not status.get("ssh_reachable"):
    chat_notify("❌ SSH 连接超时", level="error")
    return
```

### 阶段 2: 部署（一个工具调用搞定！）

```python
chat_notify("📦 正在部署 MCP Server...", level="info")

max_attempts = 20  # 最多等待 20 分钟
attempt = 0
first_wait = True

while attempt < max_attempts:
    result = qemu_deploy_vmuse_code(restart_service=True)
    
    if result["status"] == "wait":
        # cloud-init 还在进行
        percent = result.get("cloudinit_percent", 0)
        stage = result.get("cloudinit_progress", "Initializing...")
        eta = result.get("cloudinit_eta_minutes", "?")
        last_activity = result.get("cloudinit_last_activity", "")
        
        # 首次等待时给用户完整说明
        if first_wait:
            first_wait = False
            chat_notify(
                "☁️ **首次启动，系统正在初始化...**\n"
                "正在安装桌面环境和依赖，预计需要 10-15 分钟。\n"
                "我会持续监控进度，请耐心等待！",
                level="info"
            )
        
        # 显示详细进度
        progress_bar = "█" * (percent // 10) + "░" * (10 - percent // 10)
        chat_notify(
            f"⏳ [{progress_bar}] {percent}%\n"
            f"📍 {stage}\n"
            f"⏱️ 预计还需 ~{eta} 分钟",
            level="info"
        )
        
        # 如果有具体活动，也显示
        if last_activity:
            chat_notify(f"📋 {last_activity}", level="info")
        
        attempt += 1
        # 等待 1 分钟后重试
        continue
    
    if result["success"]:
        files = ", ".join(result.get("files_copied", []))
        chat_notify(f"✅ 代码部署完成！\n已复制: {files}", level="success")
        break
    else:
        # 部署失败
        error = result.get("error") or result.get("message", "Unknown error")
        chat_notify(f"❌ 部署失败: {error}", level="error")
        
        # 显示服务日志（如果有）
        if result.get("service_logs"):
            chat_notify(f"📋 服务日志:\n```\n{result['service_logs']}\n```", level="info")
        return

if attempt >= max_attempts:
    chat_notify("⚠️ 初始化超时，请检查 VM 状态", level="warning")
    return
```

### 阶段 3: 验证 MCP（可选，工具已内置验证）

```python
# qemu_deploy_vmuse_code 已经验证了 MCP
# 但可以再次确认

if result.get("mcp_reachable"):
    chat_notify(
        "🎉 **初始化完成！MCP Server 已就绪！**\n\n"
        "现在我可以：\n"
        "- 📸 操作桌面（截图、鼠标、键盘）\n"
        "- 🌐 控制浏览器\n"
        "- 💻 执行各种任务\n\n"
        "有什么需要我帮忙的吗？",
        level="success"
    )
else:
    # 服务已启动但 MCP 还没响应，可能需要几秒
    chat_notify("⏳ 服务已启动，MCP 正在初始化...", level="info")
    
    # 等待几秒后用 qemu_status 再次检查
    for i in range(6):
        # 等待 5 秒
        status = qemu_status()
        if status.get("mcp_reachable"):
            chat_notify("🎉 MCP Server 已就绪！", level="success")
            break
```

## 完整示例对话

### 首次启动（需要等待 cloud-init）

```
Agent: 🚀 VM 已启动，正在连接...
Agent: ⏳ 等待 SSH... (60秒)
Agent: ✅ SSH 已连接！
Agent: 📦 正在部署 MCP Server...
Agent: ☁️ **首次启动，系统正在初始化...**
        正在安装桌面环境和依赖，预计需要 10-15 分钟。
        我会持续监控进度，请耐心等待！
Agent: ⏳ [██░░░░░░░░] 20%
        📍 Installing desktop environment...
        ⏱️ 预计还需 ~10 分钟
Agent: 📋 Setting up xfce4-terminal (1.0.4-1build2)...
Agent: ⏳ [████░░░░░░] 40%
        📍 Installing Chromium browser...
        ⏱️ 预计还需 ~8 分钟
Agent: ⏳ [██████░░░░] 60%
        📍 Installing Python environment...
        ⏱️ 预计还需 ~6 分钟
Agent: ⏳ [████████░░] 80%
        📍 Installing Python dependencies...
        ⏱️ 预计还需 ~3 分钟
Agent: 📋 pip install fastmcp fastapi uvicorn...
Agent: ⏳ [█████████░] 90%
        📍 Installing Playwright Chromium...
        ⏱️ 预计还需 ~2 分钟
Agent: ✅ 代码部署完成！已复制: src/, skills/, pyproject.toml
Agent: 🎉 **初始化完成！MCP Server 已就绪！**
```

### 后续启动（cloud-init 已完成）

```
Agent: 🚀 VM 已启动，正在连接...
Agent: ✅ SSH 已连接！
Agent: 📦 正在部署 MCP Server...
Agent: ✅ 代码部署完成！已复制: src/, skills/, pyproject.toml
Agent: 🎉 **初始化完成！MCP Server 已就绪！**
```

## 预期时间

| 场景 | 时间 |
|------|------|
| 首次启动（含 cloud-init）| 10-20 分钟 |
| 后续启动 | 1-2 分钟 |
| 仅更新代码 | 30 秒 |

---

## cloud-init 安装阶段说明

当 `qemu_deploy_vmuse_code` 返回 `status: "wait"` 时，工具会自动检测进度并返回以下信息：
- `cloudinit_percent`: 进度百分比
- `cloudinit_progress`: 当前阶段描述
- `cloudinit_eta_minutes`: 预计剩余时间
- `cloudinit_last_activity`: 最近的日志行

### 安装步骤和里程碑

| 进度 | 阶段 | 内容 | 预计时间 |
|------|------|------|---------|
| 10% | apt update | 更新包列表 | 1-2 分钟 |
| 20% | xfce4 | 安装桌面环境 | 3-5 分钟 |
| 40% | chromium | 安装浏览器 | 2-3 分钟 |
| 60% | python3-pip | 安装 Python 环境 | 1-2 分钟 |
| 70% | venv | 创建 Python 虚拟环境 | 30 秒 |
| 80% | pip install | 安装 Python 依赖 | 2-3 分钟 |
| 90% | playwright | 安装 Playwright Chromium | 2-3 分钟 |
| 95% | services | 启动 lightdm | 30 秒 |

### 如果需要更详细的日志

Agent 可以额外调用 `qemu_ssh_exec` 查看完整日志：

```python
# 查看最近的 cloud-init 日志
log_result = qemu_ssh_exec(
    command="tail -30 /var/log/cloud-init-output.log",
    timeout=10
)
chat_notify(f"📋 日志:\n```\n{log_result.get('stdout', '')}\n```", level="info")
```

### 用户沟通原则

1. **每 1-2 分钟报告一次进度** - 不要让用户等太久没消息
2. **显示进度条和百分比** - 让用户知道大概进度
3. **给出预估时间** - 工具返回的 `eta_minutes` 字段
4. **遇到异常主动说明** - 如果某个步骤卡住超过 5 分钟，告诉用户

---

## 错误处理

### SSH 连接失败

```python
chat_notify(
    "❌ 无法连接 SSH，可能的原因：\n"
    "- VM 还在启动中\n"
    "- 网络配置问题\n"
    "请检查 VNC 查看 VM 状态。",
    level="error"
)
```

### cloud-init 超时

如果等待超过 20 分钟：

```python
chat_notify(
    "⚠️ 系统初始化超时。\n"
    "可能是网络问题导致下载缓慢。\n"
    "你可以：\n"
    "1. 继续等待\n"
    "2. 重启 VM 重试\n"
    "3. 使用 force=True 强制部署",
    level="warning"
)
```

### 服务启动失败

```python
# 查看服务日志
result = qemu_ssh_exec(command="journalctl -u novaic -n 30 --no-pager")
chat_notify(f"📋 服务日志:\n```\n{result.get('stdout', '')}\n```", level="info")

# 可能的解决方案
chat_notify(
    "可能的原因：\n"
    "- Python 依赖缺失\n"
    "- 代码语法错误\n"
    "- 端口被占用",
    level="info"
)
```

## 关键提示

1. **不要手动创建 venv** - cloud-init 会在 `/opt/novaic-venv` 创建
2. **不要手动安装依赖** - cloud-init 会安装所有必要的包
3. **不要手动启动服务** - `qemu_deploy_vmuse_code` 会自动启动
4. **耐心等待 cloud-init** - 首次启动需要时间，这是正常的
