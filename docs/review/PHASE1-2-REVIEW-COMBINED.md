# Phase 1+2 整体测试审查报告

> 4 名测试工程师对 Phase 1 与 Phase 2 整体变更的客观审查。

---

## 一、Tester 1：device_id 双轨与一致性

### 1.1 device_id 双轨（已知设计）

- **vmcontrol mDNS**：`device_id` = UUID（`load_or_generate_device_id`），用于 LAN HTTP 服务发现
- **P2P / local_vmcontrol**：`device_id` = Ed25519 hex（`p2p::DeviceIdentity`），用于 QUIC 打洞与 VncProxy 路由
- **数据流**：
  - 桌面 VNC：`local_vmcontrol.device_id`（Ed25519）→ 路由匹配 ✓
  - 移动端远程：my-devices 返回 Gateway 注册的 device_id（Ed25519）→ locate → 打洞 ✓
  - mDNS 发现：UUID，用于 LAN HTTP 直连，不经过 VncProxy
- **结论**：P2P 路径一致。mDNS 与 P2P 使用不同 ID 体系，无冲突。

### 1.2 get_vnc_proxy_url 参数命名

- **问题**：`deviceId` 参数实际用作 `agent_id`（VM/agent 标识），易混淆
- **影响**：低，调用方可能误解
- **建议**：重命名为 `agentId` 或补充注释

### 1.3 p2p_setup_error 的 device_id

- **问题**：存储 Ed25519；若前端用 UUID 展示「本机」，P2P 失败时无法命中
- **结论**：已知限制，见 Phase 1 审查

---

## 二、Tester 2：集成与数据流

### 2.1 Identity 重复加载

- **位置**：vmcontrol/lib.rs
- **问题**：`DeviceIdentity::load_or_generate` 在 vmcontrol 和 `P2pServer::start` 内各调用一次
- **影响**：低，仅冗余 IO
- **建议**：可传入 identity 避免重复，非必须

### 2.2 Registry 路径下 cloud_config 仍传入

- **问题**：使用 registry 时，`start()` 仍接收 `cloud_config`，但不再用于 heartbeat
- **影响**：无功能影响，仅冗余参数
- **结论**：可接受，保留便于未来扩展

### 2.3 setup 使用单 Discovery

- **现状**：setup 仅用 `GatewayDiscovery`，未用 `CompositeDiscovery`
- **结论**：符合当前需求；若加入 MdnsDiscovery，应使用 `CompositeDiscovery::new_for_p2p`

---

## 三、Tester 3：错误处理与边界

### 3.1 Discovery lookup 空 token

- **问题**：token 为空时，GatewayDiscovery.locate 会 401
- **现状**：vnc_proxy 在 `get_or_create_remote_conn` 中先检查 token，空则 bail
- **结论**：已覆盖

### 3.2 device_id 空字符串

- **问题**：`device_id[..8.min(device_id.len())]` 在空串时为 `[..0]`
- **结论**：安全，不会 panic

### 3.3 run_registry_loop 首次 3 次重试后仍失败

- **问题**：3 次重试均失败时，仍 spawn 循环，后续 interval 继续失败
- **结论**：可接受，不阻塞 start

---

## 四、Tester 4：代码质量与可维护性

### 4.1 server.rs use 顺序

- **问题**：`std::collections::HashMap` 与 `std::net::SocketAddr` 分散
- **建议**：合并 std 的 use

### 4.2 P2pServerConfig / P2pClientConfig 无 Debug

- **问题**：含 `Arc<dyn Trait>` 无法 derive Debug
- **影响**：调试时无法完整打印
- **结论**：可接受，可后续手动 impl Debug

### 4.3 config 模块依赖

- **问题**：config 依赖 discovery、registry，模块顺序需正确
- **结论**：当前无循环依赖，正常

---

## 五、修复优先级与状态

| 优先级 | 问题 | 状态 |
|--------|------|------|
| P2 | get_vnc_proxy_url 参数命名 | ✅ 已加注释说明 |
| P2 | server.rs use 整理 | ✅ 已合并 std use |
| P3 | Identity 重复加载 | 📝 可选优化 |
| P3 | device_id 双轨 | 📝 已文档注明 |
