# 第三轮调研：P2P 竞态与错误处理

**调研时间**: 2026-03-12  
**范围**: relay_request 与 connect_relay 时序竞态、Relay session 过期/重复请求、错误传播与用户可见反馈

---

## 一、relay_request 与 connect_relay 推送的时序竞态

### 1.1 流程概览

```
Mobile (VNC)                    Gateway                     PC (CloudBridge)              Relay
     |                              |                              |                        |
     |  POST /relay-request         |                              |                        |
     |  ───────────────────────────>|                              |                        |
     |                              |  send_push(connect_relay)     |                        |
     |                              |  ───────────────────────────>|                        |
     |  {relay_url, session_id}     |  (await 完成 = 写入 WS 缓冲)   |  spawn connect_via_relay|
     |  <───────────────────────────|                              |  QUIC + RegisterPc     |
     |                              |                              |  ─────────────────────>|
     |  connect_via_relay           |                              |                        |
     |  (ConnectRequest)             |                              |                        |
     |  ─────────────────────────────────────────────────────────────────────────────────>|
     |                              |                              |                        |
     |  RACE: PC 未 RegisterPc 时手机已 ConnectRequest → "PC offline or session expired"
```

### 1.2 已知竞态点

| # | 竞态点 | 位置 | 说明 |
|---|--------|------|------|
| **R1** | **Gateway 返回 ≠ PC 已收到** | `p2p.py:265-279` | `send_push_to_device` 完成 = `ws.send_json()` 成功 = 写入 TCP 缓冲，**非** PC 已接收/处理。PC 断连或网络抖动时，推送可静默丢失。 |
| **R2** | **手机立即连接 vs PC 建连耗时** | `relay.rs:181-188` | 手机 `connect_via_relay_only` 无固定延迟，立即尝试。PC 需：收推送 → 解析 → spawn → DNS → QUIC 握手(30s) → RegisterPc。慢网下 5–15s 常见。 |
| **R3** | **Relay 等待 PC 时间窗** | `novaic-quic-service/relay.rs:222-239` | Relay 对 ConnectRequest 轮询等待 PC 最多 **10s**（`WAIT_FOR_PC_TIMEOUT`）。若 PC 在 10s 内未 RegisterPc，返回 "PC offline or session expired"。 |
| **R4** | **Gateway session TTL vs 实际建连时间** | `p2p.py:70-81` | `_PENDING_SESSION_TTL_SECS = 10`。relay `validate_relay_session` 调用 Gateway `/validate-relay-session`，过期即 404。PC 建连若超过 10s，session 已失效。 |
| **R5** | **推送静默丢失** | `CLOUDBRIDGE_RELAY_PUSH_REVIEW.md` | PC 在 Gateway 发送后、接收前断连 → TCP 缓冲数据丢失 → PC 永远收不到 connect_relay，手机拿到的 session_id 无效。 |

### 1.3 当前缓解措施

| 措施 | 位置 | 效果 |
|------|------|------|
| Relay 长等待 | `novaic-quic-service/relay.rs:222-239` | 手机 ConnectRequest 时若 PC 未注册，轮询等待最多 10s |
| 手机重试 + session 刷新 | `relay.rs:181-239` | 4 次尝试；session 错误时重新 `relay_request` 获取新 session |
| PC 端重试 | `cloud_bridge.rs:286-316` | 3 次重试，500ms × attempt 退避 |

### 1.4 仍存在的缺口

- **R1/R5**：无 ACK 机制，Gateway 无法确认 PC 已收到推送；推送丢失时手机无感知。
- **R2**：手机首次尝试无延迟，依赖 Relay 10s 等待；若 Relay 与 Gateway session TTL 不一致（均为 10s 但起算点不同），可能提前失败。
- **R4**：Gateway 与 Relay 的 session TTL 均为 10s，PC 建连慢时易过期；PC 端 3 次重试用同一 session_id，session 过期后重试无效。

---

## 二、Relay 端 session 过期与重复请求处理

### 2.1 Session 生命周期

| 组件 | TTL | 起算 | 清理方式 |
|------|-----|------|----------|
| Gateway `_pending_relay_sessions` | 10s | `relay_request` 创建时 | `validate_relay_session` 调用时若 `is_expired()` 则 pop 并 404 |
| Relay `pc_registry` (PcEntry) | 10s | PC RegisterPc 时 | `registered_at.elapsed() > SESSION_TTL` 则拒绝；ConnectRequest 轮询时 `retain` 清理过期条目 |

