# P2P 竞态修复 Round 2 设计：R4 PC 重试无 session 刷新

**设计轮次**: Round 2（基于 R1 Review 修订）  
**日期**: 2026-03-12  
**范围**: PC 端 connect_via_relay 重试时 session 过期导致重试无效

---

## 1. 问题陈述

### 1.1 核心问题

| 竞态 ID | 描述 | 影响 |
|---------|------|------|
| **R4** | PC 重试始终用同一 session_id，Session TTL 10s，建连慢时 session 已过期 | 3 次重试全部无效，用户需等 mobile 30s 超时后重试才能拿到新 push |

### 1.2 当前流程

```
relay-request (mobile)
    → Gateway 创建 session_id，TTL 10s（R2/R3 实施后为 20s）
    → send_push(connect_relay) 给 PC
    → 返回 {relay_url, session_id} 给 mobile

PC 收到 connect_relay
    → spawn connect_via_relay(relay_url, jwt, session_id)
    → 失败时重试 3 次：500ms、1000ms、1500ms 退避
    → 始终使用同一 session_id  ← 问题点
```

### 1.3 相关代码位置

| 组件 | 文件 | 行为 |
|------|------|------|
| PC 重试逻辑 | `cloud_bridge.rs:279-323` | 3 次重试，同一 session_id，无刷新 |
| Session TTL | `p2p.py:70-81` | `_PENDING_SESSION_TTL_SECS = 10`（R2/R3 实施后为 20） |
| 手机侧参考 | `relay.rs:181-239` | session 错误时重新 `relay_request` 获取新 session |

### 1.4 对比：手机端已有 session 刷新

手机端 `connect_via_relay_only` 在错误含 `session` / `expired` 时会重新调用 `relay_request` 获取新 session 再重试。PC 端缺少等效逻辑。

---

## 2. 方案设计

### 2.1 可选方向

#### 方向 A：PC 主动调用 Gateway 新 API 刷新 session

**思路**：PC 重试失败时调用 Gateway 新 API，获取新 session 或延长当前 session。

| 子方案 | 语义 | 优点 | 缺点 |
|--------|------|------|------|
| **A1 延长 TTL** | `relay-refresh-for-pc` 重置 session 的 created_at，再活 `_PENDING_SESSION_TTL_SECS` | 不创建新 session，mobile 无需变更 | 需 Gateway 维护 device_id→session 映射 |
| **A2 创建新 session** | 创建新 session，push 给 PC，mobile 重试 relay_request 时返回该 session | PC 可立即用新 session | 需 mobile 重试才能同步；mobile 重试时机依赖 relay 30s 超时 |

#### 方向 B：PC 主动调用现有 relay_request

**思路**：PC 调用 `relay_request(target_device_id=self)`，Gateway 返回 session_id，PC 直接用。

| 问题 | 说明 |
|------|------|
| **session 不同步** | mobile 已拿旧 session，PC 拿新 session，relay 端 session_id 不匹配 |
| **结论** | 不可行 |

#### 方向 C：仅延长 session TTL 或 PC 重试次数

**思路**：不改 PC 逻辑，仅将 `_PENDING_SESSION_TTL_SECS` 从 10s 增至 30s，或增加 PC 重试次数。

| 优点 | 缺点 |
|------|------|
| 实现简单 | 治标不治本；延长 TTL 增加安全窗口；重试次数无法解决「session 已过期」 |

### 2.2 推荐方案：方向 A1（延长 TTL）

**选择理由**：
- 不引入新 session，mobile 与 PC 继续共用同一 session
- 语义清晰：PC 建连慢时主动「续期」
- 实现成本低：Gateway 增加 device_id→session 索引 + 新 API

**设计要点**：

1. **Gateway**：增加 `_device_to_session: Dict[target_device_id, session_id]`，在 `relay_request` 时写入，session 过期 pop 时同步删除。
2. **新 API**：`POST /api/p2p/relay-refresh-for-pc`，body `{ "device_id": str }`。
   - 校验：device_id 在 P2P registry，JWT 对应 user_id 与 device 归属一致。
   - 查找：`session_id = _device_to_session.get(device_id)`，若不存在或 session 已过期 → 404。
   - **操作（R1 Review 必须）**：重置 `PendingRelaySession.created_at = time.time()`，相当于**再活 `_PENDING_SESSION_TTL_SECS`**。**非硬编码 10s**。若 R2/R3 已实施，`_PENDING_SESSION_TTL_SECS` 为 20s，则 refresh 延长量为 20s。
   - 返回：`{ "ok": true, "session_id": "...", "relay_url": "..." }`（PC 可校验，但通常 PC 已有 relay_url，仅需确认续期成功）。
