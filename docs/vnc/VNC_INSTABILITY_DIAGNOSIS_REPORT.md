# VNC 连接不稳定问题诊断报告

**诊断时间**: 2026-03-11  
**参与诊断**: 6 名 subagent（连接流、P2P/relay、错误处理、VmControl、移动端、连接池）

---

## 一、执行摘要

VNC「经常连不上」由**多层问题叠加**导致，涉及：协议层、P2P/relay、连接池、VmControl、移动端、错误反馈。本报告按严重程度整理，并标注**独到发现**。

---

## 二、高严重度问题（优先修复）

### 2.1 【独到】Relay session 过期与重试冲突

| 项目 | 说明 |
|------|------|
| **位置** | `p2p/relay.rs` B8/B10 |
| **现象** | 第一次 relay 失败后，重试 2/3/4 仍用同一个 `session_id`，但 Gateway/relay 的 session TTL 仅 **10 秒** |
| **根因** | `relay_request` 只调用一次；`connect_via_relay` 重试间隔 2s+4s+8s=14s，第一次尝试本身可能耗时 ~30s，session 早已过期 |
| **影响** | 重试必然失败，表现为「偶尔能连、多数时候连不上」 |

**建议**：在收到「invalid or expired session」时，重新调用 `relay_request` 获取新 `session_id` 再重试。

---

### 2.2 relay_request 无重试

| 项目 | 说明 |
|------|------|
| **位置** | `relay.rs:189`, `rendezvous.rs:246-276` |
| **现象** | `relay_request` 只请求一次，`locate`/`heartbeat` 有 3 次重试 |
| **影响** | Gateway 短暂 503、网络抖动时，直接失败，无自动恢复 |

---

### 2.3 PC 端 relay 连接无重试

| 项目 | 说明 |
|------|------|
| **位置** | `cloud_bridge.rs:279-302` |
| **现象** | PC 收到 `connect_relay` 后只发起一次 `connect_via_relay`，失败仅打日志 |
| **影响** | 手机已连上 relay，PC 端一次失败即整条链路失败 |

---

### 2.4 连接池无健康检查，复用死连接

| 项目 | 说明 |
|------|------|
| **位置** | `vnc_proxy.rs` local_conn / remote_conns |
| **现象** | 只检查 `close_reason().is_none()`，无 ping/健康探测 |
| **影响** | NAT 超时、休眠唤醒、网络切换后，缓存的 QUIC 连接已死，首次使用必失败 |

---

### 2.5 错误不传回前端

| 项目 | 说明 |
|------|------|
| **位置** | `vnc_proxy.rs:243-245` |
| **现象** | `send_ws_close` 使用 `Message::Close(None)`，无 reason/code |
| **影响** | 前端只能看到「连接关闭」，无法区分「设备离线」「VNC socket 不存在」等 |

---

### 2.6 get_vnc_proxy_url 无 .catch()

| 项目 | 说明 |
|------|------|
| **位置** | `vncStream.ts` / `scrcpyStream.ts:371-373` |
| **现象** | `invoke('get_vnc_proxy_url').then(...)` 无 `.catch()` |
| **影响** | proxy 未启动、无在线设备时，Promise 被 reject 且无处理，用户无任何提示 |

---

### 2.7 VncProxy bind 失败时 port_tx 未发送

| 项目 | 说明 |
|------|------|
| **位置** | `vnc_proxy.rs:119-123` |
| **现象** | `TcpListener::bind` 失败时直接 return，`port_tx.send` 从未调用 |
| **影响** | setup 3s 超时后只得到「Failed to get assigned port」，真实原因（端口占用等）只在 stderr |

---

### 2.8 find_vnc_target TOCTOU，无重试

| 项目 | 说明 |
|------|------|
| **位置** | `p2p/tunnel.rs:86-102` |
| **现象** | `Path::exists()` 后 `connect()`，VM 可能在中间关闭；socket 可能尚未创建 |
| **影响** | VM 刚启动或刚关闭时，连接极易失败 |

---

### 2.9 移动端多 PC：总是选第一个在线设备

| 项目 | 说明 |
|------|------|
| **位置** | `vnc_urls.rs:46-54` |
| **现象** | `my-devices` 取第一个 `online=true` 的 device_id |
| **影响** | 多台 PC 时，可能连到错误的机器；缺少 VM/agent → host 映射 |

---

### 2.10 VM 启动与 VNC socket 竞态

| 项目 | 说明 |
|------|------|
| **位置** | `vmcontrol/api/routes/vm.rs` |
| **现象** | QEMU 启动后 VNC socket 创建有延迟；启动前只清理 QMP socket，不清理 VNC socket |
| **影响** | 用户过早点 VNC 时 socket 尚不存在；旧 VNC socket 残留导致 connect 失败 |

---

## 三、中严重度问题

### 3.1 get_or_create_remote_conn 持锁时间过长

| 项目 | 说明 |
|------|------|
| **位置** | `vnc_proxy.rs:398-436` |
| **现象** | 整个 P2P connect（15–30s+）期间持有 `remote_conns` 锁 |
| **影响** | 同设备或不同设备的并发 VNC 请求被串行化，体验卡顿 |

