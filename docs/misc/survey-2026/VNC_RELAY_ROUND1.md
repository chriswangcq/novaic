# NovAIC VNC/Relay 连接决策与路由调研（Round 1）

**产出时间**: 2026-03-12  
**输入文件**: `vnc_proxy.rs`、`vncTransport.ts`、`vncBridge.ts`、`p2p/tunnel.rs`

---

## 1. 连接决策

### 1.1 OTA vs WebSocket

| 模式 | 条件 | 传输方式 | 代码位置 |
|------|------|----------|----------|
| **OTA** | `shouldUseVncBridge()` 为 true | `VncBridgeTransport`（Tauri IPC 桥接） | `vncTransport.ts:26-29` |
| **非 OTA** | `shouldUseVncBridge()` 为 false | `invoke('get_vnc_proxy_url')` → WebSocket URL | `vncTransport.ts:31-36` |

**OTA 判断**（`vncBridge.ts:22-25`）：
- `shouldUseVncBridge()` 基于 `window.isSecureContext`
- HTTPS 页面（如 `relay.gradievo.com`）连接 `ws://127.0.0.1` 会被浏览器 Mixed Content 拦截
- 因此 OTA 模式必须走 `VncBridgeTransport`，由 Rust 侧连接 ws://，通过 IPC 与前端通信

**非 OTA**（桌面 Tauri 或非 HTTPS 环境）：
- 直接 `get_vnc_proxy_url` 获取 `ws://127.0.0.1:{port}/vnc/{pc_client_id}/{resource_id}`
- 前端 `new WebSocket(url)` 直连 VncProxy

### 1.2 本机 vs 远程

| 场景 | 判断依据 | 连接路径 |
|------|----------|----------|
| **本机** | `local_vmcontrol.device_id == device_id` | QUIC loopback `127.0.0.1:19998` |
| **远程** | `device_id != local_id` | Gateway locate + P2P relay → QUIC |

**pc_client_id 解析**（`vnc_urls.rs` / `vnc_bridge.rs`）：
1. 优先：`local_vmcontrol.device_id`（桌面本机）
2. 其次：调用方传入的 `pcClientId`（多 PC 时指定目标）
3. 兜底：`GET /api/p2p/my-devices` 取第一个 `online` 的 `pc_client_id`（移动端）

### 1.3 本地 QUIC vs 远程 Relay

| 路径 | 入口 | 连接方式 |
|------|------|----------|
| **本地** | `serve_local_vnc` | `P2pClient::connect_direct(127.0.0.1:{port}, device_id, cert_der)` → QUIC loopback |
| **远程** | `serve_remote_vnc` | `P2pClient::connect(gateway_url, token, device_id)` → relay 建连 → QUIC |

**本地**（`vnc_proxy.rs:339-344`）：
- `connect_direct` 调用 `hole_punch::connect_to_peer`，直连本机 VmControl QUIC 端口

**远程**（`vnc_proxy.rs:404-406`）：
- `connect` 调用 `relay::connect_via_relay_only`，经 Gateway rendezvous + relay 建立 QUIC 隧道

---

## 2. vnc_proxy 路由

### 2.1 serve_local_vnc

**触发条件**：`local_id.as_deref() == Some(device_id)`（`vnc_proxy.rs:277`）

**流程**：
1. `get_or_create_local_conn`：缓存或新建 QUIC 连接（`127.0.0.1:{info.port}`）
2. `tunnel::open_vnc_stream(&conn, agent_id)`：在 QUIC 上开 VNC 双向流
3. `bridge_ws_quic`：WebSocket ↔ QUIC 双向桥接

**缓存**：`local_conn` 单连接复用，TTL 4 分钟，多 VNC 窗口共享同一条 QUIC 隧道。

### 2.2 serve_remote_vnc

**触发条件**：`device_id != local_id`，或 `p2p_setup_error` 不匹配当前 device（`vnc_proxy.rs:281-288`）

**流程**：
1. `get_or_create_remote_conn`：缓存或通过 Gateway locate + relay 建连
2. `tunnel::open_vnc_stream(&conn, agent_id)`
3. `bridge_ws_quic`

**P2P 建连失败**：若 `p2p_setup_error` 中 `failed_did == device_id`，直接 `bail!`，提示检查 NOVAIC_P2P_PORT 和防火墙。

**缓存**：`remote_conns` 按 `device_id` 缓存，TTL 4 分钟。

---

## 3. ensure_vnc_endpoint：maindesk vs subuser

**位置**：`p2p/vnc_endpoint.rs`，由 `tunnel.rs` 的 `handle_incoming_stream` 在 VNC 流（stream_type 0x01）时调用。

### 3.1 resource_id 格式

