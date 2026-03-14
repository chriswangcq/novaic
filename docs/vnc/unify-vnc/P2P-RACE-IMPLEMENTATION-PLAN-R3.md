# P2P 竞态修复 Round 3 实施计划

**文档版本**: R3 最终定稿  
**创建时间**: 2026-03-12  
**输入**: P2P-R1R5-PUSH-ACK-DESIGN-R2、P2P-R2R3-MOBILE-DELAY-RELAY-WAIT-DESIGN-R2、P2P-R4-PC-SESSION-REFRESH-DESIGN-R2、P2P-E2-RFB-CLOSE-REASON-DESIGN-R2、P2P-RACE-DESIGN-REVIEW-R2

---

## 1. 实施顺序总览

按 R2 Review 建议，实施顺序为：

| 阶段 | 方案 | 依赖 | 可并行 |
|------|------|------|--------|
| **1** | R2/R3（20s TTL + 2s 手机延迟） | 无 | 可与 E2 并行 |
| **2** | R4（relay-refresh-for-pc） | R2/R3 的 TTL=20s | — |
| **3** | R1/R5（ACK 推送确认） | 无强依赖，建议 R2/R3 上线后 | 可与 E2 并行 |
| **4** | E2（RFB Close Reason） | 无 | 可与 1–3 任意阶段并行 |

**依赖图**：

```
                    ┌─────────────┐
                    │   E2        │  独立，无依赖
                    │ RFB reason  │
                    └──────┬──────┘
                           │
┌─────────────┐     ┌──────┴──────┐     ┌─────────────┐
│  R2/R3      │     │             │     │   R4        │
│ 20s + 2s    │────>│  TTL 统一   │<────│  refresh    │
│ 延迟        │     │  20s        │     │  延长=20s   │
└──────┬──────┘     └──────┬──────┘     └──────┬──────┘
       │                   │                   │
       v                   v                   v
┌─────────────────────────────────────────────────────┐
│  R1/R5 ACK                                          │
│  可与 R2/R3、R4 并行开发；建议 R2/R3 上线后再上      │
└─────────────────────────────────────────────────────┘
```

---

## 2. 任务拆解

### 2.1 R2/R3：手机 2s 延迟 + Relay/Gateway 20s TTL

| 任务 ID | 任务描述 | 文件 | 验收标准 | 预估工时 |
|---------|----------|------|----------|----------|
| R2R3-1 | Gateway `_PENDING_SESSION_TTL_SECS` 10→20 | `novaic-gateway/gateway/api/p2p.py` | 常量改为 20，单元/集成测试通过 | 5min |
| R2R3-2 | novaic-quic-service `WAIT_FOR_PC_TIMEOUT` 10→20 | `novaic-quic-service/src/relay.rs` | 第 223 行常量改为 20 | 5min |
| R2R3-3 | novaic-quic-service `SESSION_TTL` 10→20 | `novaic-quic-service/src/relay.rs` | 第 25 行常量改为 20 | 5min |
| R2R3-4 | novaic-app `connect_via_relay_only` 增加 `INITIAL_DELAY_SECS=2` | `novaic-app/src-tauri/p2p/src/relay.rs` | 每次 `relay_request` 返回后、首次 connect 前 sleep(2s)；session 错误触发新 relay_request 后，新一轮 connect 前也 sleep(2s)；失败重试（非 session 错误）用 2/4/8s 退避，无 2s 初始延迟 | 15min |
| R2R3-5 | 慢网模拟测试 | — | tc 限速或人工慢网，验证 PC 建连 5–15s 场景成功率提升 | 30min |

**R2R3-4 实现要点**：

```rust
// relay.rs connect_via_relay_only 内
const INITIAL_DELAY_SECS: u64 = 2;

// relay_request 返回后、首次 connect 前
let relay_resp = crate::rendezvous::relay_request(...).await?;
tokio::time::sleep(Duration::from_secs(INITIAL_DELAY_SECS)).await;

// 循环内：session 错误触发 relay_request 后
if is_session_error && attempt < 4 {
    match crate::rendezvous::relay_request(...).await {
        Ok(new_resp) => {
            current_relay_resp = new_resp;
            tokio::time::sleep(Duration::from_secs(INITIAL_DELAY_SECS)).await;  // 新 session 新延迟
            retry_immediately = true;
        }
        ...
    }
}
```

