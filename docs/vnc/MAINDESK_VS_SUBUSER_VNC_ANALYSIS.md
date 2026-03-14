# Maindesk vs Subuser VNC 连接差异分析

> **协作文档已迁移至** [`docs/unify-vnc/03-maindesk-vs-subuser.md`](./unify-vnc/03-maindesk-vs-subuser.md)。

## 一、调用链对比

| 维度 | Maindesk (主桌面) | Subuser (子用户) |
|------|-------------------|------------------|
| **组件** | VNCViewShared, DeviceVNCView, VNCView | VmUserVNCView |
| **数据源** | DeviceFloatingPanel: `device.id` + `binding.subject_type='main'` | DeviceFloatingPanel: `device.id` + `binding.subject_id` (username) |
| **getVncTransport 参数** | `agentId` = device.id | `agentId` = `${deviceId}:${username}` |
| **后端 resource_id** | vm_id (单段) | vm_id:username (两段) |

---

## 二、后端路由差异 (tunnel.rs find_vnc_target)

| 类型 | resource_id 格式 | 目标 | 路径/端口来源 |
|------|-----------------|------|---------------|
| **Maindesk** | `{vm_id}` | Unix socket | `/tmp/novaic/novaic-vnc-{vm_id}.sock` |
| **Subuser** | `{vm_id}:{username}` | TCP | `/tmp/novaic/share-{vm_id}/vnc-{username}.port` → 读端口 → `127.0.0.1:{port}` |

**差异要点**：
- Maindesk 走 QEMU 内置 VNC Unix socket，通常 VM 启动后即存在
- Subuser 走 TigerVNC/Xvnc TCP 端口，依赖 9p 共享的 port 文件，存在时序：用户登录、Xvnc 启动、port 文件写入

---

## 三、前端实现差异

### 3.1 连接流程

| 项目 | Maindesk | Subuser |
|------|----------|---------|
| **入口** | useVNCConnection / useDeviceVNCConnection / vncStream | VmUserVNCView 内直接 connect() |
| **WebSocket 探测** | 有（非 Bridge 时 testWebSocket） | 无 |
| **轮询重试** | 有（3s 间隔，VM running 但 WS 未就绪时） | 无，仅 mount 时 connect 一次 |
| **自动重连** | vncStream 有（disconnect 后 2s 重试，最多 3 次） | 无，需用户点 Retry |

### 3.2 RFB 构造参数

| 参数 | Maindesk (VNCView/DeviceVNCView/vncStream) | Subuser (VmUserVNCView) |
|------|-------------------------------------------|-------------------------|
| shared | `true` | 未传（默认） |
| credentials | `{}` | 未传 |
| wsProtocols | 未传 | `['binary']` |
| clipViewport | `true` (VNCView/DeviceVNCView) | 未传 |
| scaleViewport | `true` | `true` |
| resizeSession | `false` | `false` |

### 3.3 状态与 UI

| 项目 | Maindesk | Subuser |
|------|----------|---------|
| **状态机** | unknown → starting → running / error | connecting → connected / error / disconnected |
| **Start/Stop 控制** | 有 | 无（Xvnc 由 systemd 管理） |
| **错误展示** | 统一 errorMsg | 独立 errorMsg + Retry 按钮 |

---

## 四、可能导致「表现不一样」的原因

### 4.1 后端时序

- **Subuser** 依赖 `/tmp/novaic/share-{vm_id}/vnc-{username}.port` 存在
- 若用户刚登录或 Xvnc 刚启动，port 文件可能尚未写入
- Maindesk 的 Unix socket 在 VM 启动后通常更早可用

### 4.2 前端重试策略

- **Maindesk**：有轮询 + 自动重连，连接未就绪时会持续重试
- **Subuser**：只尝试一次，失败后需用户手动 Retry

### 4.3 RFB 选项

- `wsProtocols: ['binary']` 仅在 Subuser 使用，可能影响与 VncBridgeTransport 的兼容
- `shared` 未在 Subuser 显式设置，多客户端行为可能不同

### 4.4 连接建立时机

- **Maindesk**：依赖 `status === 'running' && wsReady`，有 VM 状态 + WS 探测
- **Subuser**：组件 mount 即 connect，无前置状态检查

---

## 五、相关文件索引

| 文件 | 职责 |
|------|------|
| `novaic-app/src/components/VM/VmUserVNCView.tsx` | Subuser VNC 视图 |
| `novaic-app/src/components/Visual/VNCViewShared.tsx` | Maindesk 共享流视图 |
| `novaic-app/src/components/Visual/DeviceVNCView.tsx` | Device 主桌面视图 |
| `novaic-app/src/components/Visual/useVNCConnection.ts` | Maindesk 连接 hook |
| `novaic-app/src/components/Visual/useDeviceVNCConnection.ts` | Device 连接 hook |
| `novaic-app/src/services/vncStream.ts` | 共享 VNC 流 |
| `novaic-app/src-tauri/p2p/src/tunnel.rs` | find_vnc_target、QUIC 路由 |
| `novaic-app/src-tauri/src/vnc_proxy.rs` | WS 代理、route_vnc |
