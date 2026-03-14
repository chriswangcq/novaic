# Phase 2 任务分工（4 名工程师）

> 参考 `docs/DESIGN-P2P-UNIFIED.md`、`docs/DESIGN-P2P-REGISTRATION-DISCOVERY.md`

---

## 工程师 1：types + Registry trait

**产出**：`p2p/src/types.rs` 扩展、`p2p/src/registry/mod.rs`

**内容**：
1. `types.rs`：新增 `ServerDescriptor`、`EndpointInfo`（Direct / Relay）
2. `registry/mod.rs`：`Registry` trait（register, unregister）、`CompositeRegistry`

**依赖**：无

---

## 工程师 2：Registry 实现

**产出**：`p2p/src/registry/gateway.rs`、`p2p/src/registry/mdns.rs`

**内容**：
1. `GatewayRegistry`：包装 `rendezvous::heartbeat`，从 `ServerDescriptor` 构造 `HeartbeatRequest`
2. `MdnsRegistry`：包装 `local_discovery::advertise`，从 `ServerDescriptor` 构造 `VmControlService`

**依赖**：工程师 1

---

## 工程师 3：Discovery trait + 实现

**产出**：`p2p/src/discovery/mod.rs`、`gateway.rs`、`mdns.rs`

**内容**：
1. `Discovery` trait（lookup）、`CompositeDiscovery`
2. `GatewayDiscovery`：包装 `rendezvous::locate`，返回 `ServerDescriptor`
3. `MdnsDiscovery`：维护 mDNS 发现缓存，`lookup(id)` 从缓存返回

**依赖**：工程师 1

---

## 工程师 4：集成

**产出**：修改 `config`、`server`、`client`、`vmcontrol`、`vnc_proxy`、`setup`

**内容**：
1. `P2pServerConfig`：新增 `registry: Option<Arc<dyn Registry>>`
2. `P2pServer::start`：若有 registry 则用 `registry.register` 替代直接 heartbeat；支持 `CompositeRegistry`（Gateway + mDNS）
3. `P2pClientConfig`：新增 `discovery: Option<Arc<dyn Discovery>>`
4. `P2pClient::connect`：若有 discovery 则 `discovery.lookup(id)`，否则回退到现有 `punch_and_connect(gateway_url, token, id)`
5. vmcontrol / setup：构造 `CompositeRegistry`、`GatewayDiscovery`（或 `CompositeDiscovery`）并注入

**依赖**：工程师 2、3

---

## 实施状态

| 工程师 | 产出 | 状态 |
|--------|------|------|
| 1 | types (ServerDescriptor, EndpointInfo), Registry trait, CompositeRegistry | ✅ |
| 2 | GatewayRegistry, MdnsRegistry | ✅ |
| 3 | Discovery trait, GatewayDiscovery, MdnsDiscovery, CompositeDiscovery | ✅ |
| 4 | config.registry, config.discovery, server/client 集成, vmcontrol/setup 注入 | ✅ |
