# Phase 4.1 - QEMU VNC 配置调查报告

**日期**: 2026-02-06  
**状态**: ✅ 调查完成

---

## 执行摘要

完成了对 NovAIC 系统当前 VNC 配置的全面调查，明确了现有架构、工作原理和 Phase 4 实现路径。

**关键发现**：
- ✅ QEMU 本身**不提供 VNC**（使用 `-display none`）
- ✅ VNC 服务运行在 **VM 内部**（x11vnc + websockify）
- ✅ 通过 **QEMU 端口转发** 暴露到宿主机
- ✅ QMP Socket 和 Guest Agent 已配置完成
- ✅ Phase 2 screendump 功能已实现

---

## 1. 当前 VNC 架构

### 1.1 QEMU 配置（宿主机）

**QEMU 进程参数**（Agent 1 示例）：
```bash
/opt/homebrew/bin/qemu-system-aarch64 \
  -name novaic-vm-1 \
  -M virt,highmem=on \
  -cpu host \
  -accel hvf \
  -m 4096 \
  -smp 4 \
  # 端口转发配置
  -netdev user,id=net0,\
    hostfwd=tcp::20026-:5900,\      # VNC (x11vnc)
    hostfwd=tcp::20027-:6080,\      # WebSocket (websockify)
    hostfwd=tcp::20028-:22,\        # SSH
    hostfwd=tcp:127.0.0.1:20020-:8080 \  # MCP
  # QMP 和 Guest Agent
  -qmp unix:/var/folders/.../novaic-qmp-1.sock,server,nowait \
  -chardev socket,path=/var/folders/.../novaic-ga-1.sock,server=on,wait=off,id=qga0 \
  -device virtserialport,chardev=qga0,name=org.qemu.guest_agent.0 \
  # 显示配置
  -display none \  # ⚠️ 无 QEMU VNC！
  -device virtio-gpu-pci
```

**关键配置**：
- ❌ **无 `-vnc` 参数** - QEMU 本身不提供 VNC
- ✅ **端口转发** - VM:5900 → Host:20026, VM:6080 → Host:20027
- ✅ **QMP Socket** - 用于 VM 控制（已实现 screendump）
- ✅ **Guest Agent** - 用于 Guest 内部操作

**代码位置**：`novaic-backend/gateway/vm/manager.py`
```python
# 第 545 行（ARM64）和 第 601 行（x86_64）
"-display", "none",
```

### 1.2 VM 内部服务

**systemd 服务配置**（cloud-init）：

#### x11vnc 服务
```systemd
[Unit]
Description=X11 VNC Server
After=lightdm.service

[Service]
Type=simple
User=ubuntu
Environment=DISPLAY=:0
ExecStart=/usr/bin/x11vnc -forever -shared -rfbport 5900 -display :0
Restart=always
RestartSec=3
```
- 监听端口：**5900**（VM 内部）
- 暴露端口：**20026**（宿主机，Agent 1）
- 状态：✅ **运行中**（已验证）

#### websockify 服务
```systemd
[Unit]
Description=Websockify VNC WebSocket Proxy
After=x11vnc.service
Requires=x11vnc.service

[Service]
Type=simple
User=ubuntu
ExecStart=/usr/bin/websockify 6080 localhost:5900
Restart=always
RestartSec=3
```
- 监听端口：**6080**（VM 内部）
- 代理目标：`localhost:5900` (x11vnc)
- 暴露端口：**20027**（宿主机，Agent 1）
- 状态：✅ **运行中**（已验证）

**代码位置**：`novaic-backend/gateway/vm/setup.py` (第 468-596 行)

### 1.3 前端 VNC 客户端

**技术栈**：
- 库：`novnc-rfb` (noVNC RFB 协议实现)
- 连接方式：WebSocket
- URL：从 Gateway API 动态获取

**连接流程**（VNCView.tsx）：
```typescript
// 1. 获取 WebSocket URL
const wsUrl = await vmService.getVncUrl(currentAgentId);
// 返回：ws://localhost:20027/websockify

// 2. 创建 RFB 连接
const rfb = new RFB(container, wsUrl, {
  shared: true,
  credentials: {},
});

// 3. 配置 RFB
rfb.scaleViewport = true;
rfb.clipViewport = true;
rfb.resizeSession = false;
rfb.focusOnClick = true;
rfb.viewOnly = vncLocked;
```

**代码位置**：
- 前端组件：`novaic-app/src/components/Visual/VNCView.tsx`
- VM 服务：`novaic-app/src/services/vm.ts` (第 162-174 行)

