# Phase 1 测试审查报告

> 4 名测试工程师对 Phase 1 变更的客观审查结果。接受并记录所有有效意见。

---

## 一、Tester 1：config 与配置使用

### 1.1 重复调用 resolve_p2p_port

- **位置**：`config.rs:24`（Default）、`vmcontrol/lib.rs:202-205`
- **问题**：`P2pServerConfig::default()` 在构造时调用 `resolve_p2p_port()`；vmcontrol 又显式传入 `port: resolve_p2p_port()`，导致重复调用
- **影响**：低，仅轻微冗余

### 1.2 P2pServerConfig 未使用字段

| 字段 | 是否使用 | 说明 |
|------|----------|------|
| port | ✅ | server.rs 使用 |
| stun_server | ❌ | rendezvous 使用 NOVAIC_STUN_SERVER |
| heartbeat_interval_secs | ❌ | rendezvous 硬编码 25s |
| stun_retry_interval_secs | ❌ | rendezvous 硬编码 300s |

### 1.3 P2pClientConfig 完全未使用

| 字段 | 是否使用 |
|------|----------|
| connect_strategy | ❌ |
| punch_timeout_secs | ❌ |
| relay_url | ❌ |

- **问题**：`client.rs` 直接调用 `punch_and_connect`，未读取 config
- **影响**：配置形同虚设，API 与实现不符

### 1.4 端口校验缺失

- **问题**：`resolve_p2p_port()` 接受任意 u16，包括 0
- **影响**：port=0 会绑定临时端口，heartbeat 上报端口与实际不符，P2P 不可用

---

## 二、Tester 2：server 生命周期与关闭

### 2.1 严重：accept 循环不响应 shutdown

- **位置**：`server.rs:99-126`
- **问题**：accept 循环在 `tokio::spawn` 中无限循环，未监听 shutdown 信号
- **影响**：应用退出时 accept 任务不会结束，存在任务泄漏

### 2.2 PunchListener 未关闭

- **位置**：`hole_punch.rs` 中 `PunchListener::close()` 存在
- **问题**：shutdown 时未调用 `listener.close()`
- **影响**：QUIC endpoint 和 UDP socket 未显式关闭，资源未完全释放

### 2.3 心跳 shutdown 正常

- 心跳循环通过 `heartbeat_shutdown_rx` 正确停止

---

## 三、Tester 3：client 与设计文档一致性

### 3.1 P2pClient 未使用 config

- **问题**：`connect()` 直接转发到 `punch_and_connect`，不读取 `self.config`
- **影响**：`connect_strategy`、`punch_timeout_secs`、`relay_url` 均无效

### 3.2 超时不可配置

- **问题**：15s 超时写死在 `hole_punch::connect_to_peer`
- **影响**：`P2pClientConfig.punch_timeout_secs` 无法生效

### 3.3 connect_direct 为纯转发

- **问题**：仅转发到 `connect_to_peer`，无额外逻辑
- **影响**：可接受，但价值有限

---

## 四、Tester 4：集成与边界情况

### 4.1 启动竞态（中等）

- **问题**：用户可能在 `local_info` 写入前点击 VNC
- **表现**：`local_id` 为 None → 走 remote 路径；或提示 "No online VmControl device found"
- **建议**：增加短暂重试，或更明确的“P2P 启动中”提示

### 4.2 P2P 失败时错误不清晰（中等）

- **问题**：`p2p_server.start()` 失败时，`local_vmcontrol` 保持 None
- **表现**：本地 VNC 会走 remote 路径，locate 失败，错误信息类似 "Remote P2P connect failed"
- **建议**：记录 P2P 失败状态，在 UI 或错误信息中区分“本地 P2P 未就绪”

### 4.3 其他结论

- 独立 vmcontrol 模式：正常
- 移动端：正常
- 端口重复解析：无功能影响，仅冗余

---

## 五、问题汇总（按严重程度）

| 严重程度 | 问题 | 位置 |
|----------|------|------|
| **高** | accept 循环不响应 shutdown，任务泄漏 | server.rs |
| **高** | PunchListener 未调用 close | server.rs |
| **中** | P2pServerConfig 三个字段未使用 | config.rs, server.rs |
| **中** | P2pClientConfig 全部未使用 | config.rs, client.rs |
| **中** | 启动竞态：VNC 早于 local_info | vnc_proxy, lib.rs |
| **中** | P2P 失败时错误路径与提示不清晰 | vmcontrol, vnc_proxy |
| **低** | resolve_p2p_port 重复调用 | vmcontrol |
| **低** | 端口 0 未校验 | config.rs |

---

## 六、建议修复优先级

1. **P0**：accept 循环增加 shutdown 监听，并在退出时调用 `listener.close()` ✅ 已修复
2. **P1**：要么将 config 字段接入实现，要么移除/标注为预留 ✅ 已修复（server: stun/heartbeat/stun_retry；client: punch_timeout）
3. **P2**：`resolve_p2p_port()` 增加 port=0 校验 ✅ 已修复
4. **P3**：启动竞态与 P2P 失败时的错误提示优化 ✅ 已修复（retry + SharedP2pSetupError）
