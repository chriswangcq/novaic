# Phase 3.1 快速启动指南

## ⚠️ 重要：需要重启 VM

当前有运行中的 VM（PID 1897，agent index 1），但它是用旧配置启动的，**没有 Guest Agent 支持**。

需要重启 VM 以应用新的配置。

## 步骤 1：重启 VM

### 方法 A：通过 Gateway API（推荐）

如果 Gateway 正在运行：

```bash
# 停止 VM
curl -X POST http://localhost:8000/agents/{agent_id}/vm/stop

# 启动 VM
curl -X POST http://localhost:8000/agents/{agent_id}/vm/start
```

### 方法 B：手动重启

```bash
# 查找 QEMU 进程
ps aux | grep qemu

# 优雅关闭（推荐）
# 通过 SSH 发送关机命令
ssh -p 20028 ubuntu@localhost sudo poweroff

# 或者使用 QMP（如果可用）
echo '{"execute":"qmp_capabilities"}' | socat - UNIX-CONNECT:/var/folders/.../novaic/novaic-qmp-1.sock
echo '{"execute":"system_powerdown"}' | socat - UNIX-CONNECT:/var/folders/.../novaic/novaic-qmp-1.sock

# 强制结束（不推荐，可能损坏 VM）
kill 1897
```

### 方法 C：重启 Gateway

如果 Gateway 正在运行，重启它会自动管理 VM：

```bash
# 停止 Gateway (Ctrl+C)
# 然后重新启动
cd novaic-backend
python -m gateway.main
```

## 步骤 2：验证新配置

重启 VM 后，检查 Guest Agent socket 是否创建：

```bash
# 检查 socket 文件
ls -la /var/folders/n3/_7qrtb716jg07p9d71216l3m0000gn/T/novaic/

# 应该看到三个文件：
# - novaic-mcp-1.sock   (MCP 通信)
# - novaic-qmp-1.sock   (QEMU 管理)
# - novaic-ga-1.sock    (Guest Agent) ← 新增
```

## 步骤 3：安装 VM 内的 Guest Agent

SSH 进入 VM：

```bash
ssh -p 20028 ubuntu@localhost
```

在 VM 内执行：

```bash
# 安装
sudo apt-get update
sudo apt-get install -y qemu-guest-agent

# 启动服务
sudo systemctl enable qemu-guest-agent
sudo systemctl start qemu-guest-agent

# 验证
sudo systemctl status qemu-guest-agent

# 检查 virtio-serial 设备
ls -l /dev/virtio-ports/org.qemu.guest_agent.0
```

退出 SSH：

```bash
exit
```

## 步骤 4：测试连接

在宿主机（macOS）上：

```bash
cd novaic-backend/gateway/vm

# 列出可用的 socket
python test_guest_agent.py list

# 测试 Guest Agent
python test_guest_agent.py 1
```

期望输出：

```
Testing Guest Agent for agent 1
Socket path: /var/folders/.../novaic/novaic-ga-1.sock
------------------------------------------------------------
✅ Socket file exists

Test 1: guest-ping
✅ guest-ping successful: {'return': {}}

Test 2: guest-info
✅ guest-info successful
   Version: X.X.X
   Supported commands: XX

   Important commands available:
     ✅ guest-file-open
     ✅ guest-file-read
     ✅ guest-file-write
     ✅ guest-file-close
     ✅ guest-exec
     ✅ guest-exec-status
     ✅ guest-shutdown
     ✅ guest-sync

============================================================
✅ Guest Agent is working correctly!
============================================================
```

## 步骤 5：手动测试（可选）

使用 socat 手动测试：

```bash
# 安装 socat（如果没有）
brew install socat

# 测试 ping
echo '{"execute":"guest-ping"}' | socat - UNIX-CONNECT:/var/folders/n3/_7qrtb716jg07p9d71216l3m0000gn/T/novaic/novaic-ga-1.sock

# 期望响应：{"return":{}}

# 获取详细信息
echo '{"execute":"guest-info"}' | socat - UNIX-CONNECT:/var/folders/n3/_7qrtb716jg07p9d71216l3m0000gn/T/novaic/novaic-ga-1.sock | python -m json.tool
```

## 完成标准检查

- ✅ QEMU 启动参数包含 Guest Agent 配置（已修改代码）
- ✅ VM 重启后 GA socket 文件存在
- ✅ VM 内 Guest Agent 服务运行中
- ✅ `guest-ping` 命令成功
- ✅ `guest-info` 命令成功并显示支持的命令

## 故障排查

如果遇到问题，参考 `GUEST_AGENT_SETUP.md` 中的详细故障排查指南。

## 下一步

Phase 3.1 完成后，可以进行：
- **Phase 3.2**：实现文件操作 API
- **Phase 3.3**：实现命令执行 API  
- **Phase 3.4**：集成到 Gateway 的 vmcontrol 模块