### 1.4 Gateway API

**VNC 状态查询**：
```http
GET /api/vnc/status?agent_id={agent_id}

Response:
{
  "running": true,           // x11vnc 可用
  "websockify_running": true, // websockify 可用
  "port": 20026,             // VNC 端口
  "ws_port": 20027,          // WebSocket 端口
  "ready": true              // 整体就绪
}
```

**代码位置**：`novaic-backend/gateway/api/routes.py` (第 896-909 行)

---

## 2. 端口分配方案

### 2.1 端口布局

```
19999         - Gateway (固定)
20000-21999   - Agents (100个 × 20端口)

每个 Agent 端口布局（Agent N = 20000 + N*20）：
  Offset 0: VM (MCP)        - 20000, 20020, 20040...
  Offset 1: Session MCP     - 20001, 20021, 20041...
  Offset 2: Local MCP       - 20002, 20022, 20042...
  Offset 3: Memory MCP      - 20003, 20023, 20043...
  Offset 4: Chat MCP        - 20004, 20024, 20044...
  Offset 5: QEMU Debug      - 20005, 20025, 20045...
  Offset 6: VNC             - 20006, 20026, 20046...
  Offset 7: WebSocket       - 20007, 20027, 20047...
  Offset 8: SSH             - 20008, 20028, 20048...
  Offset 9-19: 预留
```

**验证**（Agent 1，index=1）：
```bash
$ lsof -i -P | grep qemu | grep LISTEN
qemu-syst  5980  ... TCP localhost:20020 (LISTEN)  # MCP
qemu-syst  5980  ... TCP *:20028 (LISTEN)          # SSH
qemu-syst  5980  ... TCP *:20027 (LISTEN)          # WebSocket
qemu-syst  5980  ... TCP *:20026 (LISTEN)          # VNC
```

**代码位置**：`novaic-backend/gateway/config/agents.py` (第 87-156 行)

### 2.2 连接测试

```bash
# VNC 端口（x11vnc）
$ nc -zv localhost 20026
Connection to localhost port 20026 [tcp/*] succeeded!

# WebSocket 端口（websockify）
$ nc -zv localhost 20027
Connection to localhost port 20027 [tcp/*] succeeded!
```

✅ **结论**：VNC 服务完全可访问

---

## 3. QMP 和 Guest Agent 状态

### 3.1 QMP Socket

**位置**：`/var/folders/.../T/novaic/novaic-qmp-{agent_index}.sock`

**已实现功能**（vmcontrol crate）：
```rust
// 虚拟机控制
qmp_client.stop().await?;           // 暂停
qmp_client.cont().await?;           // 恢复
qmp_client.system_powerdown().await?; // 关机
qmp_client.quit().await?;           // 强制退出

// 屏幕截图（Phase 2）
qmp_client.screendump("/tmp/screen.ppm").await?;
```

**代码位置**：`novaic-app/src-tauri/vmcontrol/src/qemu/qmp.rs`

### 3.2 Guest Agent Socket

**位置**：`/var/folders/.../T/novaic/novaic-ga-{agent_index}.sock`

**已实现功能**（vmcontrol crate）：
```rust
// Guest 信息查询
ga_client.guest_info().await?;
ga_client.guest_network_get_interfaces().await?;

// 文件操作
ga_client.guest_file_open(path, "r").await?;
ga_client.guest_file_read(handle, 4096).await?;
ga_client.guest_file_close(handle).await?;

// 命令执行
ga_client.guest_exec("/bin/ls", ["-la"], env).await?;
ga_client.guest_exec_status(pid).await?;
```

**代码位置**：
- Rust 库：`novaic-app/src-tauri/vmcontrol/src/qemu/guest_agent.rs`
- Python 测试：`novaic-backend/gateway/vm/test_guest_agent.py`

---

## 4. Phase 4 实现方案评估

### 方案对比

| 方案 | 优点 | 缺点 | 实施难度 |
|------|------|------|----------|
| **A. 保持现有架构**<br>（VM 内 x11vnc + websockify） | ✅ 无需修改 QEMU<br>✅ 已经工作正常<br>✅ WebSocket 原生支持 | ⚠️ 依赖 VM 内服务<br>⚠️ 需要维护 systemd 配置 | 🟢 低（已完成） |
| **B. 添加 QEMU VNC**<br>（`-vnc unix:/path/to.vnc`） | ✅ 独立于 VM<br>✅ 更底层的控制 | ❌ 需要 WebSocket 代理<br>❌ Unix Socket 权限管理<br>❌ 可能与 x11vnc 冲突 | 🟡 中 |
| **C. QEMU VNC TCP**<br>（`-vnc :0`） | ✅ 简单直接 | ❌ 需要额外端口<br>❌ 安全性较低<br>❌ 端口冲突风险 | 🟢 低 |
| **D. 纯 QMP screendump**<br>（轮询截图） | ✅ 已实现（Phase 2）<br>✅ 无额外服务 | ❌ 不是实时流<br>❌ 延迟高<br>❌ 无交互 | 🟢 低（已完成） |

