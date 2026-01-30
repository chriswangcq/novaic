---
name: agent-bootstrap
description: Agent bootstrap after VM startup. Wait for system init, deploy MCP server code, verify service. Use when VM just started and agent needs to take over.
---

# Agent Bootstrap Skill

VM 启动后，Agent 接手进行初始化和部署。

## 触发时机

当 UI 完成以下步骤后，Agent 被唤醒：
1. 用户选择配置
2. 下载镜像（UI 显示进度）
3. 创建 VM
4. 启动 VM

## 核心任务

1. **等待 SSH** - 确保可以连接到 VM
2. **监控 cloud-init** - 查看日志，向用户报告进度
3. **部署代码** - 复制 MCP Server 代码到 VM
4. **启动服务** - 启动并验证 MCP Server

## 工具列表

| 工具 | 用途 |
|------|------|
| `qemu_status` | 检查 VM/SSH/MCP 状态 |
| `qemu_ssh_exec` | 在 VM 内执行命令 |
| `qemu_deploy_vmuse_code` | 部署 MCP Server 代码 |
| `chat_notify` | 向用户发送通知 |

## 执行流程

### 阶段 1: 确认 VM 已启动

```python
chat_notify("🚀 VM 已启动，我来接手初始化工作！", level="info")

# 检查 VM 状态
status = qemu_status()

if not status["vm_running"]:
    chat_notify("❌ VM 未运行，请检查启动状态", level="error")
    return

chat_notify("✅ VM 正在运行", level="success")
```

### 阶段 2: 等待 SSH 可用

```python
chat_notify("⏳ 等待 SSH 连接...", level="info")

max_retries = 30
retry_count = 0

while retry_count < max_retries:
    status = qemu_status()
    
    if status["ssh_reachable"]:
        chat_notify("✅ SSH 已连接！", level="success")
        break
    
    retry_count += 1
    if retry_count % 6 == 0:  # 每分钟通知一次
        chat_notify(f"⏳ 仍在等待 SSH... ({retry_count * 10}秒)", level="info")
    
    # 等待 10 秒

if retry_count >= max_retries:
    chat_notify("❌ SSH 连接超时", level="error")
    return
```

### 阶段 3: 监控 cloud-init（首次启动）

```python
# 检查是否首次启动（cloud-init 未完成）
result = qemu_ssh_exec(
    command="test -f /var/log/novaic-init-done.log && echo 'DONE' || echo 'PENDING'",
    timeout=10
)

if "DONE" in result.get("stdout", ""):
    chat_notify("✅ 系统已初始化完成（非首次启动）", level="success")
else:
    chat_notify(
        "☁️ 首次启动，系统正在初始化中...\n"
        "正在安装桌面环境和依赖，这需要 5-15 分钟。\n"
        "我会持续监控进度，请耐心等待！",
        level="info"
    )
    
    # 监控 cloud-init 日志
    last_lines = 0
    max_wait = 900  # 15 分钟
    waited = 0
    
    while waited < max_wait:
        # 获取新的日志行
        log_result = qemu_ssh_exec(
            command=f"tail -n +{last_lines + 1} /var/log/cloud-init-output.log 2>/dev/null | tail -20",
            timeout=10
        )
        
        if log_result.get("success"):
            stdout = log_result.get("stdout", "")
            if stdout.strip():
                # 提取关键信息通知用户
                lines = stdout.strip().split('\n')
                for line in lines[-3:]:  # 最后 3 行
                    if any(kw in line.lower() for kw in ['installing', 'setting up', 'processing', 'unpacking']):
                        chat_notify(f"📦 {line[:80]}...", level="info")
                        break
            
            # 更新行数
            count_result = qemu_ssh_exec(
                command="wc -l < /var/log/cloud-init-output.log 2>/dev/null || echo 0",
                timeout=5
            )
            if count_result.get("success"):
                try:
                    last_lines = int(count_result.get("stdout", "0").strip())
                except:
                    pass
        
        # 检查是否完成
        done_result = qemu_ssh_exec(
            command="test -f /var/log/novaic-init-done.log && echo 'DONE' || echo 'PENDING'",
            timeout=10
        )
        
        if "DONE" in done_result.get("stdout", ""):
            chat_notify("✅ 系统初始化完成！", level="success")
            break
        
        # 每 2 分钟报告一次进度
        waited += 30
        if waited % 120 == 0:
            chat_notify(f"⏳ 仍在初始化... ({waited // 60} 分钟)", level="info")
        
        # 等待 30 秒
    
    if waited >= max_wait:
        chat_notify("⚠️ 初始化超时，尝试继续部署...", level="warning")
```

