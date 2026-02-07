# Phase 4.1 - NovAIC VNC 架构图

## 系统架构总览

```
┌─────────────────────────────────────────────────────────────────────────┐
│                            用户浏览器 (Frontend)                          │
│                                                                           │
│  ┌─────────────────────────────────────────────────────────────────┐    │
│  │                      VNCView.tsx                                 │    │
│  │  ┌──────────────────────────────────────────────────────────┐   │    │
│  │  │  noVNC RFB Client                                        │   │    │
│  │  │  - WebSocket: ws://localhost:20027/websockify          │   │    │
│  │  │  - 实时视频流                                           │   │    │
│  │  │  - 键盘鼠标交互                                         │   │    │
│  │  └──────────────────────────────────────────────────────────┘   │    │
│  │                                                                  │    │
│  │  ┌──────────────────────────────────────────────────────────┐   │    │
│  │  │  VM Service (vm.ts)                                      │   │    │
│  │  │  - getVncUrl(agentId) → Gateway API                     │   │    │
│  │  │  - getStatus(agentId) → VM 状态                         │   │    │
│  │  └──────────────────────────────────────────────────────────┘   │    │
│  └─────────────────────────────────────────────────────────────────┘    │
└────────────────────────────┬────────────────────────────────────────────┘
                             │ HTTP/WebSocket
                             ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                     宿主机 (macOS Host)                                   │
│                                                                           │
│  ┌─────────────────────────────────────────────────────────────────┐    │
│  │                    Gateway (Python)                              │    │
│  │                    Port: 19999                                   │    │
│  │                                                                  │    │
│  │  API 端点:                                                        │    │
│  │  - GET  /api/vnc/status?agent_id=xxx                           │    │
│  │  - POST /api/vnc/start?agent_id=xxx                            │    │
│  │  - GET  /api/vm/status/{agent_id}                              │    │
│  │  - POST /api/vm/start                                           │    │
│  │                                                                  │    │
│  │  ┌────────────────────────────────────────────────────────┐     │    │
│  │  │  VM Manager (manager.py)                               │     │    │
│  │  │  - 启动/停止 QEMU                                      │     │    │
│  │  │  - 端口分配和检查                                      │     │    │
│  │  │  - 进程监控和恢复                                      │     │    │
│  │  └────────────────────────────────────────────────────────┘     │    │
│  └─────────────────────────────────────────────────────────────────┘    │
│                                                                           │
│  ┌─────────────────────────────────────────────────────────────────┐    │
│  │                 QEMU 进程 (Agent 1)                              │    │
│  │                 PID: 5980                                        │    │
│  │                                                                  │    │
│  │  命令行参数:                                                      │    │
│  │  qemu-system-aarch64                                            │    │
│  │    -name novaic-vm-1                                            │    │
│  │    -M virt,highmem=on -cpu host -accel hvf                     │    │
│  │    -m 4096 -smp 4                                              │    │
│  │    -display none            ← ⚠️ 无 QEMU VNC                    │    │
│  │    -device virtio-gpu-pci                                       │    │
│  │                                                                  │    │
│  │  端口转发 (user networking):                                     │    │
│  │    VM:5900  → Host:20026   (x11vnc)                           │    │
│  │    VM:6080  → Host:20027   (websockify) ← 前端连接这里          │    │
│  │    VM:22    → Host:20028   (SSH)                              │    │
│  │    VM:8080  → Host:20020   (MCP)                              │    │
│  │                                                                  │    │
│  │  Unix Sockets:                                                  │    │
│  │    /var/folders/.../novaic-qmp-1.sock     (QMP 控制)          │    │
│  │    /var/folders/.../novaic-ga-1.sock      (Guest Agent)        │    │
│  │    /var/folders/.../novaic-mcp-1.sock     (MCP)                │    │
│  │                                                                  │    │
│  └───────────────────────┬─────────────────────────────────────────┘    │
│                          │                                               │
│                          │ QEMU User Networking                         │
│                          │ (端口转发)                                    │
│                          ▼                                               │
│  ┌─────────────────────────────────────────────────────────────────┐    │
│  │                    虚拟机 (Ubuntu 24.04)                          │    │
│  │                                                                  │    │
│  │  ┌────────────────────────────────────────────────────────┐     │    │
│  │  │  X11 Desktop (LightDM + LXDE)                         │     │    │
│  │  │  DISPLAY=:0                                            │     │    │
│  │  │  分辨率: 1920x1080                                     │     │    │
│  │  └────────────────────────────────────────────────────────┘     │    │
│  │                          │                                       │    │
│  │                          │ X11 协议                              │    │
│  │                          ▼                                       │    │
│  │  ┌────────────────────────────────────────────────────────┐     │    │
│  │  │  x11vnc (systemd 服务)                                │     │    │
│  │  │  监听: 0.0.0.0:5900                                   │     │    │
│  │  │  命令: /usr/bin/x11vnc -forever -shared               │     │    │
│  │  │        -rfbport 5900 -display :0                      │     │    │
│  │  │  状态: ✅ Running                                      │     │    │
│  │  └────────────────────────────────────────────────────────┘     │    │
│  │                          │                                       │    │
│  │                          │ RFB 协议 (TCP)                        │    │
│  │                          ▼                                       │    │
│  │  ┌────────────────────────────────────────────────────────┐     │    │
│  │  │  websockify (systemd 服务)                            │     │    │
│  │  │  监听: 0.0.0.0:6080                                   │     │    │
│  │  │  代理: localhost:5900                                  │     │    │
│  │  │  命令: /usr/bin/websockify 6080 localhost:5900       │     │    │
│  │  │  状态: ✅ Running                                      │     │    │
│  │  └────────────────────────────────────────────────────────┘     │    │
│  │                          │                                       │    │
│  │                          │ WebSocket (TCP)                       │    │
│  │                          ▼                                       │    │
│  │  ┌────────────────────────────────────────────────────────┐     │    │
│  │  │  QEMU Guest Agent (systemd 服务)                      │     │    │
│  │  │  Socket: /dev/virtio-ports/org.qemu.guest_agent.0    │     │    │
│  │  │  功能: 文件操作、命令执行、网络查询                   │     │    │
│  │  │  状态: ✅ Running                                      │     │    │
│  │  └────────────────────────────────────────────────────────┘     │    │
│  │                                                                  │    │
│  └─────────────────────────────────────────────────────────────────┘    │
└─────────────────────────────────────────────────────────────────────────┘
```

