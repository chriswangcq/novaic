# VNC Proxy 路由与错误传播（Round 2）

**产出时间**: 2026-03-12  
**输入**: `docs/survey-2026/VNC_RELAY_ROUND1.md`、`vnc_proxy.rs`、`vnc_endpoint.rs`、`vnc_bridge.rs`、`tunnel.rs`

---

## 1. route_vnc 决策树

### 1.1 决策流程

```
route_vnc(ws, device_id, agent_id)
│
├─ local_id = state.local_vmcontrol.read().await.as_ref().map(|info| info.device_id.clone())
│
├─ 分支 1: local_id.as_deref() == Some(device_id)
│   └─► serve_local_vnc(ws, agent_id, state)
│         ├─ get_or_create_local_conn(state)
│         ├─ tunnel::open_vnc_stream(&conn, agent_id)
│         └─ bridge_ws_quic(ws, quic_send, quic_recv)
│
├─ 分支 2: p2p_setup_error 存在且 failed_did == device_id
│   └─► bail!("P2P setup failed: {}. Please check NOVAIC_P2P_PORT and firewall.", err)
│         （不进入 serve_remote_vnc，直接返回 Err）
│
└─ 分支 3: 其他
    └─► serve_remote_vnc(ws, device_id, agent_id, state)
          ├─ get_or_create_remote_conn(device_id, state)
          ├─ tunnel::open_vnc_stream(&conn, agent_id)
          └─ bridge_ws_quic(ws, quic_send, quic_recv)
```

### 1.2 local_id 判断

| 条件 | 含义 | 路由 |
|------|------|------|
| `local_id.as_deref() == Some(device_id)` | 本机 VmControl 已就绪且 device_id 匹配 | `serve_local_vnc` |
| `local_id` 为 `None` | VmControl 未启动或未注册 | 走 `serve_remote_vnc`（若 device_id 为本机，`get_or_create_local_conn` 会重试 3×500ms 后失败） |
| `local_id != device_id` | 目标为远端 PC | `serve_remote_vnc` |

**代码位置**：`vnc_proxy.rs:273-288`

### 1.3 get_or_create_local_conn

| 步骤 | 行为 |
|------|------|
| 1. 快速检查缓存 | `local_conn` 若存在且 `conn_still_valid`（未关闭、未超 TTL 4min），直接返回 |
| 2. 等待 local_vmcontrol | 轮询最多 3 次，间隔 500ms；超时则 `bail!("VmControl P2P not ready yet — please wait a moment and retry")` |
| 3. 持锁建连 | `connect_direct(127.0.0.1:{info.port}, device_id, cert_der)` |
| 4. 写缓存 | `local_conn = Some((conn, Instant::now()))` |

**失败时**：`serve_local_vnc` 调用 `send_ws_close_with_reason(&mut ws, e.to_string())` 后返回 `Err(e)`。

**代码位置**：`vnc_proxy.rs:308-349`

### 1.4 get_or_create_remote_conn

| 步骤 | 行为 |
|------|------|
| 1. 快速检查缓存 | `remote_conns.get(device_id)` 若存在且 `conn_still_valid`，直接返回 |
| 2. 校验配置 | `gateway_url` 空则 `bail!("Gateway URL not configured — cannot locate remote device")`；`token` 空则 `bail!("Not logged in — JWT token missing")` |
| 3. P2P 建连 | `p2p_client.connect(&gateway_url, &token, device_id)`（relay + rendezvous，可能 10–30s） |
| 4. 写缓存 | `remote_conns.insert(device_id, (conn, Instant::now()))` |

**失败时**：`serve_remote_vnc` 调用 `send_ws_close_with_reason(&mut ws, e.to_string())` 后返回 `Err(e)`。

**代码位置**：`vnc_proxy.rs:375-421`

---

## 2. ensure_vnc_endpoint subuser 轮询 30s 超时

### 2.1 位置与调用链

- **实现**：`p2p/vnc_endpoint.rs`
- **调用**：`tunnel::handle_incoming_stream`（PC 侧，stream_type 0x01）→ `ensure_vnc_endpoint(resource_id)`

### 2.2 subuser 轮询参数

| 常量 | 值 | 说明 |
|------|-----|------|
| `SUBUSER_POLL_TIMEOUT_SECS` | 30 | 总超时秒数 |
| `SUBUSER_POLL_INTERVAL_MS` | 500 | 轮询间隔毫秒 |
| `max_polls` | 60 | `(30*1000)/500` |

### 2.3 轮询逻辑

