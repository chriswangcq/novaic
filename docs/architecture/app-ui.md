# 客户端前端架构

> 与当前 `novaic-app` 一致；对应原 **`HANDOVER.md` §十一**。分层总览另见子模块 **`novaic-app/FRONTEND_ARCHITECTURE.md`**。

## 三层（Render / Business / DB）

### 启动与登出

1. **登录**：`auth.ts` → `pushToken()` → `invoke(update_cloud_token)` → `agentService.initialize()`
2. **恢复 Agent**：`prefsRepo.getSelectedAgent()` 或 localStorage
3. **选择 Agent**：store + prefs → `switchAgent(agentId)`，并行 load 模型（消息/日志为 Entangled stream 订阅）
4. **登出**：`getSyncService().disconnect()` + `resetServices()` 清空单例

### DB 层（Entangled 为单一事实来源）

- **IndexedDB 业务主存（messageRepo/logRepo）已移除**，改为 Entangled Stream Store（Rust SQLite 缓存 + Server Push）。
- 数据流：Subscribe → Server sync → Rust 缓存 → **`entities_changed`** → React。
- **`entities_changed` 载荷**：Rust（`Entangled/packages/client-rust/src/push.rs`）在 `EntityChanged` 中带 **`params`**（与订阅 key 一致），供 `syncListener` 按带参 `queryKey` 失效。
- **订阅 refcount**：`subscriptionSchema.acquireSubscribe` 在首次 `subscribe` 成功后再计数；AppBridge 重连时 **wire-only** `subscribe`（`entangledBootstrap`）避免双计数。
- **聊天主面板**：`ChatPanel` 唯一调用 `useMessages` / `useLogs`，子组件经 **props** 注入，避免同一 agent **重复订阅** stream。
- **清空本地缓存**：`clearLocalDb` → `invoke('entity_cache_clear')` → `Cache::clear_all()`。当前 Rust cache 是 read-model：`entity_meta` / `entity_items`；历史 `pending_ops` 表已废弃，初始化时会被 `DROP TABLE IF EXISTS pending_ops` 清掉。

**Business 层**：`messagesStore` / `logsStore`、`syncService`、`agentService`、`modelService`；Zustand `store.ts`。  
**AgentToolsTab**：`useSettings()` + Entangled 列表与 TanStack Query，不用 IndexedDB 业务表作主存。

## 关键设计决策

- **`getCachedUser()`** 不可直接放进 `useEffect` 依赖（每次新对象）→ 提取 **`userId`** 字符串。
- **currentAgentId 隔离**：Chats / Agents / Skills 状态分区。
- **MessageList**：`flex-1 min-h-0`（非 `h-full`）。

## 前端文件速查

| 需求 | 文件 |
|------|------|
| 远程桌面 | `useWebRtc.ts`、`WebRtcScrcpyView.tsx` |
| 操控台 | `DeviceConsole.tsx`、`ConsoleToolbar.tsx`、`useRemoteInput.ts` |
| 浮窗 | `DeviceFloatingPanel.tsx` → `FLOATING_PANEL_LAYOUT` |
| 模型 | `SettingsModal.tsx` → AgentToolsTab |
| 发消息 | `ChatInput.tsx`、`messagesStore` / `useMessages` |
| 执行日志 | `ExecutionLog.tsx`、`LogCapsule.tsx`、`ChatPanel.tsx` |
| Gateway 类型 | `src/services/api.ts`（数据写优先 `entangledMethod`） |
| 布局 | `LayoutContainer.tsx`、`PrimaryNav.tsx`、`App.tsx` |
| Gateway 配置 | `novaic-gateway/gateway/api/internal/config.py` |
| VM 准备 | `gateway/api/vm.py`、`vmcontrol/.../vm_prep.rs` |
| Skills UI | `Settings/SkillsPage.tsx`、`useSkills.ts`、`skillsService.ts` |
| Skills → LLM | `novaic-agent-runtime/.../system_prompt.py`；匹配 `novaic-gateway/.../skill.py` |

## Entangled Headless（Path C）

**理念**：React 展示 + 意图分发；Rust 引擎管订阅/缓存/重连。

- **读**：`useList` / `useForm` / `useStream`，`staleTime=Infinity`，仅 `entities_changed` 刷新。
- **写**：`dispatch` → `entangled_method_optimistic` / `entangled_method`。
- **路由**：`navChanged` → `nav_changed` → 路由表 → subscribe/unsubscribe。

**路由表（`src-tauri/src/commands/nav.rs`）**：

| 路由 | 订阅实体 |
|------|----------|
| `home` | agents, models, devices |
| `conversation` | agents, models, devices, messages(agentId), execution-logs(agentId), agent-tools(agentId), **agent-binding(agentId)** |
| `settings` | agents, models, devices, api-keys, skills, **agent-binding(agentId)**, agent-tools(agentId)（有 agentId 时） |
| `vm-context` | vm-users(deviceId)（组件级） |

**App.tsx 主槽（Sync Contract 1.4）**：单一 `useEffect` 调 `deriveDesiredMainNav` → `navChanged`，依赖 `isInitialized`、`settingsOpen`、`currentAgentId`；`enqueueMainNav` 与 Rust 主槽串行。启动时 `bootstrapEntangledEntities` 内可早发 `navChanged('home')` 与主 effect 共队列。

## Slot-based NavState v2

- **NavState**：per-**AppHandle** `manage()`，结构 `HashMap<slot, Vec<SubSpec>>`，避免多窗口/多 `VmPanel` 互踩。
- **示例**：`navChanged('conversation', { agentId })`；`useNavChanged('vm-context', { deviceId }, …, { slot: \`vm-${deviceId}\` })`；`navReleaseSlot(\`vm-${deviceId}\`)`。

**文件**：`nav.rs`、`nav.ts`（`navReleaseSlot`、`useNavChanged`）。

## Schema Contract

App 端不再维护 Python 生成的实体类型文件。运行时实体 schema 来自 Entangled
WS 首包；App 只保留自己实际消费的前端 contract 与单测：

- `src/data/entangled/client.ts`：解析 `{ entities, syncContractVersion }`
- `src/data/entities/entangledEntityContracts.ts`：App 消费实体的静态前端 contract
- `src/data/entities/entangledEntityContracts.test.ts`：对齐后端 contract 文件

## HTTP→Entangled 迁移（对照）

| 操作 | 旧 | 新 |
|------|----|----|
| api-keys CRUD | `gateway_post/patch/delete` | `entangledMethod('api-keys', 'create/update/delete')` |
| 用户设置 | `gateway_patch` `/api/config/settings` | `entangledMethod('user-preferences', 'upsert')` |
| bootstrap files | `gateway_get/post` agents | `entangledMethod('agent-tools', 'get_bootstrap/save_bootstrap')` |
| skills | 多个 `api.*` | `entangledMethod('skills', …)` |
| loadConfig | HTTP + prefsRepo | Entangled 缓存 `cacheGetList` 等 |
| sync 重连 invalidate | 手动 12 keys | 删除（Rust `resubscribe_all`） |

**Python**：`gateway/api/skill_actions.py`；`defs.py` 中 SKILLS / AGENT_TOOLS 的 actions。

**仍保留 HTTP 的典型场景**：文件 multipart 上传、健康检查/进程管理、Android 设备枚举、部分复杂日志查询、WebRTC 信令。

## Skills 调查报告（历史稿）

见 [**historical-doc-links.md**](../historical-doc-links.md)；产品级 Skill 商店见 [**roadmap/technical-debt.md**](../roadmap/technical-debt.md)。
