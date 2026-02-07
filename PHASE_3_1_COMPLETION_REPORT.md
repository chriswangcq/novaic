# Phase 3.1 完成报告：配置并启动 QEMU Guest Agent

**日期**：2026-02-06  
**状态**：✅ 代码修改完成，等待 VM 重启和验证

---

## 📋 任务总结

Phase 3.1 的目标是在 VM 内配置和启动 QEMU Guest Agent，为后续的文件操作和命令执行提供基础。

## ✅ 已完成的工作

### 1. 代码修改

#### 文件：`novaic-backend/gateway/vm/manager.py`

**修改内容**：
- ✅ 在 `_build_arm64_args` 方法中添加 Guest Agent 配置（第 518 行）
- ✅ 在 `_build_x86_args` 方法中添加 Guest Agent 配置（第 571 行）

**添加的配置**：
```python
# Guest Agent socket 路径
ga_socket_path = socket_dir / f"novaic-ga-{config.agent_index}.sock"

# QEMU 参数
"-chardev", f"socket,path={ga_socket_path},server=on,wait=off,id=qga0",
"-device", "virtserialport,chardev=qga0,name=org.qemu.guest_agent.0",
```

**特性**：
- ✅ ARM64 和 x86_64 架构都已配置
- ✅ Socket 路径使用统一的 `socket_dir`（临时目录）
- ✅ 命名风格与 QMP/MCP socket 保持一致
- ✅ 代码无 lint 错误

### 2. 测试工具

#### 文件：`novaic-backend/gateway/vm/test_guest_agent.py`

**功能**：
- ✅ 自动检测 Guest Agent socket
- ✅ 测试 `guest-ping` 命令
- ✅ 测试 `guest-info` 命令并显示支持的功能
- ✅ 提供详细的错误诊断和修复建议
- ✅ 支持测试多个 agent

**使用方法**：
```bash
# 列出所有 socket
python test_guest_agent.py list

# 测试特定 agent
python test_guest_agent.py 0
python test_guest_agent.py 1
```

### 3. 文档

#### `GUEST_AGENT_SETUP.md`
- ✅ 完整的安装和配置指南
- ✅ Ubuntu/Debian 安装步骤
- ✅ 详细的故障排查指南
- ✅ 验证完成标准
- ✅ 参考资料链接

#### `QUICK_START.md`
- ✅ 快速启动步骤
- ✅ VM 重启方法（多种方式）
- ✅ 完整的验证流程
- ✅ 手动测试命令

---

## 🔍 当前状态分析

### VM 运行状态

**发现**：当前有 1 个 VM 正在运行
- **PID**：1897
- **Agent Index**：1
- **Agent ID**：7b053af9-a386-425f-8127-492bfc156525
- **配置**：旧版本（无 Guest Agent）

**Socket 文件**（当前）：
```
/var/folders/n3/_7qrtb716jg07p9d71216l3m0000gn/T/novaic/
├── novaic-mcp-1.sock  ← MCP 通信
└── novaic-qmp-1.sock  ← QEMU 管理
```

**期望状态**（重启后）：
```
/var/folders/n3/_7qrtb716jg07p9d71216l3m0000gn/T/novaic/
├── novaic-mcp-1.sock  ← MCP 通信
├── novaic-qmp-1.sock  ← QEMU 管理
└── novaic-ga-1.sock   ← Guest Agent（新增）✨
```

---

## 📝 下一步行动

### 必须完成的步骤

#### 1️⃣ 重启 VM（必需）

⚠️ **修改 QEMU 启动参数后，必须重启 VM 才能生效**

**推荐方法**（如果 Gateway 正在运行）：
```bash
# 通过 API 重启
curl -X POST http://localhost:8000/agents/{agent_id}/vm/stop
curl -X POST http://localhost:8000/agents/{agent_id}/vm/start
```

**备选方法**：
```bash
# 通过 SSH 优雅关机
ssh -p 20028 ubuntu@localhost sudo poweroff

# 等待关闭后，通过 Gateway 启动
```

#### 2️⃣ 验证 Socket 创建

```bash
ls -la /var/folders/n3/_7qrtb716jg07p9d71216l3m0000gn/T/novaic/

# 确认看到 novaic-ga-1.sock
```