## 数据流详解

### 1. VNC 视频流（实时）

```
用户浏览器
    │
    │ WebSocket 连接
    │ ws://localhost:20027/websockify
    ▼
宿主机 Port 20027
    │
    │ QEMU 端口转发
    │ (user networking)
    ▼
VM Port 6080 (websockify)
    │
    │ WebSocket → TCP 转换
    │ RFB 协议
    ▼
VM Port 5900 (x11vnc)
    │
    │ RFB 编码
    │ X11 协议
    ▼
VM X11 Display :0
    │
    │ 渲染
    ▼
Linux Desktop (LXDE)
```

**特点**：
- ✅ 实时流媒体（30-60 FPS）
- ✅ 双向交互（键盘、鼠标）
- ⚠️ 依赖 VM 内部服务

### 2. QMP 控制流（命令）

```
Gateway/vmcontrol
    │
    │ Unix Socket
    │ /var/folders/.../novaic-qmp-1.sock
    ▼
QEMU QMP 服务器
    │
    │ QMP 协议
    │ {"execute": "screendump", "arguments": {...}}
    ▼
QEMU 内部
    │
    │ 虚拟 GPU 帧缓冲
    ▼
截图文件 (PPM/PNG)
```

**特点**：
- ✅ 独立于 VM 内部
- ✅ 不依赖 Guest OS
- ⚠️ 仅单次截图，非实时

### 3. Guest Agent 流（Guest 操作）

```
Gateway/vmcontrol
    │
    │ Unix Socket
    │ /var/folders/.../novaic-ga-1.sock
    ▼
QEMU virtio-serial
    │
    │ virtserialport
    │ /dev/virtio-ports/org.qemu.guest_agent.0
    ▼
VM Guest Agent (qemu-ga)
    │
    │ JSON-RPC
    │ {"execute": "guest-exec", "arguments": {...}}
    ▼
Guest OS (Ubuntu)
    │
    │ 命令执行
    ▼
文件操作/进程管理/网络查询
```

**特点**：
- ✅ Guest 内部操作
- ✅ 可重启 VNC 服务
- ⚠️ 需要 Guest Agent 运行

## 端口分配表

### Agent 0 (默认 Agent)
| 服务 | VM 端口 | 宿主机端口 | 协议 | 状态 |
|------|---------|-----------|------|------|
| MCP | 8080 | 20000 | HTTP | - |
| VNC | 5900 | 20006 | RFB | - |
| WebSocket | 6080 | 20007 | WS | - |
| SSH | 22 | 20008 | SSH | - |

### Agent 1 (当前运行)
| 服务 | VM 端口 | 宿主机端口 | 协议 | 状态 |
|------|---------|-----------|------|------|
| MCP | 8080 | 20020 | HTTP | ✅ LISTEN |
| VNC | 5900 | 20026 | RFB | ✅ LISTEN |
| WebSocket | 6080 | 20027 | WS | ✅ LISTEN |
| SSH | 22 | 20028 | SSH | ✅ LISTEN |

### Agent 2 (示例)
| 服务 | VM 端口 | 宿主机端口 | 协议 | 状态 |
|------|---------|-----------|------|------|
| MCP | 8080 | 20040 | HTTP | - |
| VNC | 5900 | 20046 | RFB | - |
| WebSocket | 6080 | 20047 | WS | - |
| SSH | 22 | 20048 | SSH | - |

**端口计算公式**：
```
宿主机端口 = 20000 + (agent_index * 20) + service_offset

service_offset:
  - vm (MCP): 0
  - session: 1
  - local: 2
  - memory: 3
  - chat: 4
  - qemudebug: 5
  - vnc: 6
  - websocket: 7
  - ssh: 8
```

