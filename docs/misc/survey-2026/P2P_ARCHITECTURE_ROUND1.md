# NovAIC P2P 架构与连接路径调研 Round 1

> **调研日期**: 2026-03-12  
> **输入**: novaic-app/src-tauri/p2p/、novaic-gateway/gateway/api/p2p.py、novaic-quic-service/src/relay.rs、docs/CURRENT_STATE_SURVEY_SUMMARY.md

---

## 1. 组件清单与职责

| 组件 | 位置 | 职责 |
|------|------|------|
| **P2pClient** | p2p/client.rs | 统一入口：`connect`（远端 relay）、`connect_via_relay`（PC 入站）、`connect_direct`（本地 loopback） |
| **relay** | p2p/relay.rs | `connect_via_relay_only`（手机：relay_request + 2s 延迟 + connect_via_relay）、`connect_via_relay`（QUIC 建连 + RegisterPc/ConnectRequest 握手） |
| **tunnel** | p2p/tunnel.rs | `run_tunnel_server`（PC 侧 accept_bi → handle_incoming_stream）、`open_vnc_stream` / `open_scrcpy_stream`（手机侧开流 + 3 字节头部） |
| **rendezvous** | p2p/rendezvous.rs | `relay_request`、`relay_refresh_for_pc`（R4）、`heartbeat`、`locate`、STUN `get_external_addr` |
| **vnc_endpoint** | p2p/vnc_endpoint.rs | `ensure_vnc_endpoint`：maindesk 返回 QEMU socket，subuser 轮询 port 文件 + Unix 代理 |
| **hole_punch** | p2p/hole_punch.rs | `connect_to_peer`（本地直连 QUIC，打洞已移除，仅用于 loopback） |
| **Gateway p2p** | gateway/api/p2p.py | heartbeat、locate、relay-request、relay-refresh-for-pc、validate-relay-session、my-devices |
| **Relay 服务** | novaic-quic-service/relay.rs | QUIC 服务端：accept → RegisterPc/ConnectRequest 握手 → 配对 → forward_streams |
| **CloudBridge** | vmcontrol/cloud_bridge.rs | 收 connect_relay 推送 → 先 ACK（R1/R5）→ spawn connect_via_relay → run_tunnel_server |
| **VncProxy** | vnc_proxy.rs | route_vnc：本机 → serve_local_vnc，远端 → serve_remote_vnc；统一 WS ↔ QUIC 桥接 |

**打洞已移除**：远端仅走 relay，`hole_punch::punch_and_connect` 已删除。

---

## 2. 连接路径

### 2.1 手机远端 VNC

```
用户点击 VNC
  → VncProxy route_vnc (device_id != local_id)
  → serve_remote_vnc
  → get_or_create_remote_conn
  → P2pClient::connect
  → relay::connect_via_relay_only
      1. rendezvous::relay_request → Gateway POST /api/p2p/relay-request
         → Gateway send_push_and_wait_ack (5s) → PC CloudBridge 收 connect_relay
         → PC 先 ACK → spawn connect_via_relay → run_tunnel_server
      2. sleep(2s)  // INITIAL_DELAY_SECS，给 PC 收推送 + spawn 缓冲
      3. connect_via_relay (RelayRole::Mobile) → Relay QUIC ConnectRequest
         → Relay 轮询等待 PC 最多 20s → 配对
  → tunnel::open_vnc_stream (stream_type=0x01, resource_id=agent_id)
  → bridge_ws_quic (WS ↔ QUIC 双向转发)
```

### 2.2 PC 入站 Relay

```
Gateway relay-request
  → send_push_and_wait_ack(connect_relay, push_id, timeout=5s)
  → PC CloudBridge 收 connect_relay
  → 若有 push_id：先发 connect_relay_ack
  → tokio::spawn connect_via_relay (RelayRole::Pc)
  → Relay QUIC RegisterPc (device_id, jwt, session_id)
  → Relay 校验 session → 写入 pc_registry
  → 手机 ConnectRequest 时 Relay 配对 → forward_streams
  → PC run_tunnel_server
  → accept_bi → handle_incoming_stream
  → stream_type 0x01: ensure_vnc_endpoint → proxy_quic_to_unix
  → stream_type 0x02: proxy_quic_to_ws (scrcpy)
```

### 2.3 本地 VNC（桌面 App）

```
route_vnc (device_id == local_id)
  → serve_local_vnc
  → get_or_create_local_conn
  → P2pClient::connect_direct(127.0.0.1:19998, device_id, cert_der)
  → hole_punch::connect_to_peer (QUIC 直连)
  → tunnel::open_vnc_stream
  → bridge_ws_quic
```

---

## 3. 2026-03-12 已实施的 P2P 竞态修复

