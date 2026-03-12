# P2P Phase 4 代码 Review 上下文

> 对照 DESIGN-P2P-UNIFIED.md，对 novaic-app 未提交改动进行挑刺式 review。

## 设计文档要点（DESIGN-P2P-UNIFIED.md）

### 架构分层
- 业务层（vmcontrol, vnc_proxy, CloudBridge）仅依赖 P2pServer / P2pClient
- 不直接 import p2p 子模块（hole_punch, relay 等）

### P2pClient 设计
- `connect(target_id)` — 设计文档无 gateway_url/token 参数
- ConnectStrategy: DirectOnly / DirectThenRelay / RelayOnly
- discovery 注入，connect_strategy 注入

### 连接流程
- 手机：discovery.lookup → Direct(addr) → connect_to_peer 超时 15s → relay-request → connect_via_relay
- PC：CloudBridge 收到 connect_relay → P2pClient::connect_via_relay → spawn run_tunnel_server

### CloudBridge 归属
- 解析 ConnectRelay，调用 P2pClient::connect_via_relay(relay_url, session_id)
- 设计：P2pClient 提供 connect_via_relay，建连后 spawn run_tunnel_server

### 目录结构
- p2p 应有 transport.rs（hole_punch 重命名）、stun.rs 抽离
- 当前：hole_punch.rs 未重命名

## 待 Review 改动文件

- p2p: client.rs, config.rs, relay.rs, server.rs, discovery/, registry/
- hole_punch.rs, rendezvous.rs, crypto.rs, types.rs
- vnc_proxy.rs, cloud_bridge.rs, setup.rs
- vmcontrol main.rs, lib.rs
