# P2P 竞态修复 Round 1 设计交叉评审报告

**评审日期**: 2026-03-12  
**输入文档**: R1/R5、R2/R3、R4、E2 四份初版设计  
**产出**: 缺口、冲突、依赖、修改建议、优先级

---

## 1. 各方案缺口

### 1.1 R1/R5 PUSH-ACK 设计

| 缺口类型 | 描述 | 建议补充 |
|----------|------|----------|
| **遗漏场景** | 同一 target 的**并发 relay_request**：用户快速双击 VNC，两次 relay_request 创建两个 session，两次 push。若方向 A 等待 ACK，两次 push 的 ACK 如何区分？`_handle_device_message` 的 Future 需按 `push_id` 注册，但 `target_device_id` 相同时，PC 可能收到两个 ConnectRelay，先后 ACK，需确保 Future 与 push_id 一一对应。 | 明确：`send_push_and_wait_ack` 的 Future 以 `push_id` 为 key，与 target 无关；并发场景下各自独立。 |
| **遗漏场景** | **PC 收到 push 后、发送 ACK 前崩溃**：PC 解析 ConnectRelay 成功，准备发 ACK 时进程退出。Gateway 超时 503，手机拿到 503 会重试 relay_request，但此时会创建新 session。旧 session 在 Relay 端 10s/20s 后过期。 | 可接受；文档中补充「ACK 前崩溃」场景说明，明确 503 为预期行为。 |
| **边界条件** | **ACK 消息丢失**：PC 发送 `connect_relay_ack` 后，Gateway 与 PC 之间的 WebSocket 在 ACK 到达前断开。Gateway 超时 503。方向 C 可重试推送，但若 PC 已 spawn connect_via_relay，重试会再 push，PC 需幂等。 | 方向 A 已在风险表中；方向 C 需明确「重试时 PC 已处理第一次」的幂等语义。 |
| **边界条件** | **旧版 PC 不发送 ACK**：文档已覆盖。但需明确：Gateway 如何区分「旧版 PC（无 push_id）」「新版 PC 未发 ACK」？当前设计 push_id 可选，旧版忽略。若 Gateway 发带 push_id 的 push，旧版不 ack，超时 503。 | 已覆盖；可补充「Gateway 可通过 device 版本或首次 ack 行为推断」作为可选优化。 |
| **遗漏场景** | **relay_request 与 refresh 并发**：R4 的 `relay-refresh-for-pc` 与 relay_request 可能并发。若 mobile 发起 relay_request 的同时 PC 调用 refresh，Gateway 的 `_device_to_session` 与 `_pending_relay_sessions` 的更新顺序需明确。 | 与 R4 协调：relay_request 创建新 session 会覆盖 `_device_to_session`；refresh 仅续期，不创建。需在 R4 中明确「refresh 时若 relay_request 刚创建新 session，refresh 操作的是哪个 session？」——应为 `_device_to_session[device_id]` 指向的当前 session。 |

### 1.2 R2/R3 Mobile Delay + Relay Wait 设计

| 缺口类型 | 描述 | 建议补充 |
|----------|------|----------|
| **遗漏场景** | **手机 2s 延迟与重试的配合**：文档说「失败重试时无此延迟」。但 `connect_via_relay_only` 的重试逻辑是：首次前 sleep(2s)，然后 for attempt 1..=4 调用 connect_via_relay。若第一次失败（非 session 错误），第 2、3、4 次重试前有 2/4/8s 退避。此时**不再**有 2s 初始延迟。需确认：session 错误触发 `relay_request` 重新获取 session 后，**新一轮** 4 次尝试是否再次 sleep(2s)？ | 明确：每次 `relay_request` 返回后、首次 connect 前都 sleep(2s)；即「新 session 新延迟」。 |
| **边界条件** | **WAIT_FOR_PC 20s 与 QUIC 30s 的关系**：PC 的 QUIC 建连超时 30s。若 PC 在 25s 时建连成功并 RegisterPc，但 Relay 的 WAIT_FOR_PC 仅 20s，手机 T+2s 即 ConnectRequest，Relay 在 T+22s 时已放弃。此时 PC 在 T+25s 才到，会失败。 | 文档已提 QUIC 30s；需明确：WAIT_FOR_PC 20s 是「手机 ConnectRequest 后的等待」，若手机 T+2s 发 ConnectRequest，Relay 等到 T+22s。PC 最晚 T+22s 需 RegisterPc。QUIC 30s 是 PC 端建连超时，若 PC 25s 才连上，已超 Relay 等待。可接受；补充说明「PC 建连需在 20s 内完成，否则 Relay 已放弃」。 |
| **遗漏场景** | **Gateway / Relay 部署不同步**：若 Gateway 先改为 20s，Relay 仍为 10s，则 Gateway 的 session 存活 20s 但 Relay 的 SESSION_TTL 仅 10s，PC RegisterPc 时可能被 Relay 拒绝（PcEntry 的 registered_at 起算，但 validate_relay_session 调 Gateway，Gateway 未过期）。需统一部署顺序。 | 文档已建议「Gateway → Relay → 手机」；补充「必须三者 TTL 一致，否则会出现 Gateway 认为有效、Relay 已过期」的边界。 |
| **边界条件** | **INITIAL_DELAY 与慢网模拟**：2s 为经验值。若实际慢网「推送到达 + spawn」需 4s，2s 仍不足。文档建议「慢网模拟测试」；可补充「若生产反馈 2s 不足，可调为 3s」的调优指引。 | 低优先级；可纳入 Round 2 调优。 |

