# P2P 竞态修复 Round 2 设计：R1/R5 推送无 ACK、无重试

**设计轮次**: Round 2（基于 R1 Review 修订）  
**日期**: 2026-03-12  
**范围**: connect_relay 推送的可靠性 — 解决 Gateway 返回 ≠ PC 已接收、推送静默丢失

---

## 1. 问题陈述

### 1.1 核心问题

`send_push_to_device` 完成 = `ws.send_json()` 成功 = **写入 TCP 发送缓冲**，**非** PC 已接收/处理。

| 竞态 ID | 描述 | 影响 |
|---------|------|------|
| **R1** | Gateway 返回 ≠ PC 已收到 | relay-request 返回 200 后，手机拿到 session_id 立即 connect_via_relay，但 PC 可能尚未收到推送 |
| **R5** | 推送静默丢失 | PC 在 Gateway 发送后、接收前断连 → TCP 缓冲数据丢失 → PC 永远收不到 connect_relay，手机拿到的 session_id 无效 |

### 1.2 当前流程

```
relay-request (HTTP POST)
    → p2p_relay_request
    → send_push_to_device(device, "connect_relay", {relay_url, session_id})
    → device.ws.send_json(message)   ← 成功 = 写入缓冲
    → 立即返回 {relay_url, session_id} 给手机
```

- **pc_client.py:245-261**：`send_push_to_device` 单向推送，不等待响应
- **cloud_bridge.rs:279-323**：PC 收到后 `tokio::spawn` 异步处理，无回执

### 1.3 缺口

- 无 ACK 机制：Gateway 无法确认 PC 已收到推送
- 无重试机制：推送丢失时手机无感知，只能依赖 Relay 10s 超时 + 手机 4 次重试
- 用户体验：手机可能长时间等待 "PC offline or session expired"，无法区分「PC 未收到」与「PC 建连慢」

---

## 2. 方案设计：可选方向

### 2.1 方向 A：PC → Gateway ACK 回执

**思路**：推送改为「请求-响应」模式，Gateway 等待 PC 回执后再返回 relay-request。

| 项目 | 设计 |
|------|------|
| **消息格式** | 推送增加 `push_id`；PC 收到后发送 `connect_relay_ack { push_id }` |
| **Gateway 行为** | `send_push_to_device` 改为 `send_push_and_wait_ack`，注册 Future，超时（如 5s）未收到 ACK 则 503 |
| **relay-request** | 仅当收到 ACK 后返回 200；超时返回 503 "Push not acknowledged by device" |
| **优点** | 手机拿到的 session_id 时，PC 已确认收到；语义清晰 |
| **缺点** | relay-request 延迟增加（至少 1 RTT）；PC 需新增 ACK 逻辑 |

**接口变更**：
- 推送：`{"type":"connect_relay","push_id":"uuid","relay_url":"...","session_id":"..."}`
- 回执：`{"type":"connect_relay_ack","push_id":"uuid"}`

### 2.2 方向 B：Gateway 推送重试

**思路**：保持单向推送，Gateway 在未收到 ACK 时周期性重试（如 3 次，间隔 1s）。

| 项目 | 设计 |
|------|------|
| **触发** | relay-request 返回后，Gateway 后台任务监听 ACK；无 ACK 则重试 |
| **问题** | 仍无 ACK 则无法区分「PC 已收到但未回执」与「PC 断连」；重试可能重复推送 |
| **去重** | PC 需对同一 session_id 的 connect_relay 幂等处理（当前已支持：spawn 多个 connect_via_relay 无副作用，第二次 session 被浪费） |
| **优点** | relay-request 可立即返回，手机体验不变；实现相对简单 |
| **缺点** | 手机仍可能拿到 session_id 时 PC 未收到；需依赖重试 + 手机端重试 |

**接口变更**：
- 推送格式不变，或增加 `push_id` 便于去重
- 可选：PC 回执 `connect_relay_ack`，Gateway 收到后停止重试

### 2.3 方向 C：混合（ACK + 重试）

**思路**：结合 A、B：Gateway 等待 ACK，超时则重试推送，最多 N 次；任一次收到 ACK 即返回 relay-request。