3. **PC 端**：重试失败且 `is_session_error` 时，调用 `relay-refresh-for-pc`，成功则继续用原 session_id 重试（因 TTL 已延长）。

**refresh 适用场景（R1 Review 必须纳入）**：
- **适用**：`validate_relay_session` 因 **session 过期** 返回 404 时。即 Gateway/Relay 端 session 因 TTL 过期，PC 建连慢导致 validate 时 is_expired。
- **不适用**：Relay 端 session 已被 **consume**（第一次 ConnectRequest 已消费，pc_registry 中已移除）。PC 重试 ConnectRequest 时，若 Relay 已消费，会返回 "PC offline"。此时 refresh 无意义——续期 Gateway 无助于 Relay，Relay 端 session 已消费。PC 应等 mobile 重试 relay_request 拿新 session。
- **区分错误来源**：`validate_relay_session` 返回 404 因过期 → 可 refresh。ConnectRequest 返回 "PC offline" → 可能是 consume 导致，refresh 无法挽回。

### 2.3 备选方案：方向 A2（创建新 session + mobile 认领）

若 A1 因 Gateway 数据结构改动复杂而放弃，可考虑 A2：

1. **Gateway 新 API**：`relay-refresh-for-pc` 创建新 session，invalidate 旧 session，push 新 connect_relay 给 PC，返回新 session_id。
2. **Gateway 修改 relay_request**：当 mobile 调用 `relay_request(target_device_id)` 时，若存在 `_pending_pc_refresh[target_device_id]` 且未过期，直接返回该 session，不创建新 session、不 push。
3. **时序**：PC 刷新 → 用新 session 连 relay；mobile 旧 session 在 relay 端 30s 超时后失败 → mobile 重试 relay_request → 拿到 PC 已刷新的 session → 连接成功。

**缺点**：用户需等 relay 30s 超时，体验较差。A1 更优。

---

## 3. 接口变更

### 3.1 Gateway 新 API（推荐 A1）

```
POST /api/p2p/relay-refresh-for-pc
Authorization: Bearer <jwt>
Content-Type: application/json

Request:
{
  "device_id": "uuid"   // PC 自己的 device_id
}

Response 200:
{
  "ok": true,
  "session_id": "uuid",   // 原 session，已续期
  "relay_url": "https://..."
}

Response 404:
{
  "detail": "no pending relay session for device" | "session already expired"
}

Response 403:
{
  "detail": "device not in registry" | "device belongs to different user"
}
```

### 3.2 Gateway 数据结构变更（A1）

```python
# p2p.py 新增
_device_to_session: Dict[str, str] = {}  # target_device_id -> session_id

# relay_request 中，创建 PendingRelaySession 后：
_pending_relay_sessions[session_id] = PendingRelaySession(...)
_device_to_session[req.target_device_id] = session_id

# validate_relay_session 中，is_expired() 且 pop 时：
_device_to_session.pop(pending.target_device_id, None)
```

### 3.3 PC 端（cloud_bridge.rs）变更

- 传入 `gateway_url` 到 `connect_and_run`（或从 ws_url 推导 http base）。
- 在 `ConnectRelay` 处理逻辑中，增加 session 错误检测与 refresh 调用：

**is_session_error 与 relay.rs 保持一致（R1 Review 必须）**：排除 "invalid"、"certificate" 等，避免误触发 refresh。参考 `novaic-app/src-tauri/p2p/src/relay.rs:198-199`：

```rust
// relay.rs 逻辑
let is_session_error = err_lower.contains("session")
    || (err_lower.contains("expired") && !err_lower.contains("certificate"));
// 排除 "Invalid JWT", "certificate expired" 等
```

PC 端伪代码：

```rust
// 伪代码，与 relay.rs 的 is_session_error 保持一致
let is_session_error = |e: &str| {
    let lower = e.to_lowercase();
    (lower.contains("session") || (lower.contains("expired") && !lower.contains("certificate")))
        && !lower.contains("invalid");  // 排除 "Invalid JWT"
};

for attempt in 1..=4 {
    match connect_via_relay(...).await {
        Ok(conn) => { ...; return; }
        Err(e) => {
            if is_session_error(&e.to_string()) && attempt < 4 {
                if let Ok(resp) = relay_refresh_for_pc(gateway_url, jwt, device_id).await {
                    // 必须用 refresh 返回的 session_id 重试（_device_to_session 指向当前 session）
                    // TTL 已延长，立即重试，不 sleep
                    continue;
                }
            }
            // 原有退避重试
            tokio::time::sleep(...).await;
        }
    }
}
```