**总预估**：约 1h（含联调与测试）

---

### 2.2 R4：PC Session Refresh（relay-refresh-for-pc）

| 任务 ID | 任务描述 | 文件 | 验收标准 | 预估工时 |
|---------|----------|------|----------|----------|
| R4-1 | Gateway 增加 `_device_to_session: Dict[str, str]` | `novaic-gateway/gateway/api/p2p.py` | relay_request 创建 session 时写入；validate 时 is_expired 且 pop 时，**先** `_device_to_session.pop(target_device_id)`，**再** `_pending_relay_sessions.pop(session_id)` | 20min |
| R4-2 | Gateway 实现 `POST /api/p2p/relay-refresh-for-pc` | `novaic-gateway/gateway/api/p2p.py` | 校验 device_id、JWT；查找 `_device_to_session`；重置 `created_at = time.time()`（延长量 = `_PENDING_SESSION_TTL_SECS`）；返回 `{ ok, session_id, relay_url }`；404/403 正确返回 | 30min |
| R4-3 | PC vmcontrol 增加 `relay_refresh_for_pc` | `novaic-app/src-tauri/p2p/src/rendezvous.rs` 或 `vmcontrol` | 函数签名 `relay_refresh_for_pc(gateway_url, jwt, device_id) -> Result<RelayRefreshResponse>` | 15min |
| R4-4 | PC cloud_bridge ConnectRelay 失败时调用 refresh | `novaic-app/src-tauri/vmcontrol/src/cloud_bridge.rs` | `is_session_error` 与 relay.rs 一致（含 session、expired 排除 certificate/invalid）；失败且 is_session_error 时调用 refresh，成功则用 refresh 返回的 session_id 继续重试；refresh 404 时 fallback 原重试 | 30min |
| R4-5 | 联调与测试 | — | 模拟 session 过期、validate 404 场景，验证 refresh 后重试成功 | 30min |

**R4-4 is_session_error 参考**（与 relay.rs:198-199 一致）：

```rust
let is_session_error = |e: &str| {
    let lower = e.to_lowercase();
    (lower.contains("session") || (lower.contains("expired") && !lower.contains("certificate")))
        && !lower.contains("invalid");
};
```

**总预估**：约 2.5h

---

### 2.3 R1/R5：推送 ACK 确认

| 任务 ID | 任务描述 | 文件 | 验收标准 | 预估工时 |
|---------|----------|------|----------|----------|
| R1R5-1 | PC CloudBridge IncomingMessage 增加 `push_id: Option<String>` | `novaic-app/src-tauri/vmcontrol/src/cloud_bridge.rs` | ConnectRelay 解析 push_id；收到后若存在 push_id，**先**发送 `connect_relay_ack { push_id }`，**再** tokio::spawn connect_via_relay | 20min |
| R1R5-2 | Gateway pc_client 处理 `connect_relay_ack` | `novaic-gateway/gateway/api/internal/pc_client.py` | `_handle_device_message` 识别 `connect_relay_ack`，以 **push_id** 为 key resolve 对应 Future | 25min |
| R1R5-3 | Gateway pc_client 新增 `send_push_and_wait_ack` | `novaic-gateway/gateway/api/internal/pc_client.py` | 注册 Future（key=push_id）、发送 connect_relay、等待 ACK，超时 5s；参考 proxy_response 模式 | 30min |
| R1R5-4 | Gateway p2p `p2p_relay_request` 改用 `send_push_and_wait_ack` | `novaic-gateway/gateway/api/p2p.py` | 生成 push_id，调用 send_push_and_wait_ack；超时返回 503 "Failed to deliver connect_relay to device" | 20min |
| R1R5-5 | 推送格式增加 push_id | `novaic-gateway` + `novaic-app` | `{"type":"connect_relay","push_id":"uuid","relay_url":"...","session_id":"..."}` | 含于 R1R5-1/2/3/4 |
| R1R5-6 | 联调与测试 | — | 正常 ACK 流程；超时 503；旧 PC 不发送 ACK 时 Gateway 超时 503 | 30min |

**总预估**：约 2.5h

---

### 2.4 E2：RFB Close Reason 透传