| 项目 | 设计 |
|------|------|
| **流程** | 1) 推送 connect_relay(push_id) 2) 等待 ACK，超时 3s 3) 重试推送，最多 3 次 4) 任一次 ACK → 返回 200 5) 全部超时 → 503 |
| **优点** | 兼顾可靠性（重试）与语义（ACK 确认后返回） |
| **缺点** | 实现复杂度最高；relay-request 最坏延迟 = 3 × 3s = 9s |

---

## 3. 接口变更

### 3.1 WebSocket 消息格式

#### 3.1.1 当前格式（不变部分）

- **Gateway → PC**：`{"type":"connect_relay","relay_url":"...","session_id":"..."}`

#### 3.1.2 新增/修改（方向 A / C 通用）

| 消息 | 方向 | 格式 | 说明 |
|------|------|------|------|
| **connect_relay** | Gateway → PC | `{"type":"connect_relay","push_id":"uuid","relay_url":"...","session_id":"..."}` | 新增 `push_id`，PC 回执时原样返回 |
| **connect_relay_ack** | PC → Gateway | `{"type":"connect_relay_ack","push_id":"uuid"}` | PC 收到 connect_relay 后立即发送，表示「已收到并开始处理」 |

**兼容性**：`push_id` 可选；旧版 PC 不发送 ack，Gateway 可检测超时并 503。

**并发场景（R1 Review 补充）**：同一 target_device_id 的**并发 relay_request**（如用户快速双击 VNC）会创建两个 session、两次 push。`send_push_and_wait_ack` 的 Future 必须以 **`push_id`** 为 key 注册，与 target_device_id 无关。每个 push 独立 push_id，各自 Future 独立，无冲突。PC 收到两个 ConnectRelay 时先后 ACK，Gateway 分别 resolve 对应 Future。

### 3.2 Gateway API

#### 3.2.1 relay-request（方向 A）

- **当前**：`send_push_to_device` 成功即返回 200
- **变更**：`send_push_and_wait_ack(device, push_id, "connect_relay", {...}, timeout=5.0)`
  - 成功：收到 `connect_relay_ack` 后返回 200
  - 失败：超时或 `send_json` 异常 → 503 `"Failed to deliver connect_relay to device"`

#### 3.2.2 relay-request（方向 B）

- 保持立即返回 200
- 新增后台任务：未收到 ACK 时，每 1s 重试推送，最多 3 次（可选实现）

#### 3.2.3 relay-request（方向 C）

- 同方向 A，但 `send_push_and_wait_ack` 内部实现重试循环
- **方向 C 幂等（R1 Review 补充）**：重试推送时，若 PC 已处理第一次 push 并 spawn connect_via_relay，第二次 push 到达时 PC 需幂等。建议：同一 session_id 只 spawn 一次，可用内存 set `_spawned_session_ids` 去重，避免重复 spawn。

### 3.3 PC CloudBridge 变更

- **IncomingMessage**：`ConnectRelay { push_id: Option<String>, relay_url, session_id }`（`push_id` 可选兼容）
- **收到 ConnectRelay 后**：若存在 `push_id`，立即发送 `connect_relay_ack { push_id }`，再 `tokio::spawn` 执行 connect_via_relay

---

## 4. 风险与回退

### 4.1 风险

| 风险 | 缓解 |
|------|------|
| **PC 旧版不发送 ACK** | Gateway 超时后 503；用户需升级 App |
| **ACK 丢失** | 方向 A 会 503；方向 C 可重试推送（PC 幂等） |
| **relay-request 延迟增加** | 方向 A/C 增加 1 RTT（通常 < 200ms）；可接受 |
| **重复推送导致 PC 多 spawn** | 当前 spawn 无副作用；可加 session_id 去重，同一 session 只 spawn 一次 |
| **PC 收到 push 后、发送 ACK 前崩溃（R1 Review 补充）** | PC 解析 ConnectRelay 成功，准备发 ACK 时进程退出。Gateway 超时 503，手机拿到 503 会重试 relay_request，创建新 session。旧 session 在 Relay 端 10s/20s 后自然过期。**可接受**；503 为预期行为，文档中明确此场景。 |
| **relay_request 与 refresh 并发（R1 Review 补充）** | R4 的 `relay-refresh-for-pc` 与 relay_request 可能并发。relay_request 创建新 session 会覆盖 `_device_to_session`；refresh 仅续期，不创建。refresh 操作的是 `_device_to_session[device_id]` 指向的**当前** session。若 relay_request 刚创建新 session，refresh 续期的是新 session。无冲突。 |

