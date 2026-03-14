# 手机 VNC 连接失败分析

> 现象：手机连不上，`ws://127.0.0.1:63471/vnc/...` 报错「连接被对方重置」

---

## 一、Relay 日志分析

### 1.1 服务状态

```text
ssh root@relay.gradievo.com 'journalctl -u novaic-quic-service -n 150 --no-pager'
```

**发现**：

1. **16:36–16:37**：Relay 反复 panic 崩溃：
   ```text
   Could not automatically determine the process-level CryptoProvider from Rustls crate features.
   Call CryptoProvider::install_default() before this point...
   ```

2. **16:37:33**：修复版本部署后成功启动：
   ```text
   [Relay] Listening on 0.0.0.0:443
   ```

3. **16:41:05**：手动重启后正常运行。

**结论**：Relay 当前应已正常运行。若仍崩溃，需确认服务器上的二进制已包含 `main.rs` 中的 `rustls::crypto::ring::default_provider().install_default()` 修复。

### 1.2 查看实时日志

```bash
ssh root@relay.gradievo.com 'journalctl -u novaic-quic-service -f'
```

---

## 二、连接流程与根因

### 2.1 手机 VNC 连接路径

```
手机前端 → get_vnc_proxy_url(agentId)
         → vnc_urls.rs: 无 local_vmcontrol 时，GET /api/p2p/my-devices 取第一个 online 的 vmcontrol device_id
         → ws://127.0.0.1:{port}/vnc/{vmcontrol_device_id}/{agent_id}

VncProxy (手机内) → route_vnc → serve_remote_vnc (device_id != local)
              → get_or_create_remote_conn(device_id)
              → P2pClient::connect(gateway_url, token, device_id)
              → punch_or_relay (打洞失败 → relay_request → connect_via_relay)
```

### 2.2 Relay 竞态（P2P 代码 Review 高 #2）

**Relay 协议要求**：PC 先 `RegisterPc`，手机再 `ConnectRequest`。session 由 PC 注册创建。

**实际时序**：

1. 手机 → Gateway `POST /api/p2p/relay-request` → 立即返回 `relay_url` + `session_id`
2. Gateway 异步推 `connect_relay` 给 PC
3. 手机立刻 `connect_via_relay(session_id, Mobile)` → 发送 `ConnectRequest`
4. PC 收到推送后需时间：建立 QUIC → 发送 `RegisterPc`

手机往往先连到 relay，此时 session 尚未注册 → relay 返回 `"PC offline or session expired"` → `connect_via_relay` 失败 → 错误向上传播 → VncProxy 的 `route_vnc` 返回 Err → WebSocket 被 drop → 前端看到「连接被对方重置」。

### 2.3 其他可能原因

| 原因 | 说明 |
|------|------|
| my-devices 无在线设备 | PC 未运行 NovAIC 或未心跳，`device_id` 取不到 |
| Gateway RELAY_URL 未配置 | `jwt_secret.env` 未设置 RELAY_URL，relay_request 可能失败 |
| relay 服务异常 | 未部署修复版本，Relay 持续 panic |
| **PC CloudBridge 未连接** | relay-request 需推 connect_relay 给 PC，若 CloudBridge 断开则 503 |

---

## 三、代码 Review 要点（与本次问题相关）

### 高优先级

| # | 问题 | 状态 | 建议 |
|---|------|------|------|
| 1 | CloudBridge token 快照，长连接下 JWT 可能过期 | 建议修复 | connect_relay 时从 `cloud_token.read().await` 重新读取 |
| 2 | **Relay 竞态：手机先连 relay 会失败** | **本次根因** | 手机 connect_via_relay 失败时重试（2s/4s/8s 指数退避） |
| 3 | IPv6 relay_url 解析错误 | 待修复 | `https://[::1]:443` 时 `format!("{}:{}", host, port)` 会出错 |
| 4 | tunnel resource_id 超 255 字节 u8 溢出 | 待修复 | 校验 `resource_id.len() <= 255` |

### 中优先级

| # | 问题 |
|---|------|
| 5 | relay 超时 30s/15s 可能不足，无重试 |
| 6 | P2P 未启动时本地 VNC 提示不明确 |

---

## 四、修复建议

### 4.1 立即：Relay 竞态重试（已实现）

在 `punch_or_relay` 中，`connect_via_relay` 失败时增加指数退避重试（2s、4s、8s），给 PC 时间完成 `RegisterPc`。

### 4.2 部署

1. **novaic-quic-service**：确认服务器已部署含 CryptoProvider 修复的版本。
2. **Gateway**：确认 `jwt_secret.env` 中 `RELAY_URL=https://relay.gradievo.com/p2p/relay` 已配置。
3. **PC 端**：确保 NovAIC 正在运行，心跳正常，Gateway 能推 `connect_relay`。

### 4.3 调试顺序

1. 确认 PC 在线：`GET /api/p2p/my-devices`（带 JWT）应返回 `online: true` 的设备。
2. 确认 Relay 正常：`journalctl -u novaic-quic-service -f` 无 panic。
3. 手机连接时观察 relay 日志，是否有 `PC registered`、`Paired session` 等。

---

## 五、相关文件

| 文件 | 说明 |
|------|------|
| `novaic-app/src-tauri/src/commands/vnc_urls.rs` | get_vnc_proxy_url，移动端从 my-devices 取 device_id |
| `novaic-app/src-tauri/src/vnc_proxy.rs` | route_vnc, serve_remote_vnc, get_or_create_remote_conn |
| `novaic-app/src-tauri/p2p/src/relay.rs` | relay 竞态重试（punch_or_relay），首次尝试前 2s 延迟 |
| `novaic-app/src-tauri/p2p/src/rendezvous.rs` | relay_request, locate |
| `novaic-quic-service/src/main.rs` | CryptoProvider 修复 |
| `novaic-gateway/gateway/api/p2p.py` | relay-request, my-devices |

---

## 六、Relay 连接失败排查步骤

1. **确认 PC 端 NovAIC 已启动且 CloudBridge 已连接**
   - PC 必须登录且保持 WebSocket 连接，Gateway 才能推送 connect_relay
   - 若 relay-request 返回 503 "target device CloudBridge not connected"，说明 PC 未连接

2. **确认 relay 服务正常**
   ```bash
   ssh -p 52222 root@47.243.221.45 'journalctl -u novaic-quic-service -n 50 --no-pager'
   ```
   - 成功时应有 `PC registered`、`Paired session`
   - 失败时常见：`Connection failed: aborted by peer`（QUIC 握手失败）、`Handler error: timed out`（15s 超时）

3. **确认 Gateway 配置**
   - `jwt_secret.env` 中 `RELAY_URL=https://relay.gradievo.com/p2p/relay`
   - relay 服务器 UDP 443、3478 已放行（防火墙）

4. **确认 my-devices 有在线设备**
   ```bash
   curl -H "Authorization: Bearer <JWT>" https://api.gradievo.com/api/p2p/my-devices
   ```
   应返回 `online: true` 的设备

5. **Relay 竞态：手机先连会失败**
   - 已修复：首次 connect_via_relay 前等待 2s，失败时重试 2s/4s/8s
   - 若仍失败，可尝试：手机点连接后稍等几秒再点；或确保 PC 端 NovAIC 在前台运行