### 推荐方案：**方案 A（保持现有架构）+ 增强**

**理由**：
1. ✅ **已经工作正常** - VNC 和 WebSocket 都可访问
2. ✅ **无需修改 QEMU** - 避免引入新的复杂性
3. ✅ **WebSocket 原生支持** - 前端直接连接，无需代理
4. ✅ **systemd 管理** - 自动重启，稳定可靠

**增强建议**（Phase 4.2-4.3）：
1. **添加 VNC 健康检查**
   - 监控 x11vnc 和 websockify 进程状态
   - 异常时通过 Guest Agent 重启服务

2. **添加 VNC 配置管理**
   - 通过 Guest Agent 动态调整分辨率
   - 配置密码保护（可选）

3. **前端增强**
   - 添加连接重试逻辑
   - 显示 VNC 服务状态
   - 集成 screendump 作为 fallback

---

## 5. 与现有系统的兼容性

### 5.1 Gateway VM Manager

**启动流程**（`manager.py`）：
```python
# 1. 启动 QEMU
process = subprocess.Popen(qemu_cmd)

# 2. 等待 VM 启动
time.sleep(5)

# 3. 等待 websockify
self._wait_for_service(ports.websocket, "websockify", timeout=60)

# 4. 等待 MCP
self._wait_for_service(ports.vm, "MCP", timeout=120)
```

**兼容性**：✅ 完全兼容
- VNC 服务由 VM 内部 systemd 自动启动
- Gateway 通过端口检查确认就绪

### 5.2 前端 VNC 组件

**启动流程**（`VNCView.tsx`）：
```typescript
// 1. 启动 QEMU VM
await vmService.start(agentId, agentIndex);

// 2. 等待 Agent 服务
for (let i = 0; i < 30; i++) {
  const healthRes = await fetch('/api/health');
  if (healthRes.ok) break;
}

// 3. 调用 /api/vnc/start
await fetch('/api/vnc/start?agent_id=' + agentId, { method: 'POST' });

// 4. 轮询 WebSocket 就绪
for (let i = 0; i < 20; i++) {
  const ws = new WebSocket(wsUrl);
  // ...
}

// 5. 创建 RFB 连接
const rfb = new RFB(container, wsUrl);
```

**兼容性**：✅ 完全兼容
- `/api/vnc/start` 仅检查端口状态，不启动服务
- 轮询机制确保 WebSocket 就绪

### 5.3 多 Agent 支持

**端口隔离**：
- Agent 0: VNC=20006, WS=20007
- Agent 1: VNC=20026, WS=20027
- Agent 2: VNC=20046, WS=20047
- ...

**状态管理**：
- 每个 Agent 独立的 VM 进程
- 独立的端口和 Socket
- 数据库持久化状态

**兼容性**：✅ 完全支持多 Agent

---

## 6. Phase 2 集成现状

### 6.1 QMP screendump 功能

**已实现**（vmcontrol API Server）：
```rust
// POST /api/screen/capture
// Body: { "agent_id": "xxx", "format": "png", "output_path": "/tmp/screen.png" }

async fn capture_screen(data: ScreenCaptureRequest) -> Result<ScreenCaptureResponse> {
    let qmp_socket = format!("/tmp/novaic/novaic-qmp-{}.sock", agent_index);
    let mut client = QmpClient::connect(&qmp_socket).await?;
    
    // 截图到临时文件（PPM 格式）
    client.screendump(&ppm_path).await?;
    
    // 转换为 PNG
    convert_ppm_to_png(&ppm_path, &png_path)?;
    
    Ok(ScreenCaptureResponse { path: png_path })
}
```

**代码位置**：`novaic-app/src-tauri/vmcontrol/src/api/routes/screen.rs`

### 6.2 与 VNC 的关系

| 功能 | VNC (实时) | screendump (静态) | 使用场景 |
|------|-----------|------------------|---------|
| 刷新率 | 实时（30-60 FPS） | 按需（手动触发） | VNC: 交互；screendump: 记录 |
| 网络开销 | 持续 | 单次 | VNC: 稳定网络；screendump: 离线 |
| 交互性 | ✅ 键盘鼠标 | ❌ 只读 | VNC: 操作；screendump: 展示 |
| 资源占用 | 中等（GPU 渲染） | 低（单次 QMP） | VNC: 长期使用；screendump: 轻量检查 |

