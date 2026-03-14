# Phase 1+2+3 整体测试审查报告

> 4 名测试工程师对 Phase 1、2、3 整体变更的客观审查。接受并修复所有有效意见。

---

## 一、测试工程师 1：数据流与一致性

### 1.1 P2pClient relay 兜底未生效（已修复）

- **问题**：使用 `GatewayDiscovery` 时，`connect()` 走 `connect_via_descriptor` → `connect_to_peer`，直连失败（NAT 超时）后**不会**走 relay，relay 兜底形同虚设。
- **根因**：`discovery.lookup` 返回 `Some` 时直接 `return`，无失败重试逻辑。
- **修复**：当 `connect_via_descriptor` 失败时，fallback 到 `punch_or_relay`；`lookup` 返回 `None` 时也尝试 `punch_or_relay`（locate 可能仍在线）。

### 1.2 get_scrcpy_proxy_url 移动端 deviceId=None（已修复）

- **问题**：移动端调用 `get_scrcpy_proxy_url({ deviceSerial })` 未传 `deviceId` 时，使用 `"local"` 作为 device_id，导致 `serve_remote_scrcpy(ws, "local", ...)` → `connect("local")` 失败（Gateway 无 "local" 设备）。
- **修复**：与 `get_vnc_proxy_url` 一致，从 `my-devices` 取第一个在线 device_id。

### 1.3 device_id 双轨（已知设计，已文档化）

- mDNS 使用 UUID，P2P 使用 Ed25519 hex，两套 ID 体系并存，设计如此。

---

## 二、测试工程师 2：集成与边界

### 2.1 GatewayDiscovery token 为空

- **现状**：`lookup` 调用 `locate` 时 token 可能为空，Gateway 返回 401。
- **结论**：`vnc_proxy::get_or_create_remote_conn` 在调用 `connect` 前已检查 `token.is_empty()` 并 bail，不会进入 connect。可接受。

### 2.2 run_registry_loop 与 run_heartbeat_loop 双轨

- **现状**：`P2pServer` 根据 `registry` 或 `cloud_config` 选择不同路径，逻辑清晰。
- **结论**：无问题。

### 2.3 CloudBridge connect_relay 与 VncProxy 时序

- **现状**：手机 `relay-request` 后，Gateway 推 `connect_relay` 给 PC，PC 与手机各自 `connect_via_relay`。PC 可能先连或后连。
- **结论**：relay 端 session TTL 120s，配对逻辑正确。已修复 Phase 3 审查中的 session 泄漏。

---

## 三、测试工程师 3：错误处理与超时

### 3.1 connect_via_relay 超时（Phase 3 已修复）

- QUIC 连接 30s 超时，handshake 读取 15s 超时。

### 3.2 relay handshake 读取挂起（Phase 3 已修复）

- 对 `recv.read_exact` 增加 15s 超时。

### 3.3 relay session TTL（Phase 3 已修复）

- `PcEntry` 含 `registered_at`，TTL 120s，插入前 `retain` 清理过期。

### 3.4 auth device_id URL 编码（Phase 3 已修复）

- 使用 `urlencoding::encode(device_id)`。

---

## 四、测试工程师 4：代码质量与可维护性

### 4.1 vnc_proxy 注释

- 注释仍写「punch_and_connect」，实际为 `P2pClient::connect`（内部 `punch_or_relay`）。建议后续统一为「Gateway locate + punch_or_relay」。

### 4.2 ConnectStrategy 未使用

- **现状**：`P2pClientConfig` 有 `ConnectStrategy::DirectThenRelay`，但 `connect()` 未根据其分支。
- **结论**：当前实现已隐含 DirectThenRelay（先 direct，失败则 relay），枚举可保留供未来扩展。

---

## 五、修复汇总

| 问题 | 文件 | 状态 |
|------|------|------|
| P2pClient relay 兜底未生效 | p2p/src/client.rs | ✅ 已修复 |
| get_scrcpy_proxy_url 移动端 deviceId=None | commands/vnc_urls.rs | ✅ 已修复 |
| relay session TTL / 内存泄漏 | novaic-quic-service/relay.rs | ✅ Phase 3 已修复 |
| connect_via_relay 超时 | p2p/hole_punch.rs | ✅ Phase 3 已修复 |
| auth device_id URL 编码 | novaic-quic-service/auth.rs | ✅ Phase 3 已修复 |
| Gateway RELAY_URL 空校验 | gateway/api/p2p.py | ✅ Phase 3 已修复 |
| validate-device device_id 空校验 | gateway/api/auth.py | ✅ Phase 3 已修复 |

---

## 六、已知限制（不修复）

- device_id 双轨（mDNS UUID vs P2P Ed25519）
- p2p_setup_error 的 device_id 与前端展示可能不一致
- run_registry_loop 首次 3 次重试后仍失败，循环继续（不阻塞 start）
