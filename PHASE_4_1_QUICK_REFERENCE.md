# Phase 4.1 - 快速参考卡片

**用于**: 快速查阅 VNC 配置和故障排查

---

## 🎯 核心结论

**当前架构**: VM 内部运行 x11vnc + websockify  
**QEMU 配置**: `-display none`（无 QEMU VNC）  
**连接方式**: WebSocket → 端口转发 → VM 服务  
**状态**: ✅ 完全可用，无需修改  
**推荐方案**: 保持现有架构 + 增强监控

---

## 📍 端口速查表

### Agent 0
```
VNC:       20006 → VM:5900
WebSocket: 20007 → VM:6080
SSH:       20008 → VM:22
MCP:       20000 → VM:8080
```

### Agent 1 (当前运行)
```
VNC:       20026 → VM:5900  ✅
WebSocket: 20027 → VM:6080  ✅
SSH:       20028 → VM:22    ✅
MCP:       20020 → VM:8080  ✅
```

### Agent N (通用公式)
```
Base = 20000 + (N * 20)
VNC:       Base + 6
WebSocket: Base + 7
SSH:       Base + 8
MCP:       Base + 0
```

---

## 🔍 快速检查命令

### 检查 QEMU 进程
```bash
ps aux | grep qemu-system | grep -v grep
```

### 检查端口监听（Agent 1）
```bash
lsof -i -P | grep LISTEN | grep '2002[0-9]'
# 预期输出:
# qemu-syst ... TCP *:20028 (SSH)
# qemu-syst ... TCP *:20027 (WebSocket)
# qemu-syst ... TCP *:20026 (VNC)
# qemu-syst ... TCP localhost:20020 (MCP)
```

### 测试 VNC 连接
```bash
nc -zv localhost 20026  # VNC
nc -zv localhost 20027  # WebSocket
```

### 检查 Socket 文件
```bash
ls -la /var/folders/.../T/novaic/*.sock
# 预期输出:
# novaic-qmp-1.sock   (QMP)
# novaic-ga-1.sock    (Guest Agent)
# novaic-mcp-1.sock   (MCP)
```

---

## 🔧 故障排查指南

### 问题 1: WebSocket 连接失败

**症状**: 前端显示 "VNC not connected"

**检查步骤**:
```bash
# 1. 检查端口监听
lsof -i:20027

# 2. 测试端口连接
nc -zv localhost 20027

# 3. 检查 QEMU 进程
ps aux | grep qemu-system
```

**可能原因**:
- ❌ QEMU 未启动 → 启动 VM: `POST /api/vm/start`
- ❌ websockify 崩溃 → 等待 systemd 自动重启（3 秒）
- ❌ 端口冲突 → 检查端口分配，重启 QEMU

**临时解决方案**:
```bash
# 通过 Guest Agent 重启 websockify (需要 Phase 4.2)
# 或 SSH 进入 VM
ssh -p 20028 ubuntu@localhost
sudo systemctl restart websockify
```

### 问题 2: VNC 黑屏

**症状**: WebSocket 已连接，但显示黑屏

**检查步骤**:
```bash
# 通过 SSH 进入 VM
ssh -p 20028 ubuntu@localhost

# 检查 X11 服务
systemctl status lightdm

# 检查 x11vnc
systemctl status x11vnc

# 检查显示环境变量
echo $DISPLAY  # 应该是 :0
```

**可能原因**:
- ❌ lightdm 未启动 → `sudo systemctl restart lightdm`
- ❌ x11vnc 崩溃 → `sudo systemctl restart x11vnc`
- ❌ X11 配置错误 → 检查 `/var/log/Xorg.0.log`

**临时解决方案**:
```bash
# 重启 X11 相关服务
sudo systemctl restart lightdm
sleep 10
sudo systemctl restart x11vnc
sudo systemctl restart websockify
```

### 问题 3: VM 无法启动

**症状**: `/api/vm/start` 返回错误

**检查步骤**:
```bash
# 1. 检查磁盘文件
ls -lh ~/Library/Application\ Support/com.novaic.app/agents/*/disk.qcow2

# 2. 检查端口占用
lsof -i:20026 -i:20027 -i:20028 -i:20020

# 3. 检查 QEMU 可用性
which qemu-system-aarch64
/opt/homebrew/bin/qemu-system-aarch64 --version
```

**可能原因**:
- ❌ 磁盘文件不存在 → 运行 Setup: `POST /api/vm/setup`
- ❌ 端口被占用 → 停止其他 VM，重新分配端口
- ❌ QEMU 未安装 → `brew install qemu`

### 问题 4: Guest Agent 不可用

**症状**: Guest Agent 命令超时

**检查步骤**:
```bash
# 1. 检查 Guest Agent Socket
ls -la /var/folders/.../novaic-ga-1.sock

# 2. SSH 进入 VM 检查
ssh -p 20028 ubuntu@localhost
systemctl status qemu-guest-agent

# 3. 测试 Guest Agent (Rust)
cd novaic-app/src-tauri/vmcontrol
cargo run --example guest_agent_demo
```

**可能原因**:
- ❌ Guest Agent 未安装 → cloud-init 配置错误
- ❌ Guest Agent 崩溃 → `sudo systemctl restart qemu-guest-agent`
- ❌ Socket 权限错误 → 检查 QEMU 启动参数