### 2.2 重复请求场景

| 场景 | 行为 | 结果 |
|------|------|------|
| **同一 session_id 的 ConnectRequest 两次** | Relay 第一次 `pc_registry.remove(session_id)` 消费 session；第二次无 entry | 第二次返回 "PC offline or session expired" ✓ 符合预期 |
| **同一 session_id 的 RegisterPc 两次** | `reg.insert(session_id, PcEntry)` 覆盖；同一 PC 重复注册会覆盖自身 | 一般不会发生（单 CloudBridge 单 session） |
| **同一 target 多次 relay_request** | 每次生成新 `session_id`，各自独立 | 多 session 并存，无冲突 ✓ |
| **手机重试用旧 session** | 第一次失败后 2s/4s/8s 退避重试，若未触发 session 刷新则仍用旧 session | **缺口**：旧 session 可能已过期，重试无效 |

### 2.3 Session 过期与重试冲突（已部分修复）

**原问题**（`VNC_INSTABILITY_DIAGNOSIS_REPORT.md`）：  
第一次 relay 失败后，重试 2/3/4 仍用同一 `session_id`，Gateway/relay TTL 仅 10s，重试间隔 2+4+8=14s，session 早已过期。

**当前实现**（`relay.rs:206-224`）：  
- 仅当错误明确包含 `"session"` 或 `"expired"`（排除 `"Invalid JWT"`、`"Invalid handshake"`）时，才重新 `relay_request` 获取新 session。
- 避免误判：`err_lower.contains("invalid")` 曾误匹配 "Invalid JWT"，已收紧为 `is_session_error`。

**仍存在的缺口**：  
- PC 端 `cloud_bridge.rs` 的 3 次重试**始终用同一 session_id**，无 session 刷新逻辑。  
- 若 PC 第一次失败因 session 过期，后续重试必然失败。

### 2.4 重复 relay_request 的并发

- 用户快速双击 VNC → 两次 `relay_request` → 两个 session_id，两次 push。  
- PC 收到两个 ConnectRelay，spawn 两个 `connect_via_relay`，分别 RegisterPc。  
- 手机通常只使用第一次返回的 session_id，第二次 session 被浪费但无副作用。  
- **无去重**：同一 target 的并发 relay_request 会创建多个 session，可考虑短期防抖（如 2s 内同 target 复用 session），当前未实现。

---

## 三、错误传播：relay 失败时前端的用户可见反馈

### 3.1 错误传播路径

```
get_or_create_remote_conn 失败
    → serve_remote_vnc / serve_remote_scrcpy 捕获 Err
    → send_ws_close_with_reason(ws, e.to_string())
    → WebSocket Close 帧 (code=1011, reason=错误文案)
    → 前端 WebSocket onclose / RFB disconnect
    → setErrorMsg / notifySubscribers
```

### 3.2 后端是否发送具体错误？

| 层级 | 行为 | 代码位置 |
|------|------|----------|
| VncProxy | `get_or_create_remote_conn` 失败 → `send_ws_close_with_reason(ws, e.to_string())` | `vnc_proxy.rs:437-439, 361-363` |
| 错误内容 | `anyhow::anyhow!("Remote P2P connect failed: {}", e)`，含 relay/rendezvous 的具体错误 | `vnc_proxy.rs:392` |

**结论**：后端**会**通过 WebSocket Close 的 reason 传递具体错误（如 "Relay rejected: PC offline or session expired"）。

### 3.3 前端是否展示？

| 路径 | 组件 | 是否展示 reason | 说明 |
|------|------|------------------|------|
| **VNC (createVncTransport)** | useVnc, AgentDesktopView | **部分** | `rfb.addEventListener('disconnect', ...)` 使用 `e?.detail?.reason`。**RFB.js 可能不暴露 WebSocket close reason**（见 `VNC_ERROR_HANDLING_AUDIT.md`），用户可能只看到通用 "Connection lost"。 |
| **VNC (vncStream)** | VNCViewShared, 缩略图 | **部分** | `disconnect` 时 `reason` 来自 `e?.detail?.reason ?? e?.reason`；若 RFB 不传，则无具体错误。 |
| **Scrcpy** | ScrcpyStream | **✓** | `ws.onclose` 直接读 `e.reason`，`notifySubscribers(state, 'error', reason)`，用户可见具体错误。 |

