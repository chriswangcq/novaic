# P2P 剩余缺口与部署验证建议 Round 3

> **产出日期**: 2026-03-12  
> **输入**: docs/survey-2026/P2P_ARCHITECTURE_ROUND1.md、P2P_RELAY_TUNNEL_ROUND2.md、docs/unify-vnc/P2P-RACE-IMPLEMENTATION-PLAN-R3.md

---

## 1. 已实施修复的验证状态

以下修复已落地代码，**需人工或集成测试**确认，无法仅靠单元测试覆盖。

### 1.1 R2/R3：20s TTL + 2s 手机延迟

| 验证点 | 操作 | 预期 | 验证方式 |
|--------|------|------|----------|
| **慢网 PC 建连** | 模拟 PC 建连 5–15s（tc 限速或人工慢网） | 手机 2s 延迟后 connect，Relay 20s 内等到 PC，配对成功 | 集成测试 / 人工 |
| **TTL 一致性** | 检查 Gateway、Relay、novaic-app 常量 | `_PENDING_SESSION_TTL_SECS == SESSION_TTL == WAIT_FOR_PC_TIMEOUT == 20` | 部署前检查 |
| **新 session 新延迟** | session 错误触发 relay_request 刷新后 | 新一轮 connect 前再次 sleep(2s) | 代码审查 + 集成 |
| **非 session 错误退避** | 网络抖动导致 connect 失败 | 使用 2/4/8s 退避，无 2s 初始延迟 | 集成测试 |

**代码实施状态**：✅ 已实施  
- Gateway: `_PENDING_SESSION_TTL_SECS = 20`  
- novaic-quic-service: `SESSION_TTL = 20`, `WAIT_FOR_PC_TIMEOUT = 20`  
- novaic-app relay.rs: `INITIAL_DELAY_SECS = 2`，session 刷新后亦有 sleep

---

### 1.2 R1/R5：推送 ACK 确认

| 验证点 | 操作 | 预期 | 验证方式 |
|--------|------|------|----------|
| **正常 ACK** | 手机发起 VNC，PC 在线 | relay-request 约 0.2s+2s 内完成，VNC 正常连接 | 集成测试 |
| **ACK 超时** | PC 断网或 App 未启动时手机发起 VNC | relay-request 5s 后返回 503 "Failed to deliver connect_relay to device" | 集成测试 |
| **旧 PC 无 ACK** | Gateway 新版本 + 旧 PC（无 connect_relay_ack） | 5s 超时 503，需提示用户升级 App | 集成测试 |
| **P2P_PUSH_ACK_ENABLED=false** | 环境变量关闭 ACK | relay-request 立即返回，行为与旧版一致 | 集成测试 |
| **ACK 顺序** | PC 收到 connect_relay | 先 sink.send(ConnectRelayAck)，再 tokio::spawn connect_via_relay | 代码审查 |

**代码实施状态**：✅ 已实施  
- pc_client.py: `send_push_and_wait_ack`，5s 超时  
- cloud_bridge.rs: 有 push_id 时先发 ConnectRelayAck 再 spawn  
- pc_client.py: `connect_relay_ack` 以 push_id 为 key resolve Future

---

### 1.3 R4：PC Session Refresh

| 验证点 | 操作 | 预期 | 验证方式 |
|--------|------|------|----------|
| **session 过期后 refresh** | 人为延迟 PC 建连（如断网 15s 后恢复），或 mock validate 404 | PC 调用 relay_refresh_for_pc，续期后 connect_via_relay 成功 | 集成测试 |
| **refresh 404** | session 已 consume 或过期后 refresh | 404，PC fallback 原退避重试 | 集成测试 |
| **is_session_error 排除 invalid** | Relay 返回 "Invalid JWT" | 不触发 refresh，按普通错误退避 | 集成测试 |
| **_device_to_session 维护** | relay_request 创建 session 时 | 写入 `_device_to_session[target_device_id] = session_id` | 代码审查 |
| **pop 顺序** | validate 时 is_expired 且 pop | 先 `_device_to_session.pop`，再 `_pending_relay_sessions.pop` | 代码审查 |