---

## 📂 关键文件位置

### 后端（Python）
```
novaic-backend/gateway/vm/
  ├── manager.py          # QEMU 启动和管理
  ├── setup.py            # cloud-init 配置
  └── vnc_monitor.py      # VNC 监控（待实现）

novaic-backend/gateway/config/
  └── agents.py           # 端口分配

novaic-backend/gateway/api/
  └── routes.py           # VNC API 端点
```

### 前端（TypeScript）
```
novaic-app/src/
  ├── components/Visual/VNCView.tsx  # VNC 组件
  └── services/vm.ts                 # VM 服务 API
```

### 控制层（Rust）
```
novaic-app/src-tauri/vmcontrol/src/
  ├── qemu/qmp.rs           # QMP 客户端
  ├── qemu/guest_agent.rs   # Guest Agent 客户端
  └── api/routes/screen.rs  # screendump API
```

---

## 🌐 API 端点速查

### VNC 相关
```
GET  /api/vnc/status?agent_id={id}
POST /api/vnc/start?agent_id={id}
POST /api/vnc/stop?agent_id={id}
```

### VM 管理
```
POST /api/vm/start
     Body: { agent_id, agent_index, memory, cpus }

POST /api/vm/stop
     Body: { agent_id, graceful }

GET  /api/vm/status/{agent_id}
GET  /api/vm/status              # 所有 VM

GET  /api/vm/running             # 运行中的 Agent
```

### vmcontrol (Rust API Server)
```
POST /api/screen/capture
     Body: { agent_id, format, output_path }

POST /api/input/send-key
     Body: { agent_id, key_code, down }

POST /api/input/send-mouse
     Body: { agent_id, button, down, x, y }
```

---

## 🔗 前端连接流程

```typescript
// 1. 启动 VM
await vmService.start(agentId, agentIndex);

// 2. 等待 Agent 服务
for (let i = 0; i < 30; i++) {
  const health = await fetch('/api/health');
  if (health.ok) break;
  await sleep(1000);
}

// 3. 获取 VNC URL
const wsUrl = await vmService.getVncUrl(agentId);
// 返回: ws://localhost:20027/websockify

// 4. 创建 RFB 连接
const rfb = new RFB(container, wsUrl, {
  shared: true,
  credentials: {},
});

// 5. 配置 RFB
rfb.scaleViewport = true;
rfb.clipViewport = true;
rfb.viewOnly = vncLocked;
```

---

## 🛡️ systemd 服务（VM 内部）

### lightdm (X11 Display Manager)
```bash
systemctl status lightdm
systemctl restart lightdm
journalctl -u lightdm -f
```

### x11vnc (VNC Server)
```bash
systemctl status x11vnc
systemctl restart x11vnc
journalctl -u x11vnc -f
```

### websockify (WebSocket Proxy)
```bash
systemctl status websockify
systemctl restart websockify
journalctl -u websockify -f
```

### qemu-guest-agent
```bash
systemctl status qemu-guest-agent
systemctl restart qemu-guest-agent
journalctl -u qemu-guest-agent -f
```

---

## 📊 性能指标

### 正常运行指标
```
VNC 帧率:    30-60 FPS
延迟:        50-200 ms
带宽:        1-5 Mbps (取决于活动内容)
CPU 占用:    10-30% (VM 内部)
内存占用:    ~4GB (VM 总内存)
```

### 异常指标
```
⚠️ 帧率 < 20 FPS      → 网络拥塞或 CPU 过载
⚠️ 延迟 > 500 ms      → 网络问题或服务崩溃
⚠️ CPU 占用 > 80%     → VM 负载过高
⚠️ 连接频繁断开       → websockify 不稳定
```

---

## 🚀 Phase 4 时间线

```
✅ Phase 4.1 (2h)   - VNC 配置调查
🔜 Phase 4.2 (4-6h) - VNC 健康监控
🔜 Phase 4.3 (3-4h) - VNC 配置管理
🔜 Phase 4.4 (2-3h) - 前端增强

总计: 11-15 小时
```

---

## 📞 紧急联系

**QEMU 进程意外退出**:
```bash
# 检查退出原因
tail -n 50 /path/to/qemu.log

# 重启 VM
curl -X POST http://localhost:19999/api/vm/start \
  -H "Content-Type: application/json" \
  -d '{"agent_id":"xxx","agent_index":1}'
```

**所有服务无响应**:
```bash
# 检查 Gateway 是否运行
curl http://localhost:19999/api/health

# 重启 Gateway
pkill -f "python.*main.py"
python novaic-backend/main.py
```

---

## 📚 完整文档链接

- [详细报告](./PHASE_4_1_VNC_INVESTIGATION_REPORT.md) - 完整技术分析
- [架构图](./PHASE_4_1_ARCHITECTURE_DIAGRAM.md) - 可视化架构
- [执行摘要](./PHASE_4_1_EXECUTIVE_SUMMARY.md) - 高层次总结
- [本参考卡片](./PHASE_4_1_QUICK_REFERENCE.md) - 快速查阅

---

**版本**: 1.0  
**更新日期**: 2026-02-06  
**维护者**: NovAIC Backend Team