---

### 3.2 多处 connect 无超时

| 项目 | 说明 |
|------|------|
| **位置** | `tunnel.rs` UnixStream/TcpStream connect；`vmcontrol/vnc` UnixStream connect |
| **现象** | 无 `tokio::time::timeout` |
| **影响** | QEMU/VmControl 卡住时，连接可能无限阻塞 |

---

### 3.3 WebSocket 升级无超时

| 项目 | 说明 |
|------|------|
| **位置** | Axum WebSocketUpgrade |
| **现象** | `route_vnc` 若在 P2P/QUIC 上卡住，handler 可一直阻塞 |
| **影响** | 前端长时间无响应 |

---

### 3.4 前端 15s 与后端 15–60s 超时不匹配

| 项目 | 说明 |
|------|------|
| **位置** | `scrcpyStream.ts:397` vs `relay.rs` |
| **现象** | 前端 15s 超时，P2P+relay 可能需 30–60s |
| **影响** | 后端仍在尝试时，前端已放弃并显示失败 |

---

### 3.5 移除坏连接时的竞态

| 项目 | 说明 |
|------|------|
| **位置** | `vnc_proxy.rs:385-391, 313-318` |
| **现象** | `open_vnc_stream` 失败后 spawn 任务移除 conn，另一请求可能在移除前拿到同一坏 conn |
| **影响** | 连续多次失败，直到坏连接被移除 |

---

### 3.6 移动端 QUIC 连接在后台失效

| 项目 | 说明 |
|------|------|
| **位置** | `vnc_proxy.rs` remote_conns |
| **现象** | 切后台后系统可能关闭网络，缓存的 Connection 失效 |
| **影响** | 恢复前台后第一次 VNC 请求大概率失败 |

---

### 3.7 VNC socket 残留未清理

| 项目 | 说明 |
|------|------|
| **位置** | `vm.rs` 启动 VM 前 |
| **现象** | 只清理 QMP socket，不清理 VNC socket |
| **影响** | 异常退出后残留的 VNC socket 可能导致 connect 失败 |

---

## 四、低严重度问题

| # | 问题 | 位置 |
|---|------|------|
| 1 | 端口分配超时提示过于笼统 | setup.rs |
| 2 | VncTarget::NotFound 未通过 WS Close 传回 | tunnel.rs |
| 3 | wsUrl 缓存无失效策略 | vncStream.ts |
| 4 | 移动端未使用 RelayOnly，打洞常失败 | p2p/config.rs |
| 5 | p2p_setup_error 的 device_id 语义可能混淆 | vnc_proxy.rs |

---

## 五、问题分布总览

| 层级 | 高 | 中 | 低 |
|------|----|----|-----|
| P2P/Relay | 3 | 2 | 1 |
| 连接池 | 1 | 2 | 0 |
| VncProxy | 2 | 2 | 1 |
| VmControl/Tunnel | 2 | 2 | 1 |
| 前端 | 1 | 1 | 1 |
| 移动端 | 1 | 1 | 2 |

---

## 六、修复优先级建议

### P0（立即）

1. **Relay session 过期**：session 过期时重新 `relay_request` 再重试
2. **relay_request 重试**：2–3 次，带退避
3. **PC relay 重试**：cloud_bridge 中 `connect_via_relay` 失败时重试
4. **连接池健康检查**：复用前检查或加 TTL（如 4–5 分钟）

### P1（短期）

5. **错误回传**：`send_ws_close` 带 reason，前端展示具体错误
6. **invoke .catch**：`get_vnc_proxy_url` 等 invoke 加 `.catch()` 并提示用户
7. **Unix/TCP connect 超时**：5–10s
8. **VM 启动时清理 VNC socket**：与 QMP 一致

### P2（中期）

9. **find_vnc_target 重试**：socket 不存在时短时重试
10. **get_or_create_remote_conn 锁优化**：连接建立时释放锁或使用条件变量
11. **前端超时**：与后端对齐或延长到 30–45s
12. **多 PC 设备选择**：支持指定目标设备或 VM→host 映射

---

## 七、独到发现汇总（有奖项）

| 发现 | 贡献者 | 说明 |
|------|--------|------|
| **Relay session TTL 与重试时序冲突** | P2P agent | 10s TTL vs 14s+ 重试间隔，导致重试必失败 |
| **PC 端 relay 无重试** | P2P agent | 手机已连 relay，PC 一次失败即全链路失败 |
| **移除坏连接时的竞态** | 连接池 agent | 并发请求可能复用同一坏连接 |
| **VncProxy bind 失败不通知** | 连接流 agent | port_tx 未发送，真实原因被掩盖 |
| **移动端多 PC 选错设备** | 移动端 agent | 缺少 VM→host 映射，多 PC 场景必错 |
| **VM 启动不清理 VNC socket** | VmControl agent | 与 QMP 处理不一致，残留 socket 影响连接 |

---

*报告由 6 名 subagent 并行诊断后汇总生成。*