**代码实施状态**：✅ 已实施  
- Gateway: `POST /api/p2p/relay-refresh-for-pc`，`_device_to_session`  
- rendezvous.rs: `relay_refresh_for_pc`  
- cloud_bridge.rs: is_session_error 时调用 refresh，用返回的 session_id 重试

---

### 1.4 E2：RFB Close Reason 透传

| 验证点 | 操作 | 预期 | 验证方式 |
|--------|------|------|----------|
| **正常断开** | VNC 连接后正常关闭 | 前端可展示 reason（若有） | 人工 |
| **PC offline / session expired** | connect 失败或 Relay 超时 | 前端展示 "PC offline or session expired" 等后端 reason | 集成测试 |
| **Bridge 模式** | OTA 模式（VncBridgeTransport） | `e.reason` 经 patch 后到达 disconnect detail | 集成测试 |
| **直连模式** | URL 直连 WebSocket | 同上 | 集成测试 |

**代码实施状态**：✅ 已实施  
- patches/@novnc+novnc+1.5.0.patch: `_rfbCloseReason` 在 _socketClose 开头设置，_fail 中仅当未设置时写入，disconnect 派发时加入 reason

---

### 1.5 端到端集成

| 验证点 | 操作 | 预期 | 验证方式 |
|--------|------|------|----------|
| **手机 → PC VNC 全流程** | 手机点击远端 VNC，PC 在线 | relay_request → ACK → 2s → connect → 配对 → open_vnc_stream → bridge_ws_quic | 集成测试 |
| **并发 relay_request** | 用户快速双击 VNC | 两个 push_id 独立，各自 ACK，无冲突 | 集成测试 |
| **PC 多实例** | 同一用户多台 PC，手机选目标 | 正确推送到 target_device_id 对应 PC | 集成测试 |

---

## 2. 剩余缺口

### 2.1 relay_request 最坏 7s 延迟

| 阶段 | 延迟 | 说明 |
|------|------|------|
| R1/R5 ACK 超时 | 5s | Gateway 等待 PC 回执，超时返回 503 |
| R2 手机 2s 延迟 | 2s | relay_request 返回后、首次 connect 前 sleep |
| **最坏合计** | **7s** | 用户点击 VNC 后，relay_request 最坏 5s + 手机 2s = 7s 才发起 connect |

**正常路径**：ACK 通常 < 200ms（1 RTT），relay_request 总延迟约 0.2s + 2s = 2.2s。

**缺口性质**：设计已知、可接受。建议：
- 在 VNC 入口处展示「正在连接 PC…」loading
- 可选：首次连接等待 > 3s 时展示「网络较慢，正在建立连接…」
- 可选：轻提示「预计等待 2–7 秒」（优先级低）

---

### 2.2 P2P_PUSH_ACK_ENABLED 回退

| 场景 | 行为 | 风险 |
|------|------|------|
| **P2P_PUSH_ACK_ENABLED=false** | Gateway 回退到 `send_push_to_device`，不等待 ACK | 恢复 R1/R5 前的竞态：Gateway 返回 ≠ PC 已收到；推送静默丢失时手机无感知 |
| **回退触发** | 生产问题需快速关闭 ACK 时 | 需明确：回退后竞态率上升，仅作临时缓解 |

**缺口性质**：回退路径已实现，但回退后语义降级。建议：
- 回退时在监控/日志中标记，便于追踪
- 文档明确：回退为临时措施，应尽快修复根因后恢复 ACK

---

### 2.3 旧 PC 兼容

| Gateway | PC | 行为 |
|---------|-----|------|
| 新（ACK 启用） | **旧**（无 connect_relay_ack） | Gateway 5s 超时 503，用户需升级 App |
| 新（ACK 禁用） | 新 | 旧行为，PC 发 ack 但 Gateway 忽略 |