| 类型 | 格式 | 示例 |
|------|------|------|
| **maindesk** | `{vm_id}`（不含 `:`） | `abc123...` |
| **subuser** | `{vm_id}:{username}` | `abc123:alice` |

### 3.2 maindesk 路径

- 直接查找 QEMU VNC socket：`/tmp/novaic/novaic-vnc-{vm_id}.sock` 或 `$TEMP/novaic/novaic-vnc-{vm_id}.sock`
- 存在则返回路径；不存在则返回错误："VNC socket not found for VM '...' — VM may not be running or VNC not enabled."

### 3.3 subuser 路径

1. 解析 `{vm_id}:{username}`
2. 轮询 port 文件：`/tmp/novaic/share-{vm_id}/vnc-{username}.port`（超时 30s，间隔 500ms）
3. 创建 Unix socket 代理：`/tmp/novaic/vnc-{vm_id}-{username}.sock`（`:` 替换为 `-`）
4. 代理：Unix socket ↔ TCP `127.0.0.1:{port}`（port 从 port 文件读取）
5. 返回代理 socket 路径

**并发**：per-resource_id 锁，防止同一 subuser 并发创建多个代理。

---

## 4. 错误处理与 Close Reason（E2 patch 后）

### 4.1 后端发送 Close Reason

| 位置 | 场景 | Close 内容 |
|------|------|------------|
| `vnc_proxy.rs:319-327` | `send_ws_close_with_reason` | code 1011，reason 截断至 120 字节 |
| `vnc_proxy.rs:204-205` | WS 升级 30s 超时 | "VNC connection timed out (30s)" |
| `vnc_proxy.rs:341-342` | 本地 QUIC 建连失败 | `e.to_string()` |
| `vnc_proxy.rs:348-349` | `open_vnc_stream` 失败 | `e.to_string()` |
| `vnc_proxy.rs:364-365` | 远端 `get_or_create_remote_conn` 失败 | `e.to_string()` |
| `vnc_proxy.rs:368-369` | 远端 `open_vnc_stream` 失败 | `e.to_string()` |
| `vnc_bridge.rs:161-165` | 收到 WS Close 帧 | `frame.reason` 通过 `emit(close_event, reason)` 传给前端 |

### 4.2 典型错误文案

- `"VNC connection timed out (30s)"` — WS 升级超时
- `"VmControl P2P not ready yet — please wait a moment and retry"` — 本地 P2P 未就绪
- `"P2P setup failed: ... Please check NOVAIC_P2P_PORT and firewall."` — 本机 P2P 启动失败
- `"Remote P2P connect failed: ..."` — relay/rendezvous 失败
- `"PC offline or session expired"` — Relay 等待 PC 超时（来自 relay 层）
- `"Gateway URL not configured"` / `"Not logged in — JWT token missing"` — 配置/登录问题

### 4.3 E2 Patch 后的前端行为

**问题**：noVNC RFB 的 `disconnect` 事件 `detail` 仅含 `{ clean }`，不含 `reason`。

**方案**（`P2P-E2-RFB-CLOSE-REASON-DESIGN-R2.md`）：
- 对 `@novnc/novnc` 打 patch，在 `_socketClose` 中保存 `e.reason`，在 `disconnect` 派发时加入 `detail.reason`
- 覆盖 URL 直连与 VncBridgeTransport 两种路径
- `useVnc.ts`、`vncStream.ts` 已预留 `e?.detail?.reason`，patch 生效后即可展示具体错误

---

## 5. 数据流概览

```
前端 createVncTransport(target)
  ├─ OTA: VncBridgeTransport → invoke('vnc_bridge_connect') → Rust 连 ws://
  └─ 非 OTA: invoke('get_vnc_proxy_url') → new WebSocket(url)

VncProxy ws://127.0.0.1:{port}/vnc/{device_id}/{agent_id}
  ├─ device_id == local → serve_local_vnc
  │     → connect_direct(127.0.0.1) → tunnel::open_vnc_stream → bridge_ws_quic
  └─ device_id != local → serve_remote_vnc
        → connect(gateway, token, device_id) [relay] → tunnel::open_vnc_stream → bridge_ws_quic

Tunnel (PC 侧): QUIC stream → ensure_vnc_endpoint(resource_id)
  ├─ maindesk: novaic-vnc-{vm_id}.sock
  └─ subuser: 轮询 port 文件 → Unix 代理 → TCP 127.0.0.1:{port}
```

---

## 6. 参考

| 文档 | 关联内容 |
|------|----------|
| `P2P-E2-RFB-CLOSE-REASON-DESIGN-R2.md` | Close reason 透传、noVNC patch |
| `VNC_RELAY_CONNECTION_FLOW_DIAGRAM.md` | 连接流程图 |
| `P2P_RACE_AND_ERROR_HANDLING_RESEARCH_ROUND3.md` | E2 缺口、错误传播 |
