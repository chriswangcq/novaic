# Phase 1 第二轮测试审查报告

> 4 名测试工程师对 Phase 1 整体变更（含首轮修复后）的客观审查。

---

## 一、Tester 1：Config 与边界值

### 1.1 heartbeat_interval_secs = 0 未校验

- **位置**：`config.rs`、`server.rs`
- **问题**：若配置 `heartbeat_interval_secs: 0`，`tokio::time::interval(Duration::ZERO)` 会立即连续 tick，导致忙循环
- **建议**：在 server 或 config 中校验，最小 1s

### 1.2 P2pServerConfig.port = 0 未校验

- **位置**：`server.rs`
- **问题**：`resolve_p2p_port()` 已校验，但 `P2pServerConfig` 可由调用方直接构造，传入 `port: 0` 时 `listen_for_peer(0)` 会绑定临时端口
- **建议**：在 `P2pServer::start()` 开头校验 `port != 0`

### 1.3 stun_retry_interval_secs = 0

- **问题**：同上，可能导致 STUN 重试过于频繁
- **建议**：与 heartbeat 一并校验

---

## 二、Tester 2：并发与锁

### 2.1 get_or_create_local_conn 持锁过长

- **位置**：`vnc_proxy.rs:283-318`
- **问题**：`local_conn.lock()` 贯穿整个函数，包括 retry 循环（最多 1.5s）。并发打开多个 VNC 时，后续请求会阻塞
- **影响**：中等，多窗口场景下首连延迟明显
- **建议**：retry 循环前释放锁，仅在「检查缓存 → 建连 → 写回」时持锁

---

## 三、Tester 3：Client 与超时

### 3.1 connect_direct 本地 loopback 超时

- **问题**：本地 127.0.0.1 连接极快，但仍使用 punch_timeout_secs（默认 15s）
- **影响**：低，仅影响错误时等待时间
- **结论**：可接受，暂不修改

### 3.2 ConnectStrategy / relay_url 仍未使用

- **结论**：Phase 4 预留，已在注释中说明

---

## 四、Tester 4：集成与 device_id

### 4.1 p2p_setup_error 的 device_id 与前端可能不一致

- **问题**：`p2p_setup_error` 存储的是 `p2p::DeviceIdentity.id`（Ed25519 hex），前端「本机」可能来自 cloud `my-devices`（UUID）
- **影响**：P2P 失败时，用户点本地 VNC 可能仍走 remote 路径，无法命中「P2P setup failed」提示
- **建议**：文档注明；或同时存储 cloud device_id（若可获取）

### 4.2 其他

- accept shutdown、listener.close、config 接入均正确
- 首轮修复已覆盖主要问题

---

## 五、修复优先级与状态

| 优先级 | 问题 | 状态 |
|--------|------|------|
| P1 | heartbeat/stun_retry = 0 导致忙循环 | ✅ 已修复（.max(1)） |
| P1 | P2pServer::start port=0 未校验 | ✅ 已修复 |
| P2 | get_or_create_local_conn 持锁过长 | ✅ 已修复（retry 前释放锁） |
| P3 | device_id 不一致（p2p hex vs cloud UUID） | 📝 已知限制，见 4.1 |