### 4.2 回退策略

- **特性开关**：Gateway 可通过环境变量 `P2P_PUSH_ACK_ENABLED=false` 回退到当前「发送即返回」行为
- **版本兼容**：`push_id` 可选，旧 PC 忽略；Gateway 根据是否启用 ACK 决定是否等待

### 4.3 兼容性矩阵

| Gateway | PC | 行为 |
|---------|-----|------|
| 旧（无 ACK） | 旧 | 当前行为 |
| 新（ACK 启用） | 旧 | Gateway 超时 503，提示升级 |
| 新（ACK 禁用） | 新 | 旧行为，PC 发 ack 但 Gateway 忽略 |
| 新（ACK 启用） | 新 | 正常 ACK 流程 |

---

## 5. 实施顺序

### 5.1 推荐方向

**建议优先方向 A**：实现简单、语义清晰、能直接解决 R1/R5。若生产反馈 relay-request 延迟敏感，再考虑方向 B（立即返回 + 后台重试）。

### 5.2 实施步骤

| 步骤 | 任务 | 依赖 |
|------|------|------|
| 1 | PC CloudBridge：IncomingMessage 增加 `push_id`，收到后发送 `connect_relay_ack` | 无 |
| 2 | Gateway pc_client：`_handle_device_message` 处理 `connect_relay_ack`，以 **push_id** 为 key resolve 对应 Future | 无 |
| 3 | Gateway pc_client：新增 `send_push_and_wait_ack`，内部注册 Future（key=push_id）、发送、等待 | 步骤 2 |
| 4 | Gateway p2p：`p2p_relay_request` 改用 `send_push_and_wait_ack`，超时 5s | 步骤 3 |
| 5 | 联调、测试、灰度 | 步骤 4 |

### 5.3 与 R2/R3/R4 的关系（R1 Review 补充）

- **R1/R5**（本设计）：解决「推送是否送达」
- **R2/R3**：手机 connect 时机、Relay 等待时间 — 独立，可并行设计
- **R4**：PC 重试 session 刷新 — **与 R1/R5 共享 `_pending_relay_sessions`**。R4 的 `relay-refresh-for-pc` 续期的是同一 session，R1/R5 的 ACK 确认的是 push 送达。两者操作同一 session 的不同维度（TTL vs 送达确认），无互斥。ACK 完成时 refresh 尚未触发；refresh 触发时 ACK 早已完成。**需明确**：refresh 续期的是 `_device_to_session` 指向的 session，与 `_pending_relay_sessions` 中条目一致；两者无冲突。

---

## 6. 参考

| 文档 | 内容 |
|------|------|
| `docs/P2P_RACE_AND_ERROR_HANDLING_RESEARCH_ROUND3.md` | R1/R5 竞态分析、缺口汇总 |
| `docs/RESEARCH_CONNECT_RELAY_FLOW.md` | relay-request 端到端流程、send_push 语义 |
| `docs/unify-vnc/P2P-RACE-DESIGN-REVIEW-R1.md` | Round 1 评审反馈 |
| `novaic-gateway/gateway/api/p2p.py` | relay-request 实现、send_push_to_device 调用 |
| `novaic-gateway/gateway/api/internal/pc_client.py` | send_push_to_device、_handle_device_message、proxy_response 模式 |
| `novaic-app/src-tauri/vmcontrol/src/cloud_bridge.rs` | ConnectRelay 解析、tokio::spawn 处理 |

---

*Round 2 修订版，已纳入 R1 Review 反馈：并发、ACK 前崩溃、与 R4 协调。*