| 方案 | 描述 | 实施位置 |
|------|------|----------|
| **R2/R3** | 20s TTL + 2s 手机延迟 | Gateway `_PENDING_SESSION_TTL_SECS=20`；Relay `SESSION_TTL=20`、`WAIT_FOR_PC_TIMEOUT=20`；relay.rs `INITIAL_DELAY_SECS=2` |
| **R4** | PC session 刷新 | Gateway `POST /api/p2p/relay-refresh-for-pc`；CloudBridge 失败且 is_session_error 时调用 `relay_refresh_for_pc` |
| **R1/R5** | 推送 ACK 确认 | Gateway `send_push_and_wait_ack`（5s 超时）；PC 收 connect_relay 后先发 `connect_relay_ack` 再 spawn |
| **E2** | RFB Close Reason | noVNC patch：`_rfbCloseReason` 透传；vnc_proxy `send_ws_close_with_reason`；前端可展示 "PC offline or session expired" 等 |

---

## 4. 关键常量：TTL、超时、延迟

### 4.1 Gateway (p2p.py)

| 常量 | 值 | 说明 |
|------|-----|------|
| `STALE_THRESHOLD_SECS` | 60 | 心跳 60s 无更新视为离线 |
| `_PENDING_SESSION_TTL_SECS` | 20 | relay session 预注册 TTL；relay-refresh 续期量 |
| `send_push_and_wait_ack` timeout | 5 | 等待 PC ACK 超时（秒） |

### 4.2 novaic-quic-service (relay.rs)

| 常量 | 值 | 说明 |
|------|-----|------|
| `SESSION_TTL` | 20s | PC RegisterPc 后若无手机连接则过期 |
| `WAIT_FOR_PC_TIMEOUT` | 20s | 手机 ConnectRequest 时轮询等待 PC 最长时间 |
| `POLL_INTERVAL` | 300ms | 轮询间隔 |
| Handshake read timeout | 15s | 首行 JSON 读取超时 |

### 4.3 novaic-app p2p (relay.rs)

| 常量 | 值 | 说明 |
|------|-----|------|
| `INITIAL_DELAY_SECS` | 2 | relay_request 返回后、首次 connect 前 sleep；session 刷新后新一轮 connect 前也 sleep |
| `HANDSHAKE_READ_TIMEOUT_SECS` | 40 | 手机等待 Relay 握手响应（覆盖 2+30+20） |
| Relay connect timeout | 30s | QUIC 建连超时 |
| `RETRY_DELAYS` | [2, 4, 8] | 非 session 错误重试退避（秒） |
| 重试次数 | 4 | connect_via_relay 最多 4 次 |

### 4.4 novaic-app p2p (tunnel.rs)

| 常量 | 值 | 说明 |
|------|-----|------|
| `CONNECT_TIMEOUT_SECS` | 5 | VNC Unix socket 连接超时 |
| `OPEN_BI_TIMEOUT_SECS` | 15 | open_bi 超时 |
| `VNC_RETRY_ATTEMPTS` | 3 | ensure_vnc_endpoint 重试 |
| `VNC_RETRY_DELAY_MS` | 200 | 重试间隔 |

### 4.5 novaic-app p2p (vnc_endpoint.rs)

| 常量 | 值 | 说明 |
|------|-----|------|
| `SUBUSER_POLL_TIMEOUT_SECS` | 30 | subuser port 文件轮询超时 |
| `SUBUSER_POLL_INTERVAL_MS` | 500 | 轮询间隔 |

### 4.6 novaic-app vnc_proxy

| 常量 | 值 | 说明 |
|------|-----|------|
| `CONN_TTL` | 4min | 连接缓存 TTL，驱逐过期 |
| `WS_UPGRADE_TIMEOUT` | 30s | WS 升级超时，超时发送 Close reason |

### 4.7 rendezvous (heartbeat)

| 常量 | 值 | 说明 |
|------|-----|------|
| `heartbeat_interval` | 25s | 典型配置，< NAT 映射超时 30s |
| STUN timeout | 5s | get_external_addr 单次 |

---

## 5. 部署与 TTL 一致性

**对齐原则**：`WAIT_FOR_PC_TIMEOUT == SESSION_TTL == _PENDING_SESSION_TTL_SECS == 20s`

**部署顺序**：Gateway → novaic-quic-service（Relay）→ novaic-app（手机/PC）

**relay_request 最坏延迟**：ACK 5s + 手机 2s = 7s 才发起 connect（正常路径约 2.2s）

---

## 6. 相关文档索引

| 文档 | 说明 |
|------|------|
| docs/CURRENT_STATE_SURVEY_SUMMARY.md | 三轮调研汇总 |
| docs/unify-vnc/P2P-RACE-IMPLEMENTATION-PLAN-R3.md | 竞态修复实施计划 |
| docs/unify-vnc/P2P-R2R3-MOBILE-DELAY-RELAY-WAIT-DESIGN-R2.md | R2/R3 设计 |
| docs/unify-vnc/P2P-R4-PC-SESSION-REFRESH-DESIGN-R2.md | R4 设计 |
| docs/unify-vnc/P2P-R1R5-PUSH-ACK-DESIGN-R2.md | R1/R5 设计 |
| docs/unify-vnc/P2P-E2-RFB-CLOSE-REASON-DESIGN-R2.md | E2 设计 |
