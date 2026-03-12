# P2P 模块化重构方案汇总（A / B / C）

> 三名架构师对 Rust app backend 与 vmcontrol 的 P2P 连接现状进行研究后的改造方案汇总。

---

## 一、现状共识

| 问题 | 描述 |
|------|------|
| **紧耦合** | vmcontrol 直接调用 p2p 的 5+ 子模块；vnc_proxy 直接调用 hole_punch |
| **硬编码** | P2P_PORT=19998 分散在 vmcontrol、vnc_proxy；STUN 服务器固定 |
| **流程固定** | STUN → QUIC bind → heartbeat → accept 无法替换或跳过 |
| **relay 难接入** | punch 超时直接失败，无 relay 兜底；connect_relay 无清晰集成点 |
| **平台逻辑混杂** | Desktop 的 local_conn 与 Mobile 的 remote_conns 混在 vnc_proxy |

---

## 二、方案 A：p2p 分层抽象（Server / Client）

**重点**：在 p2p crate 内建立统一入口，vmcontrol 和 vnc_proxy 仅依赖 P2pServer / P2pClient。

### 核心设计

```
vmcontrol / vnc_proxy
        │
        ▼
┌─────────────────────────────────────┐
│  P2pServer / P2pClient（统一入口）   │
│  - P2pServerConfig, P2pClientConfig │
│  - ConnectStrategy: DirectOnly / DirectThenRelay │
└─────────────────────────────────────┘
        │
        ▼
p2p 内部：stun, transport, rendezvous, tunnel, relay
```

### 关键点

- **P2pServer**：封装 STUN → QUIC bind → heartbeat → accept，返回 `LocalVmControlInfo` + shutdown handle
- **P2pClient**：封装 locate + punch（+ relay fallback），`connect()` 返回 `Connection`
- **可配置**：端口、STUN、心跳间隔、连接策略（DirectOnly / DirectThenRelay）
- **可插拔**：StunProvider trait、预留 Transport trait

### 优点

- 改动集中在 p2p crate，vmcontrol / vnc_proxy 改动较小
- 配置化、可测试（MockStunProvider）
- Relay 通过 ConnectStrategy 自然接入

### 缺点

- vnc_proxy 仍持有 local_conn / remote_conns 缓存逻辑
- connect_relay 的 PC 端处理未明确归属

---

## 三、方案 B：连接解析器与连接池（ConnectionResolver）

**重点**：抽取连接获取为独立组件，VncProxy 只依赖 ConnectionResolver，不直接调用 hole_punch。

### 核心设计

```
VncProxy (HandlerState)
        │
        ▼
┌─────────────────────────────────────┐
│  ConnectionResolver (trait)         │
│  - resolve(device_id) → Connection  │
└─────────────────────────────────────┘
        │
        ▼
┌─────────────────────────────────────┐
│  DefaultConnectionResolver          │
│  - P2pConnectionPool (local/remote) │
│  - resolve_local / resolve_remote   │
│  - relay_fallback: bool             │
└─────────────────────────────────────┘
        │
        ▼
p2p::connection (connect_to_peer, punch_and_connect, punch_or_relay)
```

### 关键点

- **ConnectionResolver**：抽象「按 device_id 获取 Connection」
- **P2pConnectionPool**：统一管理 local_conn、remote_conns 缓存
- **p2p::connection**：统一入口，对外暴露 punch_or_relay
- **relay fallback**：resolver 构造时 `relay_fallback: bool` 控制

### 优点

- VncProxy 与 hole_punch 完全解耦
- 连接池逻辑清晰，便于复用和测试
- 桌面 / 移动端通过 `local_info` 是否为空自动区分

### 缺点

- PC 端 connect_relay 建立的连接与 VncProxy 的 remote_conns 如何共享未完全展开
- 未解决 CloudBridge 与 VncProxy 的协调问题

---

## 四、方案 C：P2P Orchestrator 统一编排

**重点**：引入 P2P Orchestrator 作为统一编排层，协调 CloudBridge、VncProxy、VmControl 的 P2P/Relay 逻辑。

