# P2P Relay/Tunnel 实现与竞态修复验证 Round 2

> **调研日期**: 2026-03-12  
> **输入**: docs/survey-2026/P2P_ARCHITECTURE_ROUND1.md、p2p/relay.rs、tunnel.rs、cloud_bridge.rs、novaic-gateway pc_client.py、p2p.py

---

## 1. relay_request → send_push_and_wait_ack → connect_relay_ack 完整时序

### 1.1 端到端时序图

```
手机 App                     Gateway (p2p.py)              pc_client.py              PC CloudBridge
    |                              |                            |                            |
    |  POST /api/p2p/relay-request |                            |                            |
    |  {target_device_id}          |                            |                            |
    |------------------------------>|                            |                            |
    |                              | get_device(target_id)      |                            |
    |                              |---------------------------->|                            |
    |                              |                            |                            |
    |                              | send_push_and_wait_ack     |                            |
    |                              | (push_id, "connect_relay", |                            |
    |                              |  {relay_url, session_id})  |                            |
    |                              |---------------------------->| ws.send_json               |
    |                              |                            |--------------------------->|
    |                              |                            |                            |
    |                              |                            |                            | 解析 ConnectRelay
    |                              |                            |                            | 若有 push_id:
    |                              |                            |                            | 先发 connect_relay_ack
    |                              |                            |<---------------------------|
    |                              |                            | _handle_device_message     |
    |                              |                            | fut.set_result({ok:True})   |
    |                              |                            |                            |
    |                              | await fut (5s timeout)     |                            |
    |                              |<----------------------------|                            |
    |                              |                            |                            | tokio::spawn
    |                              |                            |                            | connect_via_relay
    |                              |                            |                            |
    |                              | _pending_relay_sessions     |                            |
    |                              | [session_id] = Pending...   |                            |
    |                              | _device_to_session[target]  |                            |
    |                              |   = session_id             |                            |
    |                              |                            |                            |
    | 200 {relay_url, session_id}   |                            |                            |
    |<------------------------------|                            |                            |
    |                              |                            |                            |
    | sleep(2s)  // INITIAL_DELAY   |                            |                            |
    |                              |                            |                            |
    | connect_via_relay(Mobile)    |                            |                            |
    |  → Relay QUIC ConnectRequest  |                            |                            |
    |  (Relay 轮询等待 PC 最多 20s) |                            |                            |
    |                              |                            |                            | RegisterPc
    |                              |                            |                            | 配对成功
    |                              |                            |                            |
    | open_vnc_stream / bridge     |                            |                            | run_tunnel_server
    |<========================================= QUIC stream 双向转发 =========================>|
```

### 1.2 关键代码路径

| 阶段 | 文件 | 位置 | 说明 |
|------|------|------|------|
| relay-request 入口 | p2p.py | 251-304 | `p2p_relay_request`：校验 target、生成 push_id、调用 `send_push_and_wait_ack` |
| send_push_and_wait_ack | pc_client.py | 271-303 | 注册 Future(key=push_id)、`ws.send_json`、`await asyncio.wait_for(fut, 5s)` |
| ACK 处理 | pc_client.py | 441-446 | `connect_relay_ack` 时 `fut.set_result({"ok": True})` |
| PC 收 push | cloud_bridge.rs | 281-363 | 解析 `ConnectRelay`；`push_id` 存在时先 `sink.send(ConnectRelayAck)`，再 `tokio::spawn` |
| session 登记 | p2p.py | 303-304 | ACK 返回后、`_pending_relay_sessions` 与 `_device_to_session` 写入 |

### 1.3 超时与失败路径

| 场景 | 行为 |
|------|------|
| PC 5s 内未 ACK | Gateway `asyncio.TimeoutError` → 503 "Failed to deliver connect_relay to device" |
| PC 断连 | `device._push_ack_pending` 中 Future 被 `set_exception(ConnectionError)` | disconnect 时 |
| P2P_PUSH_ACK_ENABLED=false | 回退到 `send_push_to_device`，不等待 ACK |

---

## 2. connect_via_relay_only 重试逻辑

### 2.1 流程概览

```
relay_request(gateway_url, jwt, target_device_id)
    ↓
sleep(2s)  // INITIAL_DELAY_SECS，给 PC 收推送 + spawn 缓冲
    ↓
for attempt in 1..=4:
    connect_via_relay(relay_url, jwt, session_id, Mobile)
        ↓
    Ok(conn) → return Ok(conn)
    Err(e)   → 判断 is_session_error
        ├─ session 错误 && attempt < 4:
        │   relay_request(gateway_url, jwt, target_device_id)  // 刷新 session
        │   sleep(2s)  // 新 session 新延迟
        │   retry_immediately = true
        │   continue
        └─ 非 session 错误 && attempt < 4:
            sleep(RETRY_DELAYS[attempt-1])  // 2s, 4s, 8s
            continue
    ↓
Err(last_err)
```

### 2.2 常量与配置