```rust
// vnc_endpoint.rs:156-174
let mut poll_count = 0;
let max_polls = (SUBUSER_POLL_TIMEOUT_SECS * 1000) / SUBUSER_POLL_INTERVAL_MS;
let _port = loop {
    if let Ok(s) = tokio::fs::read_to_string(&port_file).await {
        if let Ok(p) = s.trim().parse::<u16>() {
            break p;  // 成功
        }
    }
    poll_count += 1;
    if poll_count >= max_polls {
        return Err(format!(
            "VNC port file not found for user '{}': {} — Xvnc may not have started (timeout {}s)",
            username, port_file, SUBUSER_POLL_TIMEOUT_SECS
        ));
    }
    tokio::time::sleep(Duration::from_millis(SUBUSER_POLL_INTERVAL_MS)).await;
};
```

### 2.4 超时错误传播

| 层级 | 行为 |
|------|------|
| `ensure_vnc_endpoint` | 返回 `Err("VNC port file not found for user 'xxx': ... — Xvnc may not have started (timeout 30s)")` |
| `tunnel::handle_incoming_stream` | 重试 3 次（`VNC_RETRY_ATTEMPTS`），每次间隔 200ms；最终 `return Err(last_err)` |
| PC 侧 stream handler | Task 退出，QUIC stream 被 drop，**不向 QUIC 写入错误消息** |
| VncProxy 侧 `bridge_ws_quic` | `quic_recv.read()` 收到 EOF/reset，loop 退出 |
| `WsWriteCloseGuard` drop | 调用 `sink.close()`，**无 reason** |

**结论**：ensure_vnc_endpoint 的 30s 超时错误**不会**以 Close reason 形式传到前端。VncProxy 仅感知 QUIC stream 结束，发送的是无 reason 的标准 WebSocket close。

---

## 3. send_ws_close_with_reason 调用点与 reason 内容

### 3.1 实现

```rust
// vnc_proxy.rs:319-328
const WS_CLOSE_INTERNAL_ERROR: u16 = 1011;

async fn send_ws_close_with_reason(ws: &mut WebSocket, reason: impl AsRef<str>) {
    let reason_str = reason.as_ref();
    let truncated = if reason_str.len() > 120 {
        format!("{}...", &reason_str[..117])
    } else {
        reason_str.to_string()
    };
    let frame = CloseFrame { code: WS_CLOSE_INTERNAL_ERROR, reason: truncated.into() };
    let _ = ws.send(Message::Close(Some(frame))).await;
}
```

### 3.2 调用点汇总

| 位置 | 场景 | reason 内容 |
|------|------|-------------|
| `vnc_proxy.rs:206` | VNC WS 升级 30s 超时 | `"VNC connection timed out (30s)"` |
| `vnc_proxy.rs:250` | Scrcpy WS 升级 30s 超时 | `"Scrcpy connection timed out (30s)"` |
| `vnc_proxy.rs:341` | `get_or_create_local_conn` 失败 | `e.to_string()` |
| `vnc_proxy.rs:349` | 本地 `open_vnc_stream` 失败 | `e.to_string()` |
| `vnc_proxy.rs:365` | `get_or_create_remote_conn` 失败 | `e.to_string()` |
| `vnc_proxy.rs:373` | 远端 `open_vnc_stream` 失败 | `e.to_string()` |
| `vnc_proxy.rs:390` | 本地 Scrcpy `get_or_create_local_conn` 失败 | `e.to_string()` |
| `vnc_proxy.rs:398` | 本地 Scrcpy `open_scrcpy_stream` 失败 | `e.to_string()` |
| `vnc_proxy.rs:391` | 远端 Scrcpy `get_or_create_remote_conn` 失败 | `e.to_string()` |
| `vnc_proxy.rs:399` | 远端 Scrcpy `open_scrcpy_stream` 失败 | `e.to_string()` |

### 3.3 典型 reason 文案

| 场景 | reason 示例 |
|------|-------------|
| WS 升级超时 | `"VNC connection timed out (30s)"` / `"Scrcpy connection timed out (30s)"` |
| 本地 P2P 未就绪 | `"VmControl P2P not ready yet — please wait a moment and retry"` |
| 本地 QUIC 建连失败 | `"Local QUIC connect failed: ..."` |
| 本机 P2P 启动失败 | `"P2P setup failed: ... Please check NOVAIC_P2P_PORT and firewall."` |
| 远端 P2P 建连失败 | `"Remote P2P connect failed: ..."` |
| 配置/登录问题 | `"Gateway URL not configured — cannot locate remote device"` / `"Not logged in — JWT token missing"` |
| open_vnc_stream 超时 | `"open_vnc_stream timed out after 15s"` |