**结论**：VNC 和 screendump **互补**，不冲突

---

## 7. 风险评估

### 7.1 当前架构风险

| 风险 | 级别 | 影响 | 缓解措施 |
|------|------|------|---------|
| VM 内服务故障 | 🟡 中 | VNC 不可用 | ✅ systemd 自动重启<br>✅ 添加 Guest Agent 监控 |
| websockify 崩溃 | 🟡 中 | 前端无法连接 | ✅ systemd 自动重启<br>✅ 前端重连逻辑 |
| 端口冲突 | 🟢 低 | 启动失败 | ✅ 端口分配算法<br>✅ 启动前检查 |
| X11 服务异常 | 🟡 中 | 黑屏 | ✅ lightdm 自动重启<br>✅ screendump fallback |

### 7.2 修改 QEMU 配置的风险

**如果添加 QEMU VNC**（不推荐）：
- 🔴 **高风险**：与现有 x11vnc 冲突
- 🔴 **高风险**：需要同步修改多处代码
- 🔴 **高风险**：破坏现有稳定架构

**建议**：❌ **不修改 QEMU VNC 配置**

---

## 8. Phase 4 实现路线图

### Phase 4.1 ✅ 配置调查（本阶段）
- ✅ 理解当前 VNC 架构
- ✅ 验证端口可访问性
- ✅ 确认 QMP/Guest Agent 状态
- ✅ 制定实现方案

### Phase 4.2 🔜 VNC 健康监控
**目标**：确保 VNC 服务稳定运行

**任务**：
1. Gateway 端监控
   ```python
   # gateway/vm/vnc_monitor.py
   async def check_vnc_health(agent_id: str) -> VncHealth:
       # 检查 x11vnc 和 websockify 端口
       vnc_ok = await check_port(ports.vnc)
       ws_ok = await check_port(ports.websocket)
       
       # 通过 Guest Agent 检查进程状态
       ga = GuestAgentClient(ga_socket)
       x11vnc_pid = await ga.guest_exec("pgrep x11vnc")
       websockify_pid = await ga.guest_exec("pgrep websockify")
       
       return VncHealth(vnc_ok, ws_ok, x11vnc_pid, websockify_pid)
   ```

2. 自动恢复
   ```python
   async def recover_vnc(agent_id: str):
       ga = GuestAgentClient(ga_socket)
       await ga.guest_exec("systemctl restart x11vnc")
       await ga.guest_exec("systemctl restart websockify")
   ```

3. 前端状态显示
   ```typescript
   // VNCView.tsx
   const health = await vmService.getVncHealth(agentId);
   if (!health.vnc_ok) {
     // 显示警告，尝试恢复
     await vmService.recoverVnc(agentId);
   }
   ```

**完成标准**：
- ✅ 自动检测 VNC 服务故障
- ✅ 自动恢复失败的服务
- ✅ 前端显示健康状态

### Phase 4.3 🔜 VNC 配置管理
**目标**：动态管理 VNC 配置

**任务**：
1. 分辨率调整
   ```python
   # 通过 Guest Agent 调用 xrandr
   async def set_resolution(agent_id: str, width: int, height: int):
       ga = GuestAgentClient(ga_socket)
       await ga.guest_exec(f"xrandr --output Virtual-1 --mode {width}x{height}")
   ```

2. VNC 密码管理（可选）
   ```python
   # 通过 Guest Agent 配置 x11vnc 密码
   async def set_vnc_password(agent_id: str, password: str):
       ga = GuestAgentClient(ga_socket)
       # 生成密码文件
       await ga.guest_file_write("/home/ubuntu/.vnc/passwd", encrypted_password)
       # 重启 x11vnc
       await ga.guest_exec("systemctl restart x11vnc")
   ```

3. 前端配置界面
   ```typescript
   // Settings -> VNC
   <select onChange={(e) => vmService.setVncResolution(agentId, e.target.value)}>
     <option value="1920x1080">1920x1080</option>
     <option value="1280x720">1280x720</option>
   </select>
   ```

**完成标准**：
- ✅ 支持动态调整分辨率
- ✅ 支持 VNC 密码保护（可选）
- ✅ 前端配置界面

### Phase 4.4 🔜 前端增强
**目标**：提升 VNC 用户体验