### 3.4 新增 rendezvous 函数（可选）

在 `p2p/src/rendezvous.rs` 或 `vmcontrol` 内增加：

```rust
pub async fn relay_refresh_for_pc(
    gateway_url: &str,
    jwt: &str,
    device_id: &str,
) -> anyhow::Result<RelayRefreshResponse>
```

---

## 4. 风险与回退

### 4.1 风险

| 风险 | 缓解 |
|------|------|
| Gateway 多进程/多实例下 `_device_to_session` 不同步 | 单实例部署无影响；多实例需迁移到 Redis，本设计先单实例 |
| PC 频繁 refresh 导致 session 长期有效 | 每次 refresh 仅延长 `_PENDING_SESSION_TTL_SECS`，且需有 pending session；无 relay_request 时无 session |
| **relay_request 与 refresh 并发（R1 Review 补充）** | relay_request 创建新 session 会覆盖 _device_to_session；refresh 仅续期，不创建。refresh 返回的 session_id 是 `_device_to_session[device_id]` 指向的**当前** session。若 mobile 快速两次 relay_request，第一次 session A，第二次 session B，_device_to_session 变为 B。PC 若仍持有 A 的 connect_relay 正在重试，调用 refresh 拿到的是 B 的续期。PC **必须用 refresh 返回的 session_id** 重试；若 mobile 已发起新 relay_request，PC 会收到新 connect_relay，旧 session A 作废。 |
| **PC 调用 refresh 时 session 已被 consume** | refresh 适用于 validate 时 is_expired；若 Relay 已 consume，refresh 无意义。PC 的 refresh 应在「validate_relay_session 返回 404 因过期」时触发，而非「ConnectRequest 返回 PC offline」时。需区分错误来源。 |
| **多实例 Gateway 的 pop 顺序** | pop 时先 `_device_to_session.pop`，再 `_pending_relay_sessions.pop`，避免 refresh 查到已过期 session。 |

### 4.2 回退策略

- **Gateway**：不部署新 API，或新 API 返回 501，PC 端检测 501 时跳过 refresh，保持现有 3 次重试行为。
- **PC 端**：refresh 失败时 fallback 到原有重试逻辑，不改变现有行为。

### 4.3 兼容性

- 旧版 PC（无 refresh 逻辑）：行为不变。
- 旧版 Gateway（无 relay-refresh-for-pc）：PC 调用 404，fallback 到原重试。
- 新版 mobile：无需改动。

---

## 5. 实施顺序

| 步骤 | 任务 | 依赖 |
|------|------|------|
| 1 | Gateway：增加 `_device_to_session`，在 relay_request / validate 中维护 | 无 |
| 2 | Gateway：实现 `POST /api/p2p/relay-refresh-for-pc`，**refresh 延长量 = `_PENDING_SESSION_TTL_SECS`** | 步骤 1；**依赖 R2/R3 的 TTL 配置** |
| 3 | PC：vmcontrol 增加 `relay_refresh_for_pc` 调用（或 p2p 模块新增后 vmcontrol 调用） | 无（可并行） |
| 4 | PC：cloud_bridge ConnectRelay 处理中，失败且 `is_session_error` 时调用 refresh 并重试；`is_session_error` 与 relay.rs 一致 | 步骤 2、3 |
| 5 | 联调与测试：模拟慢建连、session 过期场景 | 步骤 4 |

**依赖 R2/R3**：若 R2/R3 未实施，R4 的 refresh 延长量暂用 `_PENDING_SESSION_TTL_SECS`（当前 10s）；R2/R3 实施后该常量变为 20s，refresh 自动联动，**无需硬编码**。

---

## 6. 参考

- `novaic-app/src-tauri/vmcontrol/src/cloud_bridge.rs`：ConnectRelay 处理与重试
- `novaic-app/src-tauri/p2p/src/relay.rs`：is_session_error 逻辑、手机端 session 刷新
- `novaic-gateway/gateway/api/p2p.py`：relay_request、_pending_relay_sessions、session TTL
- `docs/unify-vnc/P2P-RACE-DESIGN-REVIEW-R1.md`：Round 1 评审反馈
- `docs/unify-vnc/P2P-RACE-DESIGN-CONVENTIONS.md`：设计约定

---

*Round 2 修订版，已纳入 R1 Review 反馈：refresh 延长量引用 _PENDING_SESSION_TTL_SECS、适用场景与 is_session_error。*