| 常量 | 值 | 说明 |
|------|-----|------|
| `INITIAL_DELAY_SECS` | 2 | relay_request 返回后、首次 connect 前 sleep；session 刷新后新一轮 connect 前也 sleep |
| `RETRY_DELAYS` | [2, 4, 8] | 非 session 错误重试退避（秒） |
| 重试次数 | 4 | connect_via_relay 最多 4 次 |

### 2.3 is_session_error 判定

```rust
// relay.rs:198-199
let is_session_error = err_lower.contains("session")
    || (err_lower.contains("expired") && !err_lower.contains("certificate"));
```

- **包含**：`session`、`expired`（排除 certificate）
- **排除**：`invalid`（JWT、handshake 等鉴权/协议错误）、`certificate`（证书过期）

### 2.4 session 刷新与 2s 延迟

- session 错误时：`relay_request` 获取新 session → `sleep(2s)` → 立即重试下一轮
- 非 session 错误时：`sleep(RETRY_DELAYS[attempt-1])` → 无 2s 初始延迟

---

## 3. cloud_bridge ConnectRelay 处理

### 3.1 ACK 顺序（R1/R5）

```rust
// cloud_bridge.rs:281-363
IncomingMessage::ConnectRelay { push_id, relay_url, session_id } => {
    let jwt = cloud_token.read().await.clone();
    // ...
    if let Some(ref pid) = push_id_opt {
        let ack_msg = OutgoingMessage::ConnectRelayAck { push_id: pid.clone() };
        if let Ok(json) = serde_json::to_string(&ack_msg) {
            let _ = sink.lock().await.send(Message::Text(json)).await;  // 先 ACK
        }
    }
    tokio::spawn(async move {
        // 再 spawn connect_via_relay
        ...
    });
    continue;
}
```

**顺序保证**：先 `sink.send(ConnectRelayAck)`，再 `tokio::spawn`。Gateway 收到 ACK 时，PC 已确认收到 push 并即将开始 connect_via_relay。

### 3.2 refresh 调用（R4）

```rust
// cloud_bridge.rs:324-341
if is_session_error && attempt < 4 {
    if let Ok(resp) =
        p2p::rendezvous::relay_refresh_for_pc(&gw, &jwt, &did).await
    {
        current_session_id = resp.session_id;
        current_relay_url = resp.relay_url;
        tracing::info!("[CloudBridge] Session refreshed, retrying connect_via_relay");
        continue;
    }
}
```

- 调用 `relay_refresh_for_pc` 续期 Gateway 侧 `_pending_relay_sessions` 的 `created_at`
- 续期量 = `_PENDING_SESSION_TTL_SECS`（20s）
- refresh 失败时 fallback 到原有 500ms×attempt 退避重试

### 3.3 is_session_error

```rust
// cloud_bridge.rs:324-327
let is_session_error = (err_lower.contains("session")
    || (err_lower.contains("expired") && !err_lower.contains("certificate")))
    && !err_lower.contains("invalid");
```

与 relay.rs 一致，但额外排除 `invalid`（JWT、handshake 等鉴权错误）。

### 3.4 非 session 错误退避

```rust
// cloud_bridge.rs:344-351
if attempt < 4 {
    let delay_ms = 500 * attempt as u64;  // 500ms, 1s, 1.5s
    tokio::time::sleep(Duration::from_millis(delay_ms)).await;
}
```

**注意**：CloudBridge 退避为 500ms×attempt，与手机侧 relay.rs 的 2/4/8s 不同；PC 侧更短，因 PC 已收到 push，主要应对 Relay 端瞬时抖动。

---

## 4. tunnel handle_incoming_stream 与 VNC/Scrcpy 转发

### 4.1 流协议（Stream Header）

每个 QUIC 双向流以 3 字节头部开始：

```
[stream_type: u8][id_len: u8][id: id_len bytes]
```

| stream_type | 含义 | resource_id |
|-------------|------|--------------|
| 0x01 | VNC | vm_id（agent_id） |
| 0x02 | Scrcpy | Android device_id |

### 4.2 handle_incoming_stream 流程

```
accept_bi() → (send, recv)
    ↓
读取头部: stream_type, id_len, resource_id
    ↓
match stream_type:
    0x01 (VNC):
        ensure_vnc_endpoint(resource_id)  // maindesk→QEMU socket, subuser→port 文件轮询
        UnixStream::connect(socket_path)
        proxy_quic_to_unix(send, recv, unix)  // 65K 缓冲双向转发
    0x02 (Scrcpy):
        ws_url = "{vmcontrol}/api/android/scrcpy?device={resource_id}"
        proxy_quic_to_ws(send, recv, ws_url)  // 帧格式 [type:u8][len:u32 BE][data]
    其他:
        send "ERR:unknown_stream_type"
```

### 4.3 VNC 转发（proxy_quic_to_unix）