### 1.3 R4 PC Session Refresh 设计

| 缺口类型 | 描述 | 建议补充 |
|----------|------|----------|
| **遗漏场景** | **R2/R3 将 TTL 改为 20s 后，refresh 延长量**：R4 写「重置 created_at，相当于延长 10s」。若 R2/R3 已实施，`_PENDING_SESSION_TTL_SECS` 为 20s，则 refresh 的语义应为「再活 20s」而非「再活 10s」。否则 session 在 Gateway 端 20s TTL，refresh 只延长 10s，会导致「refresh 后 10s 即过期」的不一致。 | **必须**：refresh 延长量 = `_PENDING_SESSION_TTL_SECS`，随 R2/R3 配置联动。 |
| **遗漏场景** | **PC 调用 refresh 时 session 已被 consume**：Relay 端 session 被第一次 ConnectRequest 消费后，pc_registry 中已移除。PC 重试时若因网络问题拿到旧错误，调用 refresh 续期 Gateway session。但 Relay 端 session 已消费，续期 Gateway 无助于 Relay。此时 PC 应用**原 session_id** 重试 ConnectRequest——若 Relay 已消费，会返回 "PC offline"。正确行为：refresh 仅当「session 未被 Relay 消费、仅因 TTL 过期」时有效。若 Relay 已消费，refresh 无意义，PC 应等 mobile 重试 relay_request 拿新 session。 | 明确：refresh 适用于「Gateway/Relay validate 时 is_expired」的场景；若 Relay 已 consume（第二次 ConnectRequest），refresh 无法挽回。PC 的 refresh 应在「validate_relay_session 返回 404 因过期」时触发，而非「ConnectRequest 返回 PC offline」时——后者可能是 consume 导致。需区分错误来源。 |
| **边界条件** | **relay_request 与 refresh 的竞态**：R4 已提「relay_request 创建新 session 会覆盖 _device_to_session」。若 mobile 快速两次 relay_request（双击），第一次 session A，第二次 session B，_device_to_session 变为 B。PC 可能仍持有 A 的 connect_relay，正在重试。此时 PC 调用 refresh，拿到的是 B 的续期？还是 A？应为 `_device_to_session[device_id]` 即 B。PC 若用 session A 重试会失败。 | 明确：refresh 返回的 session_id 是当前 `_device_to_session` 指向的；PC 必须用该 session_id 重试。若 mobile 已发起新 relay_request，PC 应收到新 connect_relay，旧 session 作废。 |
| **遗漏场景** | **多实例 Gateway 的 _device_to_session**：R4 已标注「多实例需 Redis」。但单实例下，`_device_to_session` 与 `_pending_relay_sessions` 的清理需同步。validate 时 is_expired 会 pop session，此时需 pop `_device_to_session`。R4 已写。需确认 pop 顺序无竞态。 | 已覆盖；可补充「pop 时先 _device_to_session.pop，再 _pending_relay_sessions.pop，避免 refresh 查到已过期 session」。 |
| **边界条件** | **PC 的 is_session_error 误判**：R4 伪代码用 `lower.contains("session")` 或 `lower.contains("expired")`。需排除 "Invalid JWT"、"certificate expired" 等。参考 relay.rs 的 is_session_error。 | 补充：与 relay.rs 的 is_session_error 逻辑保持一致，排除 invalid、certificate 等。 |