### 核心设计

```
                    ┌─────────────────────────────────────┐
                    │     P2P Orchestrator                 │
                    │  - get_connection(device_id)        │
                    │  - on_connect_relay(url, session)   │
                    │  - PlatformKind: Desktop / Mobile   │
                    └─────────────────────────────────────┘
                                         │
        ┌────────────────────────────────┼────────────────────────────────┐
        ▼                                ▼                                ▼
   VncProxy                        CloudBridge                      VmControl
   get_connection()               connect_relay → on_connect_relay   P2P Server
```

### 关键点

- **P2POrchestrator**：统一连接获取、relay 入站处理、连接缓存
- **PlatformKind**：Desktop（local + remote）vs Mobile（仅 remote）
- **connect_relay 集成**：CloudBridge 解析消息 → 调用 Orchestrator.on_connect_relay → Orchestrator 建连并 spawn run_tunnel_server
- **依赖注入**：gateway_url、cloud_token、relay_url 均可注入

### 优点

- connect_relay 有明确归属，逻辑不分散
- 平台差异内聚到 Orchestrator，VncProxy 无平台分支
- 为未来 relay、多设备等扩展留足空间

### 缺点

- 需新建 p2p_orchestrator 模块，迁移成本较高
- CloudBridge 需持有 Orchestrator 引用，依赖关系更复杂

---

## 五、三方案对比

| 维度 | 方案 A | 方案 B | 方案 C |
|------|--------|--------|--------|
| **改造重心** | p2p crate | vnc_proxy + p2p::connection | 新建 Orchestrator + 全链路 |
| **vmcontrol 改动** | 大（改用 P2pServer） | 小 | 中 |
| **vnc_proxy 改动** | 中（改用 P2pClient） | 大（接入 Resolver） | 大（接入 Orchestrator） |
| **connect_relay 归属** | 未明确 | 未明确 | Orchestrator.on_connect_relay |
| **平台抽象** | 无 | 隐式（local_info） | 显式（PlatformKind） |
| **配置化** | 强（Server/Client Config） | 中（relay_fallback） | 强（全量注入） |
| **迁移成本** | 低 | 中 | 高 |
| **扩展性** | 中 | 中 | 高 |

---

## 六、推荐组合与实施建议

### 组合 1：A + B（渐进式）

1. **Phase 1**：实施方案 A，在 p2p 内新增 P2pServer、P2pClient，vmcontrol 和 vnc_proxy 逐步切换
2. **Phase 2**：实施方案 B，抽取 ConnectionResolver、P2pConnectionPool，VncProxy 接入
3. **Phase 3**：实现 relay（punch_or_relay、connect_via_relay），CloudBridge 处理 connect_relay 时需单独设计共享点

**适用**：希望分步推进、先解决 p2p 与 vnc_proxy 解耦，connect_relay 可后续迭代。

### 组合 2：C 为主（一步到位）

1. 直接引入 P2P Orchestrator
2. VncProxy、CloudBridge 统一接入
3. 在 Orchestrator 内复用方案 A 的 P2pServer/P2pClient 思想（或方案 B 的 ConnectionResolver）

**适用**：connect_relay 即将上线，希望一次性解决编排与平台抽象。

### 组合 3：A + C 融合

1. p2p 内实现 P2pServer、P2pClient（方案 A）
2. 新建 P2P Orchestrator，内部使用 P2pClient 获取连接，对外提供 get_connection、on_connect_relay
3. VncProxy、CloudBridge 只依赖 Orchestrator

**适用**：既要 p2p 内部模块化，又要顶层统一编排。

---

## 七、详细文档索引

| 方案 | 文档路径 |
|------|----------|
| A | `docs/P2P_REFACTOR_PROPOSAL_A.md` |
| B | `docs/REFACTOR-VNCPROXY-P2P-CONNECTION-POOL.md` |
| C | `docs/DESIGN-P2P-ORCHESTRATOR-PROPOSAL-C.md` |