### 阶段 4: 部署 MCP Server 代码

```python
chat_notify("📦 正在部署 MCP Server 代码...", level="info")

result = qemu_deploy_vmuse_code(restart_service=True)

if result.get("success"):
    files = ", ".join(result.get("files_copied", []))
    chat_notify(f"✅ 代码部署完成！\n已复制: {files}", level="success")
else:
    chat_notify(f"❌ 部署失败: {result.get('error')}", level="error")
    
    # 尝试查看日志
    log_result = qemu_ssh_exec(command="journalctl -u novaic -n 20 --no-pager")
    if log_result.get("success"):
        chat_notify(f"📋 服务日志:\n```\n{log_result.get('stdout', '')[:500]}\n```", level="info")
    return
```

### 阶段 5: 验证 MCP Server

```python
chat_notify("🔍 验证 MCP Server 状态...", level="info")

# 等待服务启动
max_retries = 12
retry_count = 0

while retry_count < max_retries:
    status = qemu_status()
    
    if status.get("mcp_reachable"):
        chat_notify(
            "🎉 初始化完成！MCP Server 已就绪！\n\n"
            "现在我可以：\n"
            "- 操作桌面和浏览器\n"
            "- 执行各种任务\n"
            "- 帮您完成工作\n\n"
            "有什么需要我帮忙的吗？",
            level="success"
        )
        return
    
    retry_count += 1
    # 等待 5 秒

if retry_count >= max_retries:
    chat_notify(
        "⚠️ MCP Server 未响应，但服务可能还在启动中。\n"
        "您可以稍后再试，或让我检查一下日志。",
        level="warning"
    )
    
    # 检查服务状态
    svc_result = qemu_ssh_exec(command="systemctl is-active novaic.service")
    chat_notify(f"服务状态: {svc_result.get('stdout', 'unknown')}", level="info")
```

## 用户沟通原则

1. **主动汇报进度** - 不要让用户等太久没消息
2. **解释正在做什么** - "正在安装桌面环境..."
3. **给出预期时间** - "这需要 5-15 分钟"
4. **遇到问题主动说明** - 不要沉默

## 示例对话

```
Agent: 🚀 VM 已启动，我来接手初始化工作！
Agent: ✅ VM 正在运行
Agent: ⏳ 等待 SSH 连接...
Agent: ✅ SSH 已连接！
Agent: ☁️ 首次启动，系统正在初始化中...
        正在安装桌面环境和依赖，这需要 5-15 分钟。
        我会持续监控进度，请耐心等待！
Agent: 📦 Setting up xfce4...
Agent: 📦 Setting up chromium-browser...
Agent: ⏳ 仍在初始化... (2 分钟)
Agent: 📦 Setting up python3-pip...
Agent: ✅ 系统初始化完成！
Agent: 📦 正在部署 MCP Server 代码...
Agent: ✅ 代码部署完成！已复制: src/, skills/, pyproject.toml
Agent: 🔍 验证 MCP Server 状态...
Agent: 🎉 初始化完成！MCP Server 已就绪！

        现在我可以：
        - 操作桌面和浏览器
        - 执行各种任务
        - 帮您完成工作

        有什么需要我帮忙的吗？
```

## 快速部署（非首次启动）

如果 VM 之前已经初始化过，流程会更快：

```python
# cloud-init 已完成，直接部署
chat_notify("⚡ 检测到非首次启动，直接部署代码...", level="info")

result = qemu_deploy_vmuse_code(restart_service=True)

if result.get("success"):
    chat_notify("✅ 部署完成！MCP Server 已就绪！", level="success")
```

## 错误处理

### SSH 连接失败
```python
chat_notify("❌ 无法连接 SSH，请检查 VM 是否正常启动", level="error")
# 建议用户检查 VNC 看看 VM 状态
```

### cloud-init 超时
```python
chat_notify("⚠️ 系统初始化超时，可能网络问题。尝试继续部署...", level="warning")
# 尝试继续，可能部分依赖需要手动安装
```

### 服务启动失败
```python
# 查看日志
log_result = qemu_ssh_exec(command="journalctl -u novaic -n 50 --no-pager")
chat_notify(f"📋 服务日志:\n{log_result.get('stdout', '')}", level="info")

# 尝试重启
qemu_ssh_exec(command="sudo systemctl restart novaic")
```