- 65K 缓冲，`tokio::select!` 双向转发
- quic_recv → unix_write；unix_read → quic_send
- 任一方 EOF 时 shutdown/finish

### 4.4 Scrcpy 转发（proxy_quic_to_ws）

- 帧格式：`[type: u8][len: u32 BE][data]`，type=0x00 Binary、0x01 Text
- quic → vmcontrol：解帧后按 Text/Binary 发 WS
- vmcontrol → quic：WS Binary/Text 加帧头发送

### 4.5 常量

| 常量 | 值 | 说明 |
|------|-----|------|
| `CONNECT_TIMEOUT_SECS` | 5 | VNC Unix socket 连接超时 |
| `OPEN_BI_TIMEOUT_SECS` | 15 | open_bi 超时 |
| `VNC_RETRY_ATTEMPTS` | 3 | ensure_vnc_endpoint 重试 |
| `VNC_RETRY_DELAY_MS` | 200 | 重试间隔 |

---

## 5. 竞态修复实施后的验证点

以下验证点需**人工或集成测试**确认，无法仅靠单元测试覆盖。

### 5.1 R1/R5 推送 ACK

| 验证点 | 操作 | 预期 |
|--------|------|------|
| 正常 ACK | 手机发起 VNC，PC 在线 | relay-request 约 0.2s+2s 内完成，VNC 正常连接 |
| ACK 超时 | PC 断网或 App 未启动时手机发起 VNC | relay-request 5s 后返回 503 "Failed to deliver connect_relay to device" |
| 旧 PC 无 ACK | Gateway 新版本 + 旧 PC（无 connect_relay_ack） | 5s 超时 503，提示升级 App |
| P2P_PUSH_ACK_ENABLED=false | 环境变量关闭 ACK | relay-request 立即返回，行为与旧版一致 |

### 5.2 R2/R3 手机 2s 延迟 + Relay 20s 等待

| 验证点 | 操作 | 预期 |
|--------|------|------|
| 慢网 PC 建连 | 模拟 PC 建连 5–15s（tc 限速或人工慢网） | 手机 2s 延迟后 connect，Relay 20s 内等到 PC，配对成功 |
| TTL 一致性 | 检查 Gateway、Relay、novaic-app 常量 | `_PENDING_SESSION_TTL_SECS == SESSION_TTL == WAIT_FOR_PC_TIMEOUT == 20` |

### 5.3 R4 PC Session Refresh

| 验证点 | 操作 | 预期 |
|--------|------|------|
| session 过期后 refresh | 人为延迟 PC 建连（如断网 15s 后恢复），或 mock validate 404 | PC 调用 relay_refresh_for_pc，续期后 connect_via_relay 成功 |
| refresh 404 | session 已 consume 或过期后 refresh | 404，PC fallback 原退避重试 |
| is_session_error 排除 invalid | Relay 返回 "Invalid JWT" | 不触发 refresh，按普通错误退避 |

### 5.4 E2 RFB Close Reason

| 验证点 | 操作 | 预期 |
|--------|------|------|
| 正常断开 | VNC 连接后正常关闭 | 前端可展示 reason（若有） |
| PC offline / session expired | connect 失败或 Relay 超时 | 前端展示 "PC offline or session expired" 等后端 reason |

### 5.5 端到端集成

| 验证点 | 操作 | 预期 |
|--------|------|------|
| 手机 → PC VNC 全流程 | 手机点击远端 VNC，PC 在线 | relay_request → ACK → 2s → connect → 配对 → open_vnc_stream → bridge_ws_quic |
| 并发 relay_request | 用户快速双击 VNC | 两个 push_id 独立，各自 ACK，无冲突 |
| PC 多实例 | 同一用户多台 PC，手机选目标 | 正确推送到 target_device_id 对应 PC |

### 5.6 部署检查清单

- [ ] Gateway `_PENDING_SESSION_TTL_SECS = 20`
- [ ] novaic-quic-service `SESSION_TTL`、`WAIT_FOR_PC_TIMEOUT` 均为 20
- [ ] novaic-app relay.rs `INITIAL_DELAY_SECS = 2`
- [ ] 部署顺序：Gateway → novaic-quic-service → novaic-app
- [ ] 禁止 Gateway 20s + Relay 10s 混跑

---

## 6. 相关文档索引

| 文档 | 说明 |
|------|------|
| docs/survey-2026/P2P_ARCHITECTURE_ROUND1.md | Round 1 架构与连接路径 |
| docs/unify-vnc/P2P-RACE-IMPLEMENTATION-PLAN-R3.md | 竞态修复实施计划 |
| docs/unify-vnc/P2P-R1R5-PUSH-ACK-DESIGN-R2.md | R1/R5 ACK 设计 |
| docs/unify-vnc/P2P-R2R3-MOBILE-DELAY-RELAY-WAIT-DESIGN-R2.md | R2/R3 设计 |
| docs/unify-vnc/P2P-R4-PC-SESSION-REFRESH-DESIGN-R2.md | R4 设计 |