## 服务依赖关系

```
启动顺序:
1. QEMU 进程启动
   └─> QMP Socket 就绪
   └─> Guest Agent Socket 就绪
   └─> MCP Socket 就绪

2. VM 内部启动 (cloud-init + systemd)
   ├─> lightdm.service (X11 Display Manager)
   │   └─> DISPLAY=:0 启动
   │       └─> LXDE Desktop 渲染
   │
   ├─> x11vnc.service (依赖 lightdm)
   │   └─> 监听 VM:5900
   │       └─> 端口转发到 Host:20026
   │
   ├─> websockify.service (依赖 x11vnc)
   │   └─> 监听 VM:6080
   │       └─> 端口转发到 Host:20027
   │
   └─> qemu-guest-agent.service
       └─> 连接 /dev/virtio-ports/org.qemu.guest_agent.0
           └─> 通过 Guest Agent Socket 与宿主机通信

3. 前端连接
   ├─> 查询 Gateway API (/api/vm/status)
   │   └─> 获取 vnc_url: ws://localhost:20027/websockify
   │
   └─> 创建 WebSocket 连接
       └─> noVNC RFB 握手
           └─> 实时视频流开始
```

## 故障点和恢复策略

### 故障点 1: lightdm 崩溃
**症状**：X11 Display 丢失，x11vnc 无法连接  
**检测**：Guest Agent 检查 `systemctl is-active lightdm`  
**恢复**：Guest Agent 执行 `systemctl restart lightdm`  
**影响时间**：10-15 秒

### 故障点 2: x11vnc 崩溃
**症状**：VNC 端口 (20026) 不可访问  
**检测**：Gateway 端口检查失败  
**恢复**：Guest Agent 执行 `systemctl restart x11vnc`  
**影响时间**：2-3 秒

### 故障点 3: websockify 崩溃
**症状**：WebSocket (20027) 连接失败  
**检测**：前端 WebSocket 握手失败  
**恢复**：Guest Agent 执行 `systemctl restart websockify`  
**影响时间**：2-3 秒

### 故障点 4: QEMU 进程崩溃
**症状**：所有端口不可访问，VM 完全停止  
**检测**：PID 检查失败  
**恢复**：Gateway VM Manager 重启 QEMU  
**影响时间**：60-120 秒（完整启动）

### 故障点 5: Guest Agent 崩溃
**症状**：无法通过 Guest Agent 操作 VM  
**检测**：Guest Agent 命令超时  
**恢复**：通过 SSH 或手动重启 `qemu-guest-agent`  
**影响时间**：5-10 秒

## Phase 4.2 监控架构

```
┌─────────────────────────────────────────────────────────────┐
│                   Gateway VNC Monitor                        │
│                   (vnc_monitor.py)                           │
│                                                              │
│  ┌────────────────────────────────────────────────────┐     │
│  │  定期健康检查 (每 30 秒)                           │     │
│  │                                                     │     │
│  │  1. 检查宿主机端口                                  │     │
│  │     - nc -zv localhost 20026 (VNC)                │     │
│  │     - nc -zv localhost 20027 (WebSocket)          │     │
│  │                                                     │     │
│  │  2. 通过 Guest Agent 检查进程                       │     │
│  │     - guest_exec("pgrep x11vnc")                  │     │
│  │     - guest_exec("pgrep websockify")              │     │
│  │     - guest_exec("systemctl is-active lightdm")   │     │
│  │                                                     │     │
│  │  3. 故障检测和自动恢复                              │     │
│  │     if not vnc_ok:                                │     │
│  │       guest_exec("systemctl restart x11vnc")      │     │
│  │     if not ws_ok:                                 │     │
│  │       guest_exec("systemctl restart websockify")  │     │
│  │                                                     │     │
│  │  4. 记录健康状态到数据库                            │     │
│  │     - vnc_health 表                                │     │
│  │     - 异常事件日志                                  │     │
│  └────────────────────────────────────────────────────┘     │
└─────────────────────────────────────────────────────────────┘
                          │
                          │ HTTP API
                          ▼
┌─────────────────────────────────────────────────────────────┐
│                   Frontend Status Display                    │
│                   (VNCView.tsx)                              │
│                                                              │
│  ┌────────────────────────────────────────────────────┐     │
│  │  实时状态指示器                                     │     │
│  │                                                     │     │
│  │  🟢 VNC: Running                                   │     │
│  │  🟢 WebSocket: Running                             │     │
│  │  🟢 X11: Active                                    │     │
│  │                                                     │     │
│  │  [Refresh] [Recover] [Settings]                   │     │
│  └────────────────────────────────────────────────────┘     │
└─────────────────────────────────────────────────────────────┘
```

---

**图表说明**：
- ✅ = 服务运行中
- ⚠️ = 警告或限制
- ❌ = 不可用或不推荐
- 🟢 = 健康状态良好
- 🟡 = 中等风险
- 🔴 = 高风险

**最后更新**: 2026-02-06