| 任务 ID | 任务描述 | 文件 | 验收标准 | 预估工时 |
|---------|----------|------|----------|----------|
| E2-1 | 安装 patch-package | `novaic-app/package.json` | 添加 `patch-package` 依赖，postinstall 中 `patch-package` | 5min |
| E2-2 | 手动验证 noVNC patch 逻辑 | `node_modules/@novnc/novnc/core/rfb.js` | 在 _socketClose 开头设 `_rfbCloseReason`；_fail 中仅当未设置时写入；disconnect 派发时加入 reason | 15min |
| E2-3 | 验证 bridge 模式 | OTA 模式 | 确认 VncBridgeTransport 下 `e.reason` 经 patch 后到达 disconnect detail | 15min |
| E2-4 | 生成 patch 文件 | `novaic-app/patches/@novnc+novnc@1.5.0.patch` | `npx patch-package @novnc/novnc` | 5min |
| E2-5 | pin @novnc/novnc 版本 | `novaic-app/package.json` | 固定版本（如 1.5.0），避免升级导致 patch 失效 | 5min |
| E2-6 | 回归测试 | — | OTA 模式、直连模式、P2P 失败场景，确认 "PC offline or session expired" 等可展示 | 20min |

**patch 内容要点**（rfb.js）：

1. 构造函数/`_connect` 中：`this._rfbCloseReason = ''`
2. `_socketClose` 开头：`this._rfbCloseReason = (e && e.reason) ? String(e.reason) : ''`
3. `_fail` 内：`this._rfbCloseReason = this._rfbCloseReason || (typeof details === 'string' ? details : '')`
4. disconnect 派发：`detail: { clean, reason: this._rfbCloseReason || '' }`

**总预估**：约 1h

---

## 3. 部署检查清单

### 3.1 TTL 同步（R2/R3 必须）

| 组件 | 常量/配置 | 目标值 | 文件 |
|------|-----------|--------|------|
| Gateway | `_PENDING_SESSION_TTL_SECS` | 20 | `novaic-gateway/gateway/api/p2p.py:70` |
| novaic-quic-service | `SESSION_TTL` | 20 | `novaic-quic-service/src/relay.rs:25` |
| novaic-quic-service | `WAIT_FOR_PC_TIMEOUT` | 20 | `novaic-quic-service/src/relay.rs:223` |

**对齐原则**：`WAIT_FOR_PC_TIMEOUT == SESSION_TTL == _PENDING_SESSION_TTL_SECS == 20s`

**部署顺序**：Gateway → novaic-quic-service（Relay）→ novaic-app（手机/PC）

**检查项**：

- [ ] Gateway 部署前确认 `_PENDING_SESSION_TTL_SECS = 20`
- [ ] novaic-quic-service 部署前确认 `SESSION_TTL`、`WAIT_FOR_PC_TIMEOUT` 均为 20
- [ ] 三者必须同版本发布或明确兼容矩阵，禁止 Gateway 20s + Relay 10s 混跑

### 3.2 版本兼容矩阵

| Gateway | novaic-quic-service | novaic-app (PC) | novaic-app (Mobile) | 行为 |
|---------|---------------------|-----------------|---------------------|------|
| 旧 (10s) | 旧 (10s) | 旧 | 旧 | 当前行为 |
| 新 (20s) | 新 (20s) | 旧 | 新 (2s 延迟) | 正常；手机 2s 延迟改善成功率 |
| 新 (20s) | 新 (20s) | 新 (R4 refresh) | 新 | 正常；PC 可 refresh |
| 新 (20s) | 旧 (10s) | — | — | **禁止**：Gateway 认为有效、Relay 已过期 |
| 旧 (10s) | 新 (20s) | — | — | **禁止**：Relay 等 20s 但 Gateway 10s 即过期 |

### 3.3 R1/R5 ACK 兼容矩阵

| Gateway | PC | 行为 |
|---------|-----|------|
| 旧（无 ACK） | 旧 | 当前行为 |
| 新（ACK 启用） | 旧 | Gateway 超时 503，提示升级 App |
| 新（ACK 禁用） | 新 | 旧行为，PC 发 ack 但 Gateway 忽略 |
| 新（ACK 启用） | 新 | 正常 ACK 流程 |

---

## 4. 回退方案

### 4.1 R2/R3 回退

