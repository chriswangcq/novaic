# P2P 竞态修复 Round 2 设计评审报告

**评审日期**: 2026-03-12  
**输入文档**: P2P-R1R5-PUSH-ACK-DESIGN-R2.md、P2P-R2R3-MOBILE-DELAY-RELAY-WAIT-DESIGN-R2.md、P2P-R4-PC-SESSION-REFRESH-DESIGN-R2.md、P2P-E2-RFB-CLOSE-REASON-DESIGN-R2.md  
**产出**: Round 1 反馈纳入情况、新缺口/冲突、实施顺序、Round 3 就绪判断

---

## 0. 输入文档状态说明

**已检出** Round 2 修订版文档：`P2P-R1R5-PUSH-ACK-DESIGN-R2.md`、`P2P-R2R3-MOBILE-DELAY-RELAY-WAIT-DESIGN-R2.md`、`P2P-R4-PC-SESSION-REFRESH-DESIGN-R2.md`、`P2P-E2-RFB-CLOSE-REASON-DESIGN-R2.md`。  
以下逐项核查 R2 是否已纳入 Round 1 反馈。

---

## 1. Round 1 反馈纳入情况

### 1.1 R1/R5 PUSH-ACK 设计

| Round 1 建议 (§4.1) | 纳入状态 | 说明 |
|---------------------|----------|------|
| §3.1.2 兼容性：并发 relay_request 时，Future 以 push_id 为 key，与 target 无关 | ✅ 已纳入 | R2 §3.1.2 明确「Future 必须以 push_id 为 key 注册，与 target_device_id 无关」 |
| §4.1 风险：PC 发 ACK 前崩溃 → 503，手机重试 relay_request 拿新 session | ✅ 已纳入 | R2 §4.1 风险表有「PC 收到 push 后、发送 ACK 前崩溃」场景 |
| §5.3 与 R4 关系：与 relay-refresh-for-pc 共享 `_pending_relay_sessions`，无冲突 | ✅ 已纳入 | R2 §5.3 明确共享、ACK 与 refresh 分别处理送达和续期 |
| 方向 C：重试推送时 PC 已 spawn 的幂等处理 | ✅ 已纳入 | R2 §3.2.3 明确「同一 session_id 只 spawn 一次」 |

**R1 缺口（§1.1）待 R2 覆盖**：
- 同一 target 并发 relay_request：Future 以 push_id 为 key
- PC 收到 push 后、发送 ACK 前崩溃：503 为预期，文档需说明
- ACK 消息丢失：方向 C 幂等语义
- relay_request 与 refresh 并发：与 R4 协调 `_device_to_session` 更新顺序

---

### 1.2 R2/R3 Mobile Delay + Relay Wait 设计

| Round 1 建议 (§4.2) | 纳入状态 | 说明 |
|---------------------|----------|------|
| §2.1 手机侧：每次 relay_request 返回后、新一轮 connect 前都 sleep(2s) | ✅ 已纳入 | R2 §2.1 明确「每次 relay_request 返回后、新一轮 connect 前都 sleep(2s)」 |
| §2.2 WAIT_FOR_PC：PC 建连需在 20s 内完成 | ✅ 已纳入 | R2 §2.2 明确「PC 建连需在 WAIT_FOR_PC_TIMEOUT(20s) 内完成」 |
| §4.1 风险：Gateway/Relay/手机三者 TTL 必须同时升级 | ✅ 已纳入 | R2 §2.3、§4.1 明确「必须三者 TTL 一致」、部署顺序 |
| §5 实施顺序：部署顺序与兼容矩阵 | ✅ 已纳入 | R2 §4.3 明确「同版本发布或明确兼容矩阵」 |

**R1 缺口（§1.2）待 R2 覆盖**：
- 手机 2s 延迟与重试：每次 relay_request 返回后、首次 connect 前都 sleep(2s)
- WAIT_FOR_PC 20s 与 QUIC 30s：PC 建连需在 20s 内完成
- Gateway/Relay 部署不同步：三者 TTL 一致，否则边界故障

---

### 1.3 R4 PC Session Refresh 设计

| Round 1 建议 (§4.3) | 纳入状态 | 说明 |
|---------------------|----------|------|
| §2.2 推荐方案 A1：refresh 延长量 = `_PENDING_SESSION_TTL_SECS` | ✅ 已纳入 | R2 §2.2 明确「再活 _PENDING_SESSION_TTL_SECS」、§5 依赖 R2/R3 |
| §2.2 设计要点：refresh 适用于 validate 因过期 404，非 Relay consume | ✅ 已纳入 | R2 §2.2 明确「适用/不适用」场景 |
| §3.3 PC 端：is_session_error 与 relay.rs 一致，排除 invalid/certificate | ✅ 已纳入 | R2 §3.3 伪代码与 relay.rs 一致 |
| §4.1 风险：relay_request 与 refresh 并发，PC 用 refresh 返回的 session_id | ✅ 已纳入 | R2 §4.1、§3.3 明确「必须用 refresh 返回的 session_id」 |
| §5 实施顺序：依赖 R2/R3 TTL，R2/R3 未实施时暂用 10s | ✅ 已纳入 | R2 §5 明确依赖 R2/R3、_PENDING_SESSION_TTL_SECS 自动联动 |

**R1 缺口（§1.3）待 R2 覆盖**：
- **关键**：refresh 延长量必须 = `_PENDING_SESSION_TTL_SECS`，与 R2/R3 联动
- refresh 适用场景：validate 404 因过期；Relay consume 时不可用
- is_session_error 与 relay.rs 保持一致
- relay_request 与 refresh 竞态：PC 必须用 refresh 返回的 session_id