### 3.4 错误传播缺口汇总

| # | 缺口 | 影响 |
|---|------|------|
| **E1** | **invoke 失败无 .catch** | `get_vnc_proxy_url` 失败时，部分调用链无 `.catch()`，Promise reject 无处理，用户无提示（"Starting…" 一直转圈） |
| **E2** | **RFB disconnect 不暴露 close reason** | VNC 路径即使后端发送了 Close reason，RFB 的 disconnect 事件可能不包含，前端无法展示 "PC offline or session expired" 等 |
| **E3** | **get_vnc_proxy_url 成功但 WebSocket 失败** | URL 获取成功，但 `get_or_create_remote_conn` 在 WS 升级后失败；此时通过 Close 帧传 reason，依赖 E2 的 RFB 行为 |
| **E4** | **PC 端 relay 失败无反馈到手机** | CloudBridge `connect_via_relay` 失败仅打日志，不通过任何信道通知手机；手机可能已连上 relay 等待，最终超时或 "PC offline" |

---

## 四、已知竞态点与错误处理缺口总览

### 4.1 竞态点

| ID | 竞态点 | 严重度 | 建议 |
|----|--------|--------|------|
| R1 | Gateway 返回 ≠ PC 已收到推送 | 高 | 增加 PC→Gateway ACK，或推送重试 |
| R2 | 手机立即连接 vs PC 建连耗时 | 高 | 已缓解（Relay 10s 等待）；可考虑手机侧短延迟 |
| R3 | Relay 等待 PC 仅 10s | 中 | 慢网可能不足；可考虑 15–20s |
| R4 | Session TTL 10s vs 建连耗时 | 高 | PC 重试需支持 session 刷新；或延长 TTL |
| R5 | 推送静默丢失 | 高 | 同 R1 |

### 4.2 错误处理缺口

| ID | 缺口 | 严重度 | 建议 |
|----|------|--------|------|
| E1 | invoke 失败无 .catch | 高 | 所有 `get_vnc_proxy_url` / `get_scrcpy_proxy_url` 调用加 `.catch()` 并 `setErrorMsg` |
| E2 | RFB 不暴露 WebSocket close reason | 中 | 检查 RFB 源码；若无则考虑在 RFB 前加一层 WS 包装，或改用自定义协议传 reason |
| E3 | URL 成功但 WS 建连失败 | 中 | 依赖 E2；Close 帧已有 reason |
| E4 | PC relay 失败无反馈到手机 | 中 | 设计 PC→Gateway→手机 的失败通知（或手机端超时文案更明确） |

### 4.3 相关文件索引

| 组件 | 文件 |
|------|------|
| Gateway relay-request | `novaic-gateway/gateway/api/p2p.py` |
| Gateway session 校验 | `p2p.py:283-304` |
| PC CloudBridge connect_relay | `novaic-app/src-tauri/vmcontrol/src/cloud_bridge.rs:279-321` |
| 手机 relay 连接 + 重试 | `novaic-app/src-tauri/p2p/src/relay.rs` |
| Relay 服务端 | `novaic-quic-service/src/relay.rs` |
| VncProxy 错误发送 | `novaic-app/src-tauri/src/vnc_proxy.rs:290-300, 437-439` |
| 前端 useVnc / vncStream | `novaic-app/src/hooks/useVnc.ts`, `novaic-app/src/services/vncStream.ts` |
| Scrcpy 错误展示 | `novaic-app/src/services/scrcpyStream.ts:505-520` |

---

## 五、与既有文档的对照

| 文档 | 与本轮调研的对应 |
|------|------------------|
| `P2P_RELAY_RACE_ANALYSIS.md` | R1–R4 的详细时间线分析 |
| `CLOUDBRIDGE_RELAY_PUSH_REVIEW.md` | R1、R5 推送语义与静默丢失 |
| `VNC_INSTABILITY_DIAGNOSIS_REPORT.md` | Session 过期与重试冲突（已部分修复） |
| `VNC_ERROR_HANDLING_AUDIT.md` | E2 RFB 不暴露 close reason |
| `VNC_OTA_ERROR_PROPAGATION_REPORT.md` | E1 invoke 失败与前端静默 |
| `P2P_SERVER_ISSUE_REPORT.md` | session 错误匹配过宽（已修复）、PC 重试用同一 session |

---

*报告由代码与既有文档交叉分析生成。*