### 1.4 E2 RFB Close Reason 设计

| 缺口类型 | 描述 | 建议补充 |
|----------|------|----------|
| **遗漏场景** | **VncBridgeTransport 的 raw channel**：文档说「同时覆盖 URL 直连与 VncBridgeTransport」。VncBridgeTransport 下，RFB 的 WebSocket 来自 bridge 的 raw channel。bridge 的 onclose 已传 `reason: e.payload`。需确认 noVNC 的 rfb 在 bridge 模式下，`_socketClose` 收到的 `e` 是否包含 reason。若 bridge 传了，但 rfb 未用，则 patch 后应能拿到。 | 补充：验证 bridge 模式下 `e.reason` 或 `e.payload` 的传递路径，确保 patch 后两种模式都能拿到 reason。 |
| **边界条件** | **reason 为空或超长**：后端 reason 可能为空字符串，或错误信息很长。`detail.reason` 为空时前端已有 `?? ''` 兜底。超长时是否截断？可暂不处理，后续若有 UX 问题再优化。 | 低优先级；可注明「reason 长度无限制，前端展示可考虑截断」。 |
| **遗漏场景** | **disconnect 与 _fail 的时序**：`_fail` 会设置 `_rfbCloseReason`，然后可能调用 `_updateConnectionState('disconnected')`。若 `_socketClose` 与 `_fail` 都能触发 disconnect，需确保 `_rfbCloseReason` 在 dispatch 时已正确设置。文档中位置 2 在 `_fail` 内设置，位置 1 在 `_socketClose` 内。若 `_fail` 先于 `_socketClose` 调用，`_socketClose` 可能覆盖 reason。需理清调用顺序。 | 补充：分析 noVNC 中 `_socketClose` 与 `_fail` 的调用关系，确保 reason 不被错误覆盖。 |
| **边界条件** | **patch 与 noVNC 升级**：文档已提「升级时检查 patch」。可补充「pin @novnc/novnc 版本，升级时需回归测试 patch」。 | 已覆盖；可加版本 pin 建议。 |

---

## 2. 方案间冲突

### 2.1 R1/R5 与 R4：relay-refresh-for-pc 与 ACK 是否冲突？

**结论：无直接冲突，但需明确分工。**

| 维度 | R1/R5 ACK | R4 relay-refresh-for-pc |
|------|-----------|-------------------------|
| **解决问题** | 推送未送达（R1）、推送丢失（R5） | 推送已送达，但 PC 建连慢，session 过期（R4） |
| **触发时机** | relay_request 时，Gateway 等 ACK 后返回 | PC connect_via_relay 重试失败且 session 错误时 |
| **冲突点** | 无 | 无 |

**协调要点**：
- R1/R5 方向 A 实施后，Gateway 返回 200 时 PC 已 ACK，即 PC 已收到 push。但 PC 的 `connect_via_relay` 可能因 QUIC 慢、Relay 等待超时等失败。
- R4 的 refresh 针对的是「session 在 Gateway/Relay 端过期」——即 PC 建连超过 TTL。此时 ACK 早已完成，refresh 是独立的重试辅助手段。
- **需明确**：R4 的 `relay-refresh-for-pc` 与 R1/R5 的 `send_push_and_wait_ack` 共享 Gateway 的 `_pending_relay_sessions`。refresh 续期的是同一 session，ACK 确认的是 push 送达。两者操作同一 session 的不同维度，无互斥。

### 2.2 R2/R3 的 20s 与 R4 的 refresh 如何配合？

**结论：存在配置联动，必须协调。**

| 问题 | 说明 |
|------|------|
| **TTL 统一** | R2/R3 将 `WAIT_FOR_PC_TIMEOUT`、`SESSION_TTL`、`_PENDING_SESSION_TTL_SECS` 改为 20s。R4 的 refresh「延长 10s」需改为「延长 20s」或「延长 _PENDING_SESSION_TTL_SECS」。 |
| **refresh 语义** | refresh 应「重置 created_at」，使 session 再活 `_PENDING_SESSION_TTL_SECS`。即 refresh 延长量 = 当前 TTL 配置，非硬编码 10s。 |
| **实施顺序** | 若先实施 R2/R3，则 R4 设计时直接采用 20s；若先实施 R4，则 R4 的 refresh 延长量应引用 `_PENDING_SESSION_TTL_SECS` 常量，避免硬编码。 |