#### 3️⃣ 安装 VM 内的 Guest Agent

```bash
# SSH 进入 VM
ssh -p 20028 ubuntu@localhost

# 安装
sudo apt-get update
sudo apt-get install -y qemu-guest-agent
sudo systemctl enable qemu-guest-agent
sudo systemctl start qemu-guest-agent

# 验证
sudo systemctl status qemu-guest-agent
ls -l /dev/virtio-ports/org.qemu.guest_agent.0

# 退出
exit
```

#### 4️⃣ 测试连接

```bash
cd novaic-backend/gateway/vm
python test_guest_agent.py 1
```

**期望输出**：
```
✅ Socket file exists
✅ guest-ping successful
✅ guest-info successful
✅ Guest Agent is working correctly!
```

---

## 📊 完成标准检查

| 标准 | 状态 | 说明 |
|------|------|------|
| QEMU 配置 Guest Agent 通道 | ✅ | 代码已修改，ARM64 和 x86_64 都已配置 |
| VM 重启应用新配置 | ⏳ | 等待执行 |
| VM 内 Guest Agent 服务运行 | ⏳ | 需要安装和启动 |
| 宿主机可通过 socket 通信 | ⏳ | 需要验证 |
| `guest-ping` 命令成功 | ⏳ | 需要测试 |
| `guest-info` 命令成功 | ⏳ | 需要测试 |

---

## 📁 相关文件

### 修改的文件
- ✅ `novaic-backend/gateway/vm/manager.py`

### 新建的文件
- ✅ `novaic-backend/gateway/vm/test_guest_agent.py` - 测试工具
- ✅ `novaic-backend/gateway/vm/GUEST_AGENT_SETUP.md` - 详细指南
- ✅ `novaic-backend/gateway/vm/QUICK_START.md` - 快速启动
- ✅ `PHASE_3_1_COMPLETION_REPORT.md` - 本报告

---

## 🎯 Phase 3 后续任务

完成 Phase 3.1 后，可以继续：

- **Phase 3.2**：实现文件操作 API
  - `guest-file-open`
  - `guest-file-read`
  - `guest-file-write`
  - `guest-file-close`

- **Phase 3.3**：实现命令执行 API
  - `guest-exec`
  - `guest-exec-status`

- **Phase 3.4**：集成到 vmcontrol 模块
  - 创建 Python wrapper
  - 提供统一的 API 接口
  - 错误处理和重试机制

---

## 🔗 参考资源

- [QEMU Guest Agent Protocol](https://wiki.qemu.org/Features/GuestAgent)
- [QGA Commands Reference](https://qemu.readthedocs.io/en/latest/interop/qemu-ga-ref.html)
- [Ubuntu qemu-guest-agent](https://packages.ubuntu.com/search?keywords=qemu-guest-agent)

---

## 💡 技术说明

### Guest Agent 通信架构

```
宿主机 (macOS)                    VM 内 (Ubuntu)
┌─────────────────┐              ┌──────────────────┐
│ Python 代码      │              │ qemu-guest-agent │
│                 │              │ 服务              │
└────────┬────────┘              └────────┬─────────┘
         │                                │
         │ Unix Socket                    │
         │ /tmp/novaic/                   │
         │ novaic-ga-*.sock               │
         │                                │
         └────────────────────────────────┘
                        │
                        ▼
                  QEMU virtio-serial
                  (/dev/virtio-ports/
                   org.qemu.guest_agent.0)
```

### Socket 命名规范

```
/tmp/novaic/novaic-{type}-{agent_index}.sock

类型：
- mcp: MCP 通信（virtio-serial）
- qmp: QEMU 管理（QMP 协议）
- ga: Guest Agent（QGA 协议）

示例：
- novaic-mcp-0.sock
- novaic-qmp-0.sock
- novaic-ga-0.sock
```

---

## ✅ 结论

**Phase 3.1 的代码工作已完成**。所有必要的配置已添加到 QEMU 启动参数中，并提供了完整的测试工具和文档。

**下一步**：重启 VM 并验证 Guest Agent 连接。参考 `QUICK_START.md` 进行操作。

---

**报告生成时间**：2026-02-06 14:22  
**生成工具**：Claude (Sonnet 4.5) in Cursor