| 步骤 | 操作 |
|------|------|
| 1 | Gateway：`_PENDING_SESSION_TTL_SECS` 20 → 10 |
| 2 | novaic-quic-service：`WAIT_FOR_PC_TIMEOUT`、`SESSION_TTL` 20 → 10 |
| 3 | novaic-app：移除 `INITIAL_DELAY_SECS` 的 sleep，或 `INITIAL_DELAY_SECS` 2 → 0 |
| 4 | 三者同版本回退，保持 TTL 一致 |

**可选**：通过环境变量 `P2P_INITIAL_DELAY_SECS=0` 关闭手机 2s 延迟，便于 A/B 或快速关闭。

### 4.2 R4 回退

| 步骤 | 操作 |
|------|------|
| 1 | Gateway：不部署 `relay-refresh-for-pc`，或新 API 返回 501 |
| 2 | PC：refresh 调用 404/501 时 fallback 到原有 3 次重试，行为不变 |
| 3 | 旧版 PC 无 refresh 逻辑，行为不变 |

### 4.3 R1/R5 回退

| 步骤 | 操作 |
|------|------|
| 1 | Gateway：环境变量 `P2P_PUSH_ACK_ENABLED=false` 回退到「发送即返回」行为 |
| 2 | 或：还原 `p2p_relay_request` 为 `send_push_to_device`，移除 `send_push_and_wait_ack` |
| 3 | PC：`push_id` 可选，旧版 PC 忽略；回退后 PC 发 ack 但 Gateway 忽略，无副作用 |

### 4.4 E2 回退

| 步骤 | 操作 |
|------|------|
| 1 | 移除 `patches/@novnc+novnc@x.x.x.patch` |
| 2 | 执行 `npm install` 恢复原始 @novnc/novnc |
| 3 | 前端 `e?.detail?.reason` 重新变为空，回退到通用错误文案 |

---

## 5. relay_request 最坏延迟 7s 说明与用户提示建议

### 5.1 延迟构成

| 阶段 | 延迟 | 说明 |
|------|------|------|
| R1/R5 ACK 超时 | 5s | Gateway 等待 PC 回执，超时返回 503 |
| R2 手机 2s 延迟 | 2s | relay_request 返回后、首次 connect 前 sleep |
| **最坏合计** | **7s** | 用户点击 VNC 后，relay_request 最坏 5s + 手机 2s = 7s 才发起 connect |

**正常路径**：ACK 通常 < 200ms（1 RTT），relay_request 总延迟约 0.2s + 2s = 2.2s。

### 5.2 用户提示建议

| 场景 | 建议文案 |
|------|----------|
| relay_request 进行中 | "正在连接 PC…"（可加 loading 动画） |
| relay_request 超时 503 | "无法联系到 PC，请确认 PC 已开机且 App 已登录" |
| connect 失败（含 session 错误） | 展示后端 reason（E2 实施后），如 "PC offline or session expired" |
| 首次连接等待 > 3s | 可选："网络较慢，正在建立连接…" |

**可选**：在 VNC 入口处增加「预计等待 2–7 秒」的轻提示，降低用户对首次连接延迟的焦虑。优先级：低。

---

## 6. 附录：相关代码位置速查

| 组件 | 文件 | 关键行/说明 |
|------|------|-------------|
| Gateway relay session | `novaic-gateway/gateway/api/p2p.py` | 70, 274–304 |
| Gateway pc_client | `novaic-gateway/gateway/api/internal/pc_client.py` | send_push_to_device, _handle_device_message |
| Relay 服务端 | `novaic-quic-service/src/relay.rs` | 25, 222–239 |
| 手机 relay 连接 | `novaic-app/src-tauri/p2p/src/relay.rs` | 155–239 |
| PC CloudBridge | `novaic-app/src-tauri/vmcontrol/src/cloud_bridge.rs` | 279–323 |
| noVNC | `node_modules/@novnc/novnc/core/rfb.js` | _socketClose, _fail, disconnect |
| 前端 useVnc | `novaic-app/src/hooks/useVnc.ts` | 112–134 |
| 前端 vncStream | `novaic-app/src/services/vncStream.ts` | 198–219 |

---

*Round 3 最终定稿。实施时按阶段 1→2→3 顺序推进，E2 可与任意阶段并行。*