---

### 1.4 E2 RFB Close Reason 设计

| Round 1 建议 (§4.4) | 纳入状态 | 说明 |
|---------------------|----------|------|
| §2.2 推荐方案：验证 VncBridgeTransport 下 reason 传递 | ✅ 已纳入 | R2 §2.2 明确 bridge 模式验证、§5 步骤 2 回归测试 |
| §2.4 具体修改：`_socketClose` 与 `_fail` 调用顺序，reason 不被覆盖 | ✅ 已纳入 | R2 §2.4 完整分析、§2.5 位置 2 仅当未设置时写入 |
| §5 实施顺序：pin @novnc/novnc 版本，升级时回归 | ✅ 已纳入 | R2 §2.6 明确 pin 版本、升级时回归 |

**R1 缺口（§1.4）待 R2 覆盖**：
- VncBridgeTransport 的 raw channel 下 reason 传递路径验证
- `_socketClose` 与 `_fail` 时序，确保 `_rfbCloseReason` 不被错误覆盖

---

## 2. 修订版新发现的缺口或冲突

### 2.1 新缺口（基于 R1 与 R1 Review 交叉检查）

| 方案 | 缺口 | 建议 |
|------|------|------|
| **R1/R5** | 方向 A 的 `send_push_and_wait_ack` 超时 5s，与 R2 手机 2s 延迟叠加后，relay_request 最坏延迟 = 5s + 2s = 7s，需在文档中明确 | 补充「relay_request 最坏延迟」说明 |
| **R2/R3** | 手机 `connect_via_relay_only` 重试时，若第一次失败（非 session 错误），第 2–4 次无 2s 延迟；文档需明确「仅首次 connect 前有 2s」 | 明确 2s 仅应用于「relay_request 返回后首次 connect」 |
| **R4** | `_device_to_session` 与 `_pending_relay_sessions` 的 pop 顺序：validate 时 is_expired 先 pop 哪个？R1 Review 建议「先 _device_to_session.pop，再 _pending_relay_sessions.pop」 | R2 需在伪代码或设计要点中明确 |
| **E2** | reason 为空或超长时的前端展示策略；R1 Review 标为低优先级，可注明「长度无限制，前端可考虑截断」 | 可选补充 |

### 2.2 方案间冲突复核

| 冲突点 | Round 1 结论 | R2 需确保 |
|--------|--------------|-----------|
| **R2/R3 与 R4 的 TTL** | refresh 延长量 = `_PENDING_SESSION_TTL_SECS` | R4 必须引用该常量，禁止硬编码 10s |
| **R1/R5 与 R4** | 共享 `_pending_relay_sessions`，无冲突 | R1/R5、R4 文档均需明确共享关系 |
| **relay_request 与 refresh 并发** | `_device_to_session` 指向最新 session | R4 明确 refresh 返回当前 `_device_to_session` 的 session |

### 2.3 依赖与配置联动

```
_PENDING_SESSION_TTL_SECS (Gateway) == SESSION_TTL (Relay) == WAIT_FOR_PC_TIMEOUT (Relay) == 20s
R4 refresh 延长量 == _PENDING_SESSION_TTL_SECS  // 必须
```

---

## 3. 实施顺序与依赖的最终建议

### 3.1 依赖图（与 Round 1 一致）

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

### 3.2 实施顺序

| 阶段 | 任务 | 依赖 | 预估 |
|------|------|------|------|
| **1** | R2/R3（20s + 2s 延迟） | 无 | Gateway + Relay + 手机，约 20min |
| **2** | R4（relay-refresh-for-pc） | R2/R3 的 TTL=20s | refresh 延长量引用 `_PENDING_SESSION_TTL_SECS` |
| **3** | R1/R5（ACK） | 无强依赖 | 建议 R2/R3 上线后 |
| **4** | E2（RFB patch） | 无 | 可与 1–3 任意阶段并行 |

### 3.3 部署顺序

- **Gateway → Relay → 手机**：三者 TTL 必须同版本或兼容
- **R4 依赖**：R2/R3 合并后，R4 的 refresh 延长量才能确定为 20s（或引用常量）

---

## 4. 是否可进入 Round 3 最终定稿

### 4.1 结论：**可进入 Round 3**

| 条件 | 状态 |
|------|------|
| Round 2 修订版文档存在 | ✅ 已检出 4 份 |
| Round 1 全部修改建议已纳入 | ✅ 逐项核查已通过 |
| 方案间冲突已协调 | ✅ R4 引用 _PENDING_SESSION_TTL_SECS，R2/R3 三端 TTL 同步 |

### 4.2 Round 3 产出预期

- 最终设计定稿（无待办缺口）
- 实施计划（任务拆解、验收标准、回退方案）
- 兼容矩阵与部署检查清单

---

## 5. 总结

| 维度 | 结论 |
|------|------|
| **Round 1 反馈纳入** | ✅ 全部纳入（R1/R5、R2/R3、R4、E2） |
| **新缺口** | relay_request 最坏延迟（R1/R5 方向 A 5s + R2 2s = 7s）、2s 仅首次 connect 前、R4 pop 顺序已明确 |
| **冲突** | ✅ R2/R3 与 R4 的 TTL 联动已在 R4 中明确 |
| **实施顺序** | R2/R3 → R4 → R1/R5；E2 可并行 |
| **Round 3 就绪** | ✅ 是 |

---

*Round 2 评审完成。4 份 R2 设计已纳入全部 Round 1 反馈，可进入 Round 3 最终定稿。*
