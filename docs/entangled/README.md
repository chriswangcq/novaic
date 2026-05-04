# Entangled 实时同步架构拆页地图

> 本目录（`docs/entangled/`）提供 Entangled 同步引擎架构的最细粒度源码级拆解。这套架构从独立服务重构为【层级融合 + 端侧 Headless】形态，并彻底落地于前端 Path C。

与主干架构文档 [docs/entangled-architecture.md](../entangled-architecture.md) 配合食用。

## 目录索引

### 核心层分解 (Python 后端侧)
| 专题 | 说明 |
|------|------|
| [protocol-layer-and-ws.md](protocol-layer-and-ws.md) | `entangled.server`：PubSub、同步协商约束、`syncContractVersion`。 |
| [sql-persistence-and-def.md](sql-persistence-and-def.md) | `entangled.sql`：SQLite 持久层、WAL 锁、`EntityDef`/`FieldDef`。 |
| [python-app-shell.md](python-app-shell.md) | `entangled.app`：被替代的独立独立服务壳、集成 JWT 的免代码服务。 |

### 业务级集成 (Gateway 侧)
| 专题 | 说明 |
|------|------|
| [gateway-integration.md](gateway-integration.md) | `novaic-gateway` 如何放弃手写 SQL、全面继承 Hooks 等融合方案。 |
| [schema-and-cascade-push.md](schema-and-cascade-push.md) | Schema 推送与通知机制（一次写入 = 一次通知，无自动级联）。 |

### 客户端侧 (Rust / React 侧)
| 专题 | 说明 |
|------|------|
| [react-rust-client.md](react-rust-client.md) | Path C Headless 架构：为什么不再基于 IndexedDB、由 Rust 做 SQLite Master。 |
| [optimistic-and-pending.md](optimistic-and-pending.md) | 历史机制说明：旧 optimistic / `pending_ops` 路径已退役，当前 App cache 是 read-model。 |
| [nav-slots-and-routing.md](nav-slots-and-routing.md) | Rust 侧的新路网：Slot-based `NavState` 路由与 Refcount 如何彻底解决组件乱丢重连问题。 |