**缺口性质**：新 Gateway + 旧 PC 组合下，用户会收到 503。建议：
- 503 响应 body 中增加 `{"upgrade_required": true}` 或类似字段
- 前端解析后展示「请升级 PC 端 App 以使用远程连接」
- 灰度时优先确保 PC 端升级率，再启用 Gateway ACK

---

### 2.4 其他已知缺口

| 缺口 | 说明 | 优先级 |
|------|------|--------|
| **INITIAL_DELAY_SECS 不可配置** | 实施计划建议 `P2P_INITIAL_DELAY_SECS=0` 环境变量，当前 relay.rs 为硬编码 2 | 低 |
| **CloudBridge 退避与 relay.rs 不一致** | PC 侧 500ms×attempt，手机侧 2/4/8s；设计上 PC 已收到 push，短退避可接受 | 低 |
| **多实例 Gateway 的 _device_to_session** | 当前为进程内 Dict，多实例部署时需迁移 Redis | 中（多实例场景） |

---

## 3. 部署检查清单：Gateway / Relay / novaic-app TTL 一致性

### 3.1 TTL 同步（R2/R3 必须）

| 组件 | 常量/配置 | 目标值 | 文件 | 当前值 |
|------|-----------|--------|------|--------|
| Gateway | `_PENDING_SESSION_TTL_SECS` | 20 | `novaic-gateway/gateway/api/p2p.py:71` | 20 |
| novaic-quic-service | `SESSION_TTL` | 20 | `novaic-quic-service/src/relay.rs:25` | 20 |
| novaic-quic-service | `WAIT_FOR_PC_TIMEOUT` | 20 | `novaic-quic-service/src/relay.rs:223` | 20 |

**对齐原则**：`WAIT_FOR_PC_TIMEOUT == SESSION_TTL == _PENDING_SESSION_TTL_SECS == 20s`

**部署顺序**：Gateway → novaic-quic-service（Relay）→ novaic-app（手机/PC）

### 3.2 部署前检查项

- [ ] Gateway 部署前确认 `_PENDING_SESSION_TTL_SECS = 20`
- [ ] novaic-quic-service 部署前确认 `SESSION_TTL`、`WAIT_FOR_PC_TIMEOUT` 均为 20
- [ ] novaic-app relay.rs 确认 `INITIAL_DELAY_SECS = 2`
- [ ] 三者必须同版本发布或明确兼容矩阵，**禁止 Gateway 20s + Relay 10s 混跑**

### 3.3 版本兼容矩阵

| Gateway | novaic-quic-service | novaic-app (PC) | novaic-app (Mobile) | 行为 |
|---------|---------------------|-----------------|---------------------|------|
| 旧 (10s) | 旧 (10s) | 旧 | 旧 | 当前行为 |
| 新 (20s) | 新 (20s) | 旧 | 新 (2s 延迟) | 正常；手机 2s 延迟改善成功率 |
| 新 (20s) | 新 (20s) | 新 (R4 refresh) | 新 | 正常；PC 可 refresh |
| 新 (20s) | **旧 (10s)** | — | — | **禁止**：Gateway 认为有效、Relay 已过期 |
| **旧 (10s)** | **新 (20s)** | — | — | **禁止**：Relay 等 20s 但 Gateway 10s 即过期 |

### 3.4 R1/R5 ACK 兼容矩阵

| Gateway | PC | 行为 |
|---------|-----|------|
| 旧（无 ACK） | 旧 | 当前行为 |
| 新（ACK 启用） | **旧** | Gateway 超时 503，**提示升级 App** |
| 新（ACK 禁用） | 新 | 旧行为，PC 发 ack 但 Gateway 忽略 |
| 新（ACK 启用） | 新 | 正常 ACK 流程 |

---

## 4. 建议的回归测试场景

### 4.1 正常路径

