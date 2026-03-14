# QEMU Guest Agent 安装和配置指南

## 概述

QEMU Guest Agent (qga) 是运行在虚拟机内部的服务，通过 virtio-serial 与宿主机的 QEMU 进程通信。它提供：
- 文件操作（读写、打开、关闭）
- 命令执行
- 系统控制（关机、重启、冻结文件系统等）
- 系统信息获取

## Phase 3.1 完成状态

### ✅ 已完成的修改

1. **QEMU 启动参数配置**
   - 在 `_build_arm64_args` 中添加 Guest Agent 通道
   - 在 `_build_x86_args` 中添加 Guest Agent 通道
   - Socket 路径：`/tmp/novaic/novaic-ga-{agent_id}.sock`

2. **配置细节**
   ```python
   ga_socket_path = socket_dir / f"novaic-ga-{agent_id}.sock"
   
   args.extend([
       "-chardev", f"socket,path={ga_socket_path},server=on,wait=off,id=qga0",
       "-device", "virtserialport,chardev=qga0,name=org.qemu.guest_agent.0",
   ])
   ```

### 🔄 需要重启 VM

**重要**：修改 QEMU 启动参数后，需要重启 VM 才能生效。

```bash
# 通过 Gateway API 重启 VM
# 或者手动重启
```

## VM 内安装 Guest Agent

### Ubuntu/Debian (推荐)

```bash
# 1. 更新包列表
sudo apt-get update

# 2. 安装 qemu-guest-agent
sudo apt-get install -y qemu-guest-agent

# 3. 启用自动启动
sudo systemctl enable qemu-guest-agent

# 4. 启动服务
sudo systemctl start qemu-guest-agent

# 5. 检查状态
sudo systemctl status qemu-guest-agent
```

### 检查安装

```bash
# 检查是否安装
which qemu-ga

# 检查服务状态
sudo systemctl status qemu-guest-agent

# 检查 virtio-serial 设备
ls -l /dev/virtio-ports/

# 应该看到 org.qemu.guest_agent.0
ls -l /dev/virtio-ports/org.qemu.guest_agent.0
```

## 宿主机测试

### 1. 列出可用的 Socket

```bash
cd novaic-backend/gateway/vm
python test_guest_agent.py list
```

### 2. 测试 Guest Agent 连接

```bash
# 测试指定 agent (使用 agent_id)
python test_guest_agent.py <agent_id>

# 示例：
python test_guest_agent.py 550e8400-e29b-41d4-a716-446655440000
```

### 3. 手动测试（使用 socat）

```bash
# 需要先安装 socat
# macOS: brew install socat
# Ubuntu: apt-get install socat

# 测试 ping (替换 <agent_id> 为实际的 agent ID)
echo '{"execute":"guest-ping"}' | socat - UNIX-CONNECT:/tmp/novaic/novaic-ga-<agent_id>.sock

# 期望响应：{"return":{}}

# 获取 Guest Agent 信息
echo '{"execute":"guest-info"}' | socat - UNIX-CONNECT:/tmp/novaic/novaic-ga-<agent_id>.sock
```

## 故障排查

### 问题 1：Socket 文件不存在

**症状**：`/tmp/novaic/novaic-ga-*.sock` 不存在

**原因**：
- VM 未运行
- QEMU 未配置 Guest Agent 参数
- VM 启动失败

**解决**：
1. 检查 VM 是否运行：`ps aux | grep qemu`
2. 检查 QEMU 命令参数（从 DB 或日志）
3. 重启 VM 以应用新配置

### 问题 2：Socket 存在但连接超时

**症状**：Socket 文件存在，但 `guest-ping` 超时

**原因**：
- VM 内未安装 qemu-guest-agent
- qemu-guest-agent 服务未运行
- virtio-serial 设备未正确识别

**解决**：
1. SSH 进入 VM
2. 安装 qemu-guest-agent（见上文）
3. 检查 `/dev/virtio-ports/org.qemu.guest_agent.0` 是否存在
4. 检查服务状态：`sudo systemctl status qemu-guest-agent`

### 问题 3：部分命令不可用

**症状**：`guest-ping` 成功，但其他命令失败

**原因**：
- Guest Agent 版本过旧
- 某些命令需要特定权限或配置

**解决**：
1. 升级 qemu-guest-agent 到最新版本
2. 检查 `/etc/qemu/qemu-ga.conf` 配置
3. 查看 Guest Agent 日志：`journalctl -u qemu-guest-agent`

## 验证完成标准

运行测试脚本应该显示：

```
✅ Socket file exists
✅ guest-ping successful
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

✅ Guest Agent is working correctly!
```

## 下一步

Phase 3.1 完成后，可以进行：
- **Phase 3.2**：实现文件操作 API（读写文件）
- **Phase 3.3**：实现命令执行 API
- **Phase 3.4**：集成到 vmcontrol 模块

## 参考资料

- [QEMU Guest Agent Protocol](https://wiki.qemu.org/Features/GuestAgent)
- [QGA Commands](https://qemu.readthedocs.io/en/latest/interop/qemu-ga-ref.html)
- Ubuntu qemu-guest-agent package