**任务**：
1. 连接重试逻辑
   ```typescript
   async function connectWithRetry(wsUrl: string, maxRetries: number = 5) {
     for (let i = 0; i < maxRetries; i++) {
       try {
         const rfb = new RFB(container, wsUrl);
         return rfb;
       } catch (e) {
         if (i === maxRetries - 1) throw e;
         await sleep(2000 * Math.pow(2, i)); // 指数退避
       }
     }
   }
   ```

2. screendump fallback
   ```typescript
   if (!vncConnected) {
     // 使用 screendump 作为降级方案
     const screenshot = await vmService.captureScreen(agentId);
     setFallbackImage(screenshot);
   }
   ```

3. 性能优化
   ```typescript
   // 根据网络条件调整 VNC 质量
   rfb.qualityLevel = getNetworkQuality() > 0.8 ? 9 : 6;
   rfb.compressionLevel = getNetworkQuality() > 0.8 ? 0 : 9;
   ```

**完成标准**：
- ✅ 连接失败自动重试
- ✅ screendump 作为 fallback
- ✅ 性能优化

---

## 9. 推荐的后续步骤

### 立即行动（Phase 4.2）
1. **实现 VNC 健康监控**
   - 添加 `gateway/vm/vnc_monitor.py`
   - 集成到 VM Manager
   - 前端显示健康状态

2. **添加自动恢复机制**
   - 检测 x11vnc/websockify 故障
   - 通过 Guest Agent 重启服务
   - 记录恢复日志

### 短期目标（Phase 4.3）
1. **VNC 配置管理**
   - 分辨率动态调整
   - 密码保护（可选）
   - 前端配置界面

2. **文档完善**
   - VNC 故障排查指南
   - Guest Agent 使用文档
   - 端口分配说明

### 长期优化（Phase 4.4+）
1. **前端体验提升**
   - 连接重试
   - screendump fallback
   - 性能优化

2. **监控和日志**
   - VNC 连接统计
   - 性能指标收集
   - 异常告警

---

## 10. 附录

### 10.1 关键文件清单

| 文件路径 | 作用 | 关键行 |
|---------|------|-------|
| `novaic-backend/gateway/vm/manager.py` | QEMU 启动配置 | 455-607 |
| `novaic-backend/gateway/vm/setup.py` | cloud-init VNC 配置 | 465-597 |
| `novaic-backend/gateway/api/routes.py` | VNC API 端点 | 896-954 |
| `novaic-backend/gateway/config/agents.py` | 端口分配 | 87-156 |
| `novaic-app/src/components/Visual/VNCView.tsx` | 前端 VNC 组件 | 1-740 |
| `novaic-app/src/services/vm.ts` | VM 服务 API | 162-174 |
| `novaic-app/src-tauri/vmcontrol/` | QMP/Guest Agent | 全部 |

### 10.2 测试命令

```bash
# 1. 检查 QEMU 进程
ps aux | grep qemu-system | grep -v grep

# 2. 检查端口监听
lsof -i -P | grep LISTEN | grep 2002[0-9]

# 3. 测试 VNC 连接
nc -zv localhost 20026

# 4. 测试 WebSocket 连接
nc -zv localhost 20027

# 5. 检查 QMP Socket
ls -la /var/folders/.../T/novaic/*.sock

# 6. 测试 QMP 命令（需要 Python）
python3 novaic-backend/gateway/vm/test_guest_agent.py
```

### 10.3 参考文档

- [QEMU QMP 协议](https://wiki.qemu.org/Documentation/QMP)
- [QEMU Guest Agent](https://wiki.qemu.org/Features/GuestAgent)
- [noVNC 项目](https://github.com/novnc/noVNC)
- [x11vnc 文档](https://github.com/LibVNC/x11vnc)
- [websockify 文档](https://github.com/novnc/websockify)

---

## 总结

### ✅ 已完成
1. 全面理解了当前 VNC 架构（VM 内部 x11vnc + websockify）
2. 验证了 VNC 和 WebSocket 端口的可访问性
3. 确认了 QMP 和 Guest Agent 的配置状态
4. 评估了多种 Phase 4 实现方案
5. 制定了详细的实现路线图

### 🎯 推荐方案
**保持现有架构 + 增强监控和配置管理**
- 无需修改 QEMU 配置
- 利用 Guest Agent 增强管理
- 与现有系统完全兼容
- 风险低，可维护性高

### 📋 下一步
**Phase 4.2 - VNC 健康监控**
- 实现服务状态检查
- 添加自动恢复机制
- 前端状态显示

---

**报告结束**