| 场景 | 步骤 | 预期 |
|------|------|------|
| **手机 → PC VNC 全流程** | 手机点击远端 VNC，PC 在线、App 已登录 | relay_request 2–3s 内返回，VNC 连接成功 |

### 4.2 竞态与超时

| 场景 | 步骤 | 预期 |
|------|------|------|
| **PC 断网** | PC 断网或 App 未启动，手机发起 VNC | relay_request 5s 后 503 "Failed to deliver connect_relay to device" |
| **慢网 PC 建连** | tc 限速或人工慢网，PC 建连 5–15s | 手机 2s 延迟后 connect，Relay 20s 内等到 PC，配对成功 |
| **session 过期后 refresh** | 人为延迟 PC 建连 15s 后恢复 | PC 调用 relay_refresh_for_pc，续期后 connect_via_relay 成功 |
| **Relay 等待 PC 超时** | 手机 connect 后 PC 始终不 RegisterPc | 20s 后返回 "PC offline or session expired" |

### 4.3 兼容与回退

| 场景 | 步骤 | 预期 |
|------|------|------|
| **旧 PC 无 ACK** | Gateway 新版本 + 旧 PC（无 connect_relay_ack） | 5s 超时 503 |
| **P2P_PUSH_ACK_ENABLED=false** | 环境变量关闭 ACK | relay-request 立即返回，行为与旧版一致 |
| **refresh 404** | session 已 consume 或过期后 refresh | 404，PC fallback 原退避重试 |

### 4.4 错误展示（E2）

| 场景 | 步骤 | 预期 |
|------|------|------|
| **PC offline / session expired** | connect 失败或 Relay 超时 | 前端展示 "PC offline or session expired" 等后端 reason |
| **正常断开** | VNC 连接后正常关闭 | 前端可展示 reason（若有） | 人工 |
| **Bridge 模式** | OTA 模式 | `e.reason` 经 patch 后到达 disconnect detail |

### 4.5 并发与多实例

| 场景 | 步骤 | 预期 |
|------|------|------|
| **并发 relay_request** | 用户快速双击 VNC | 两个 push_id 独立，各自 ACK，无冲突 |
| **PC 多实例** | 同一用户多台 PC，手机选目标 | 正确推送到 target_device_id 对应 PC |

### 4.6 用户提示文案建议

| 场景 | 建议文案 |
|------|----------|
| relay_request 进行中 | "正在连接 PC…"（可加 loading 动画） |
| relay_request 超时 503 | "无法联系到 PC，请确认 PC 已开机且 App 已登录" |
| 旧 PC 503 | "请升级 PC 端 App 以使用远程连接" |
| connect 失败（含 session 错误） | 展示后端 reason（E2 实施后），如 "PC offline or session expired" |
| 首次连接等待 > 3s | 可选："网络较慢，正在建立连接…" |

---

## 5. 相关文档索引

| 文档 | 说明 |
|------|------|
| docs/survey-2026/P2P_ARCHITECTURE_ROUND1.md | Round 1 架构与连接路径 |
| docs/survey-2026/P2P_RELAY_TUNNEL_ROUND2.md | Round 2 时序与验证点 |
| docs/unify-vnc/P2P-RACE-IMPLEMENTATION-PLAN-R3.md | 竞态修复实施计划 |
| docs/unify-vnc/P2P-R1R5-PUSH-ACK-DESIGN-R2.md | R1/R5 ACK 设计 |
| docs/unify-vnc/P2P-R2R3-MOBILE-DELAY-RELAY-WAIT-DESIGN-R2.md | R2/R3 设计 |
| docs/unify-vnc/P2P-R4-PC-SESSION-REFRESH-DESIGN-R2.md | R4 设计 |
| docs/unify-vnc/P2P-E2-RFB-CLOSE-REASON-DESIGN-R2.md | E2 设计 |

---

*Round 3 产出。基于 R1/R2 调研与实施计划，汇总剩余缺口与部署验证建议。*