**建议**：R4 文档修改为「refresh 重置 created_at，session 再活 `_PENDING_SESSION_TTL_SECS`（与 relay_request 创建时一致）」。

### 2.3 R1/R5、R2/R3、R4 的时序关系

```
T+0:    mobile relay_request
T+0~1:  Gateway push, (R1/R5) 等 ACK
T+1:    mobile 拿到 session_id, (R2/R3) sleep(2s)
T+3:    mobile 首次 connect_via_relay
T+0~?:  PC 收 push, ACK, spawn connect_via_relay, QUIC 建连...
T+?:    PC RegisterPc 或 失败重试
```

- R2/R3 的 20s：mobile T+3 发 ConnectRequest 后，Relay 最多等到 T+23。PC 需在 T+23 前 RegisterPc。
- R4 的 refresh：若 PC 在 T+15 时第一次失败（session 过期），可调用 refresh 续期，再重试。续期后 Gateway session 再活 20s，Relay 的 validate 会通过（若 Gateway 与 Relay TTL 一致）。

---

## 3. 实施依赖与建议顺序

### 3.1 依赖图

```
                    ┌─────────────┐
                    │   E2        │  独立，无依赖
                    │ RFB reason  │
                    └──────┬──────┘
                           │
┌─────────────┐     ┌──────┴──────┐     ┌─────────────┐
│  R2/R3      │     │             │     │   R4        │
│ 20s + 2s    │────>│  协调点     │<────│  refresh    │
│ 延迟        │     │  TTL 统一   │     │             │
└──────┬──────┘     └──────┬──────┘     └──────┬──────┘
       │                   │                   │
       │                   │                   │
       v                   v                   v
┌─────────────────────────────────────────────────────┐
│  R1/R5 ACK                                          │
│  依赖：R2/R3、R4 可并行，但 R1/R5 与 R2/R3 无依赖   │
└─────────────────────────────────────────────────────┘
```

### 3.2 建议实施顺序

| 阶段 | 任务 | 理由 |
|------|------|------|
| **1** | R2/R3（20s + 2s 延迟） | 改动小、无 API 变更、立即改善成功率；先统一 TTL 为 20s，为 R4 奠定基础 |
| **2** | R4（relay-refresh-for-pc） | 依赖 R2/R3 的 TTL 配置；实施时 refresh 延长量 = 20s |
| **3** | R1/R5（ACK） | 与 R2/R3、R4 无强依赖；可并行开发，但建议 R2/R3 上线后再上 R1/R5，避免一次改动过多 |
| **4** | E2（RFB patch） | 完全独立，可与 1–3 任意阶段并行；建议尽早，改善用户可见错误反馈 |

**并行建议**：
- E2 与 R2/R3 可同时开发、同时上线。
- R4 与 R1/R5 可并行开发，但 R4 需等 R2/R3 的 TTL 合并后再定 refresh 延长量。

---

## 4. 具体修改建议

### 4.1 R1/R5 PUSH-ACK 设计

| 位置 | 修改内容 |
|------|----------|
| §3.1.2 兼容性 | 补充：并发 relay_request 时，每个 push 独立 push_id，Future 以 push_id 为 key，无冲突。 |
| §4.1 风险 | 补充：PC 发 ACK 前崩溃 → 503，手机重试 relay_request 拿新 session；旧 session 自然过期。 |
| §5.3 与 R2/R3/R4 的关系 | 补充：与 R4 的 relay-refresh-for-pc 共享 `_pending_relay_sessions`，无冲突；R4 续期时 ACK 已完成。 |
| 新增 | 方向 C 若采用：明确重试推送时 PC 已 spawn 的幂等处理，同一 session_id 只 spawn 一次（可加内存 set 去重）。 |

### 4.2 R2/R3 Mobile Delay 设计

