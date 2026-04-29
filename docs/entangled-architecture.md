# Entangled (实时实体同步引擎) 架构总览

本文档基于 `Entangled` 子模块与其在 NovAIC Gateway 和 Tauri 客户端（Rust/React）的具体集成，提供细粒度的架构全景视图。
历史上独立的 `entangled-service` 已被彻底消除，现今的 Entangled 是一套 **引擎级库 (Library) + 可选应用壳 (App Shell)**。

---

## 1. 核心定位与三层架构 (Python Server 侧)

Entangled 于 2026 年 4 月完成终极统一，Python 服务端侧遵循严格的“**协议、存储、应用**”三层剥离：

| 层级 | 路径 | 职责定位 | 核心模块 / 特性 |
|:---|:---|:---|:---|
| **层 1：Protocol** | `entangled.server` | **纯协议验证与 PubSub 分发** | 不关心任何 DB：`EntityStoreProtocol(ABC)` 鸭子类型约束、`ws_handler` 协商（含 `syncContractVersion`）、`notifier` 更新下发。 |
| **层 2：Storage** | `entangled.sql` | **SQL 数据底座与表意层** | `SqlEntityStore` 继承字协议：提供全套 CRUD 闭环。具备自己的 `Database` (WAL-mode SQLite wrapper)、`Locks`（并发控制）、`EntityDef` 与 `FieldDef` 解析。Gateway 直接继承使用此类。 |
| **层 3：App Shell** | `entangled.app` | **业务壳与独立启动入口** | **取代了过时的 entangled-service**。零代码生成 FastAPI 应用（`factory.py`），提供自带 JWT Auth（`auth.py`）、REST API (`crud.py`) 和 WebSocket 挂载 (`ws.py`)。 |

直接通过 `python -m entangled.app.main`（或同级 CLI 可执行指令）即可快速唤醒独立同步服务。

---

## 2. Entangled.SQL 存储引擎详解

Entangled 的数据引擎针对高并发、多读轻写场景做了深度改造：

- **Database / Logs** (`database.py`, `locks.py`):
    - 基于原生 `sqlite3` 提供 async thread-pool 包装。
    - **隔离锁定机制**：采用两级锁。写操作在独立线程锁定文件，以安全执行 `VACUUM` 乃至并发防碰撞。
- **配置化表结构** (`entity_def.py`):
    - 完全通过 `EntityDef` / `FieldDef` class-level property 自动建表（支持 `id`, `user_id`, `created_at` 以及灵活的 `json` 约束）。
    - 一次写入 = 一次通知，无自动级联。
- **Store Abstraction** (`entity_store.py`):
    - 代理全部读写动作。提供 `sync_type`(`list` / `stream`) 与 `sync_limit`。提供抽象游标（Cursor）为 `list_stream` 同步历史消息（例如 Chat Messages）提供高性能 O(log N) 级获取。

---

## 3. 在 Business Service 的深层集成与落地

> **⚠️ 2026-04-16 更新**：Entangled 服务端的唯一 HTTP 消费者已从 Gateway 迁移至 **Business Service (:19998)**。
> Gateway 不再拥有 `GatewayEntityStore(SqlEntityStore)`，仅保留 `AuthEntityStore` 管理本地 auth 实体。

在 NovAIC 中，**`novaic-business` (Business Service)** 是 Entangled 服务端能力的唯一宿主节点：

### 3.1 Business 直连 Entangled HTTP
~~旧架构~~：Gateway 曾直接继承 `SqlEntityStore`，派生出 `GatewayEntityStore`。该类已不存在。

当前架构中，Business Service 通过 `EntangledServiceClient` 直连 Entangled HTTP API，所有业务实体 CRUD 统一经 Business `/internal/entities/*` 代理端点。其余服务（Device、Workers、Gateway）均通过 Business 间接访问 Entangled，不再直连。

### 3.2 WebSockets 打通与 Sync Contract
- **App WS 仍在 Gateway 上**：Gateway 在 `AppBridge WS` 数据通道（`gateway/api/app_client.py`）只承载信令、业务动作（如 interrupt、WebRTC Offer）和 Entangled endpoint discovery。
- 但所有实体 CRUD 写操作经 Gateway 鉴权后转发至 **Business Service `/internal/entities/*`**，由 Business 代理写入 Entangled。
- Entangled direct WS 首帧 `event=schema` 带 `syncContractVersion` 和 capabilities；App Rust 注册 schema 后供 TS bootstrap 使用。

### 3.3 状态级联与智能推送 (Entangled Notifier)
`gateway/entity/entangled_bridge.py`：承担着关联表初始化（解析所有 `EntityDef.parent` 拓扑）、启动自动同步版本与元信息的重任；
客户端不再需要繁琐的「我要订阅会话也要一并订阅它的所有日志」——服务端发现 `Cascade` 之后将主动连同 Parent 节点将其子关联的初始化事件推送到网关 WebSocket 下发池。