### 3.4 未覆盖场景

| 场景 | 是否发送 Close reason |
|------|------------------------|
| `ensure_vnc_endpoint` subuser 30s 超时 | ❌ 否（错误在 PC 侧，QUIC stream 直接结束，VncProxy 无具体错误） |
| `bridge_ws_quic` 运行中 QUIC 断开 | ❌ 否（`WsWriteCloseGuard` 仅 `sink.close()`，无 reason） |
| `bridge_ws_quic` 运行中 WS 收到 Close | 透传（取决于客户端行为） |

---

## 4. Scrcpy 30s 超时是否发送 Close reason

**是**。Scrcpy handler 与 VNC handler 同构，均使用 `tokio::select!` 竞争 `route_scrcpy` 与 30s 超时：

```rust
// vnc_proxy.rs:244-252
let timeout_fut = async move {
    tokio::time::sleep(WS_UPGRADE_TIMEOUT).await;
    let mut guard = socket.lock().await;
    if let Some(mut ws) = guard.take() {
        send_ws_close_with_reason(&mut ws, "Scrcpy connection timed out (30s)").await;
    }
};
```

**代码位置**：`vnc_proxy.rs:221-262`

---

## 5. vnc_bridge CloseFrame 到前端的传递路径

### 5.1 数据流

```
VncProxy (Rust)
  │ send_ws_close_with_reason(ws, reason)
  │   → ws.send(Message::Close(Some(CloseFrame { code: 1011, reason })))
  ▼
WebSocket (tokio_tungstenite, vnc_bridge 侧)
  │ ws_read.next() → Some(Ok(WsMsg::Close(frame)))
  ▼
vnc_bridge.rs:160-166
  │ let reason = frame.as_ref().map(|f| f.reason.to_string()).unwrap_or_else(|| "Connection closed".to_string());
  │ app.emit(&close_event, &reason)
  ▼
Tauri emit("vnc_bridge:{bridge_id}:close", reason)
  ▼
前端 vncBridge.ts
  │ listen(`vnc_bridge:${bridgeId}:close`, (e) => { ... })
  │ this.onclose?.({ reason: e.payload })
  ▼
VncBridgeTransport / useVnc 等
  │ onclose?.({ reason })
  ▼
UI 展示错误文案
```

### 5.2 代码路径

| 层级 | 文件 | 行号 | 行为 |
|------|------|------|------|
| 后端发送 | `vnc_proxy.rs` | 319-328 | `send_ws_close_with_reason` 构造 `CloseFrame` 并发送 |
| Bridge 接收 | `commands/vnc_bridge.rs` | 160-166 | 解析 `frame.reason`，`emit(close_event, &reason)` |
| 前端监听 | `services/vncBridge.ts` | 81-89 | `listen(closeEvent, (e) => this.onclose?.({ reason: e.payload }))` |

### 5.3 OTA vs 直连

| 模式 | Close 来源 | 传递路径 |
|------|------------|----------|
| **OTA**（VncBridgeTransport） | VncProxy → vnc_bridge 的 WebSocket | vnc_bridge 收到 Close → emit → 前端 listen |
| **直连**（URL WebSocket） | VncProxy → 前端 `new WebSocket(url)` | 前端 `ws.onclose` 直接收到 `CloseEvent`，含 `e.reason` |

### 5.4 noVNC patch 说明

当前 noVNC 的 `disconnect` 事件 `detail` 仅含 `{ clean }`，不含 `reason`。需对 `@novnc/novnc` 打 patch，在 `_socketClose` 中保存 `e.reason`，在 `disconnect` 派发时加入 `detail.reason`，才能让 `useVnc.ts`、`vncStream.ts` 等通过 `e?.detail?.reason` 展示具体错误。详见 `P2P-E2-RFB-CLOSE-REASON-DESIGN-R2.md`。

---

## 6. 参考

| 文档 | 关联内容 |
|------|----------|
| `VNC_RELAY_ROUND1.md` | 连接决策、路由概览 |
| `P2P-E2-RFB-CLOSE-REASON-DESIGN-R2.md` | Close reason 透传、noVNC patch |
| `VNC_BACKEND_TUNNEL_TIMING_REPORT.md` | ensure_vnc_endpoint 与 WS 超时协调 |
| `P2P_RACE_AND_ERROR_HANDLING_RESEARCH_ROUND3.md` | E2 缺口、错误传播 |
