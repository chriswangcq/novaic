# Phase 2 测试审查报告

> 4 名测试工程师对 Phase 2 变更的客观审查结果。

---

## 一、Tester 1：Registry 与类型

### 1.1 GatewayRegistry base_url 为快照

- **问题**：`GatewayRegistry` 接受 `base_url: String`，用户修改 Gateway URL 后需重启才生效
- **对比**：`GatewayDiscovery` 使用 `Arc<Mutex<String>>`，可动态更新
- **建议**：统一为 `Arc<Mutex<String>>`

### 1.2 MdnsRegistry 重复 register 被忽略

- **问题**：首次 `register()` spawn advertise，后续 `register()` 直接返回，descriptor 变更（如 hostname）不会更新
- **影响**：低，单次会话内通常不变
- **结论**：可接受，文档注明

### 1.3 MdnsDiscovery 返回的 descriptor 无 cert_der_b64

- **问题**：mDNS 发现的设备无 P2P 证书，`ServerDescriptor` 缺少 `cert_der_b64`
- **影响**：若将 MdnsDiscovery 加入 CompositeDiscovery 且优先于 Gateway，P2P connect 会失败
- **建议**：CompositeDiscovery 在用于 P2P 时跳过无 cert 的 descriptor，或文档明确：P2P 仅用 GatewayDiscovery

---

## 二、Tester 2：Discovery 与 CompositeDiscovery

### 2.1 CompositeDiscovery 吞掉 Err

- **问题**：`if let Ok(Some(d)) = backend.lookup(id).await` 在返回 `Err` 时继续下一个 backend，最终可能返回 `Ok(None)`
- **影响**：Gateway 网络错误时，用户看到「Device not found」而非真实错误
- **建议**：至少记录最后一个 Err，或提供「全部失败时返回最后错误」的选项

### 2.2 MdnsDiscovery 需外部 shutdown

- **问题**：`MdnsDiscovery::new(shutdown)` 需传入 `Arc<Notify>`，当前 setup 未使用 MdnsDiscovery，无影响
- **结论**：若未来使用，需在 app shutdown 时 notify

### 2.3 GatewayDiscovery token 为空

- **问题**：用户未登录时 token 为空，locate 会 401
- **结论**：当前返回 `Ok(None)` 或 Err，vnc_proxy 已有「Not logged in」校验，可接受

---

## 三、Tester 3：Server 与集成

### 3.1 run_registry_loop 首次 register 失败未重试

- **问题**：首次 `registry.register()` 失败时返回 `?`，整个 start 失败
- **对比**：后续 interval 内失败仅 warn，不中断
- **建议**：首次失败可考虑重试 1–2 次，或与后续逻辑一致（warn 后继续）

### 3.2 vmcontrol 同时存在 mDNS 与 Registry

- **问题**：vmcontrol 已有独立 mDNS advertise，Registry 目前仅用 GatewayRegistry，无重复
- **结论**：若未来加入 MdnsRegistry，会与现有 mDNS 重复广播，需二选一

### 3.3 GatewayRegistry token 为空时 register 失败

- **问题**：未登录时 `heartbeat` 失败，run_registry_loop 仅 warn
- **结论**：可接受，登录后下次 interval 会成功

---

## 四、Tester 4：Client 与边界

### 4.1 connect_via_descriptor 对 Relay 直接 bail

- **问题**：`EndpointInfo::Relay` 时直接 `bail`，符合 Phase 4 规划
- **结论**：符合设计

### 4.2 device_id 截断导致错误信息不完整

- **问题**：`anyhow!("Device {} not found", &target_device_id[..8.min(...)])` 仅显示前 8 字符
- **影响**：低，便于日志
- **结论**：可接受

### 4.3 P2pClientConfig 无 Debug

- **问题**：`P2pClientConfig` 移除 `#[derive(Debug)]`（因 `Arc<dyn Discovery>`）
- **影响**：调试时无法完整打印 config
- **建议**：可添加 `impl Debug` 手动实现

---

## 五、修复优先级与状态

| 优先级 | 问题 | 状态 |
|--------|------|------|
| P1 | GatewayRegistry base_url 改为 Arc<Mutex<String>> | ✅ 已修复 |
| P2 | CompositeDiscovery 跳过无 cert_der_b64 的 descriptor | ✅ 已修复（new_for_p2p + require_cert） |
| P2 | CompositeDiscovery 记录/返回最后 Err | ✅ 已修复 |
| P3 | 首次 register 失败时重试 3 次 | ✅ 已修复 |