---

## 4. 客户端架构：Headless Rust Client / React Path C

抛弃了笨重且极易竞态的前端 IndexedDB 与 `@entangled/react` 厚绑定（Path B 时代），现进入完全以服务端及 Rust 缓存驱动的 **Path C Headless 模式**。

### 4.1 Rust SQLite 与 `entangled_cache.db`
- 数据真实主存不再是 JS 内存或者 Web IndexedDB。
- Tauri 后端使用纯 Rust（`sqlx` 驱动底层 SQLite 表结构），维护起本机的 `entangled_cache.db`。所有的流式同步（Stream Sync）历史变更通过 Tauri Event 通道下钻进入持久化文件库。
- 只有触发真实的视图变更才会通过 Rust 的 `entities_changed` Tauri 事件连同 `params` 通知前端，彻底剥离大量垃圾重新渲染。

### 4.2 动词缩减与服务端确认写入
前端由原先十几个 Hook 精简为仅使用极少数“意图分发”命令：
1. **读 (Render)**：通过 `hooks.tsx` (例如 `createListStore`, `createFormStore`) 从内存读。
2. **写 (Mutation / Action)**：派发到 `entangled_method` / `entangledMethod`，经服务端 action hook 或实体写入确认后，再由 sync 帧回写本地缓存。当前活代码是 pessimistic-first：客户端缓存不维护离线写队列。
3. **路由 (Subscription Routing)**：采用 **Slot-based NavState (v2)**（`src/data/entangled/nav.ts` -> Rust `nav.rs`）。

### 4.3 插槽 (Slot) 并发路由模型
- 旧架构存在不同 Tab 的 Subscriptions 互相践踏的问题。
- 如今 Tauri 端 `NavState` 由 `HashMap<slot_name, Vec<SubSpec>>` 独立保护各个组件（比如并行悬浮框、侧边工具栏）。
- 主界面的 `deriveDesiredMainNav` 挂载 `conversation` 路由时将批量发起该上下文的所有业务请求：如 `messages(agentId), execution-logs(agentId), agent-binding(agentId)`。切换视图时 Rust 会自行判断 `refcount` 实现 `unsubscribe`。

---

## 5. 存储对齐：Clear Cache (清理本地缓存) 的排障细节

在桌面的 `Settings -> Clear Cache`，对应的不仅是前端的 localStorage `clearLocalDb(userId)`；而是发起了 `invoke('entity_cache_clear')` 触达底层 Rust。
当前 App 侧 `entangled_cache.db` 只有 `entity_meta` / `entity_items`（以及索引），`Cache::clear_all()` 清理这些 read-model 行并执行 `VACUUM`。历史版本曾有 `pending_ops`，现在 Rust 初始化会主动 `DROP TABLE IF EXISTS pending_ops`，不要再把它当作活跃排障对象。

排查客户端缓存时可直接看：

```bash
sqlite3 "$HOME/Library/Application Support/com.novaic.app/entangled_cache.db" ".tables"
sqlite3 "$HOME/Library/Application Support/com.novaic.app/entangled_cache.db" \
  "SELECT entity, version, subscribed FROM entity_meta ORDER BY entity"
sqlite3 "$HOME/Library/Application Support/com.novaic.app/tool_results.db" ".tables"
```

`log-payloads` 是 action / lazy-fetch 表面，不是默认订阅的热 stream。执行日志热路径订阅 `execution-logs`，大 payload 需要按需 action 读取或通过 TRS / LLM Factory join key 下钻。

---

## 6. 开发者速查清单

| 如果你要改... | 去哪个文件里找... |
|:---|:---|
| 新增一个服务端表的字段 / 约束 | `Entangled/packages/server-python/entangled/sql/entity_def.py` |
| 配置特定表的拦截验证钩子 | `novaic-business/main_business.py`（Hook 注册）/ `novaic-business/business/internal/entity.py`（entity proxy） |
| 修复 Rust 存储的慢查询或类型 | `Entangled/packages/client-rust/src/cache.rs` 或 `store.rs` |
| 调整 React 侧对数据库的重新渲染 | `novaic-app/src/data/entangled/hooks.tsx` |
| 改变页面切换到底需不需要重新请求 DB | `novaic-app/src-tauri/src/commands/nav.rs` 与前端 `nav.ts` (管控路由插槽与 Refcount) |
| Entangled App 的独立接口 / WebSocket 登入 | `Entangled/packages/server-python/entangled/app/ws.py` 与 `auth.py` |