| 位置 | 修改内容 |
|------|----------|
| §2.1 手机侧短延迟 | 明确：每次 `relay_request` 返回后、新一轮 connect 尝试前，都执行 sleep(2s)。即 session 刷新后重新 relay_request 拿到新 session，首次 connect 前仍有 2s 延迟。 |
| §2.2 WAIT_FOR_PC | 补充：PC 建连需在 WAIT_FOR_PC_TIMEOUT(20s) 内完成；若 QUIC 超过 20s，Relay 已放弃，PC 建连成功也无意义。 |
| §4.1 风险 | 补充：Gateway / Relay / 手机 三者 TTL 必须同时升级，否则会出现「Gateway 认为有效、Relay 已过期」的边界故障。 |
| §5 实施顺序 | 补充：部署顺序 Gateway → Relay → 手机，且需同版本发布或明确兼容矩阵。 |

### 4.3 R4 PC Session Refresh 设计

| 位置 | 修改内容 |
|------|----------|
| §2.2 推荐方案 A1 | **必须**：refresh 延长量改为「再活 `_PENDING_SESSION_TTL_SECS`」，非硬编码 10s。若 R2/R3 已实施则为 20s。 |
| §2.2 设计要点 | 补充：refresh 适用于「validate_relay_session 因 session 过期返回 404」的场景。若 Relay 已 consume session（第二次 ConnectRequest），refresh 无法挽回；此时 PC 应等 mobile 重试 relay_request。 |
| §3.3 PC 端变更 | 补充：`is_session_error` 与 relay.rs 保持一致，排除 "invalid"、"certificate" 等，避免误触发 refresh。 |
| §4.1 风险 | 补充：`relay_request` 与 refresh 并发时，`_device_to_session` 指向最新 session；PC 必须用 refresh 返回的 session_id 重试，若 mobile 已发起新 relay_request，PC 会收到新 connect_relay，旧 session 作废。 |
| §5 实施顺序 | 补充：依赖 R2/R3 的 TTL 配置；若 R2/R3 未实施，R4 的 refresh 延长量暂用 10s，R2/R3 实施后改为 20s。 |

### 4.4 E2 RFB Close Reason 设计

| 位置 | 修改内容 |
|------|----------|
| §2.2 推荐方案 | 补充：验证 VncBridgeTransport 模式下，bridge 传的 reason 能否经 patch 后到达 disconnect detail。 |
| §2.4 具体修改 | 补充：分析 `_socketClose` 与 `_fail` 的调用顺序，确保 `_rfbCloseReason` 在 dispatch disconnect 时不被错误覆盖。 |
| §5 实施顺序 | 补充：pin @novnc/novnc 版本，升级时需回归 patch 适用性。 |

---

## 5. 优先级建议

### 5.1 P0（必须优先）

| 方案 | 理由 |
|------|------|
| **R2/R3** | 改动最小、无 API、立即提升成功率；为 R4 的 TTL 统一奠定基础 |
| **R1/R5** | 解决 R1/R5 根因，避免「推送未送达」导致的无效 session；用户感知最直接 |

### 5.2 P1（重要，建议尽快）

| 方案 | 理由 |
|------|------|
| **R4** | 解决 PC 重试无效；依赖 R2/R3 的 TTL，实施时需协调 refresh 延长量 |
| **E2** | 改善用户可见错误，P2P 失败时能展示 "PC offline or session expired" 等具体信息；独立可并行 |

### 5.3 P2（可后续）

| 项目 | 说明 |
|------|------|
| R1/R5 方向 C（ACK+重试） | 若方向 A 生产反馈 503 率偏高，再考虑方向 C |
| INITIAL_DELAY 调优 | 2s 若不足可调 3s，需生产数据支撑 |
| 多实例 Gateway 的 Redis | R4 的 `_device_to_session` 多实例扩展，当前单实例可满足 |

---

## 6. 总结

| 维度 | 结论 |
|------|------|
| **缺口** | 四份设计均有遗漏场景或边界条件，见 §1；以 R4 与 R2/R3 的 TTL 联动、R4 的 refresh 适用场景最为关键 |
| **冲突** | R1/R5 与 R4 无冲突；R2/R3 与 R4 存在配置联动，R4 的 refresh 延长量必须与 TTL 一致 |
| **依赖** | 建议顺序：R2/R3 → R4 → R1/R5；E2 可并行 |
| **修改** | 每份设计需补充的点见 §4 |
| **优先级** | P0: R2/R3、R1/R5；P1: R4、E2；P2: 方向 C、调优、多实例 |

---

*Round 1 交叉评审完成，建议各设计按 §4 修改后进入 Round 2。*
