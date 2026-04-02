# Entangled 架构升级计划（详细版）

> 本文档基于对 NovAIC 当前 Entangled 栈的评审（前端 `data/entangled`、`Entangled/packages/client-rust`、`novaic-gateway/gateway/entity`、Python `entangled/server`）整理，目标是把**隐性契约显性化**、**热路径非阻塞**、**单一真源与可扩展拓扑**分阶段落地。  
> 与 [HANDOVER.md](../HANDOVER.md) 中的 Path C（Rust 管订阅、React 失效驱动读）**兼容**，不预设推翻该模型。

---

## 一、背景与问题域

### 1.1 当前分层（摘要）

| 层 | 路径 | 职责 |
|----|------|------|
| 前端胶水 | `novaic-app/src/data/entangled/` | React Query、dispatch、nav、schema 辅助 |
| Tauri | `novaic-app/src-tauri/`（app_bridge、nav、entangled commands） | WS、SQLite 缓存、订阅生命周期 |
| 本地引擎 | `Entangled/packages/client-rust/` | cache、push、订阅 registry |
| 服务端 | `novaic-gateway/gateway/entity/` + `Entangled/packages/server-python/` | EntityStore、subscribe、notifier、sync |

### 1.2 主要架构张力（为何要做本计划）

- **协议**：delta/schema 对主键字段（`idField`）表达不完整，客户端依赖回退表，易与 `defs.py` 漂移。
- **契约**：服务端 params 序列化与 Rust `CacheKey` 哈希若不一致，会漏同步或脏分区。
- **运行时**：同步 SQLite 压在 asyncio / WS 读路径上，尾延迟与卡顿风险。
- **演进**：`defs.py` 体量与 TS/Rust 手工对齐成本高；多 worker 时进程内 notifier 不共享。
- **宿主**：前端模块单例（listener、nav 队列）与 React/HMR/测试边界模糊；OTA 与 Tauri 能力边界需文档化。

---

## 二、总原则与成功指标

### 2.1 原则

1. **不推翻 Path C**：订阅生命周期仍以 Rust `nav_changed` 为准；数据写仍经 `dispatch` / Rust optimistic。
2. **向后兼容优先**：协议增字段、老客户端忽略新字段；必要时握手协商 `clientCapabilities`。
3. **每阶段可测**：合并前必须具备验收项或检查清单勾选项。
4. **先止血再重构**：阶段 0 完成后再大规模动协议与线程模型，减少变量。

### 2.2 成功指标（建议季度复盘）

| 指标 | 说明 |
|------|------|
| 正确性 | 清缓存 + load_more + 非 `id` 主键实体无「静默空表」类回归 |
| 性能 | Gateway / 桌面端在约定压测模型下 P95 延迟或 CPU 较基线有记录到的改善 |
| 工程效率 | 新增实体以 defs 为源，codegen 覆盖 TS/Rust 主键与 keyParams，CI 防漂移 |
| 安全 | OTA 能力与敏感 Tauri command 清单经评审并落在本文档检查项 |

---

## 三、阶段总览与依赖

```text
阶段 0（止血） ──► 阶段 1（协议/契约） ──► 阶段 2（运行时） ──► 阶段 3（codegen/拆分）
                                                      │
阶段 5（宿主/安全） ════════════════════════════════ 可并行 ═══►
阶段 4（横向扩展） ──► 仅在有明确容量/多实例需求时启动
```

---

## 四、阶段 0：契约漏洞止血

**执行记录（2026-04-01）**：已完成 0.1–0.4 代码与约定文档。**0.2**：Rust 侧补充 `cache::item_id_tests`（`model_id` 主键、`get_list_with_pending` 与 `default_id_field_for_entity("models")` 联调）；**完整联调 / 灰度**仍建议合并前人工点检。

**目标**：消除同产品内「一半路径用 `id`、一半用 `id_field`」的实现不一致，降低误判为「架构问题」的噪声。

### 4.1 工作项（详细）

| ID | 内容 | 交付物 |
|----|------|--------|
| 0.1 | `entangled_load_more` 中 `prepend_older` 与 `entity_prepend_page` 主键策略一致；若 WS 响应可带 `idField` 则优先使用 | PR：`commands/entangled.rs` 等 |
| 0.2 | 审计 `cache.rs` 内 optimistic / `get_list_with_pending` 等是否写死 `"id"`；改为按实体主键或统一 helper | PR + 测试或手工用例表 |
| 0.3 | 审计 Python：`handle_load_more`、create notify、游标等写死 `"id"` 的路径，改为 `defn.id_field` | PR：server-python / gateway |
| 0.4 | 文档：主键字段在 defs → Rust 回退 → prepend/load_more → notify 全链路一致 | 本节或 `docs/entangled-pk-conventions.md`（可选另文） |

### 4.2 阶段 0 检查清单

- [x] **0.1** `grep` 全仓库 `prepend_older` / `load_more` 路径无孤立硬编码 `"id"`（`entangled_load_more` 与 `entity_prepend_page` 均使用 `default_id_field_for_entity`）
- [x] **0.2** 自动：`entangled-client` `cache::item_id_tests`（`model_id` + pending create）；**agent_id** 类建议仍做一次手工 smoke
- [x] **0.3** Python：`store.create` 通知、`sync._stream_head_n_sync`、`ws_handler` load_more 已按 `id_field` / `getattr(defn,'id_field','id')` 处理
- [x] **0.4** 已添加 [entangled-pk-conventions.md](./entangled-pk-conventions.md)
- [x] `cargo check`（`novaic-app/src-tauri`）与 `cargo test`（`entangled-client`）通过
- [ ] 与当前 Gateway 联调：消息流 / 模型列表 load_more 无空窗

### 4.3 里程碑 M0

- [ ] 上述检查清单全部勾选
- [ ] 内测或灰度无新增「清缓存后某列表恒空」工单

---

## 五、阶段 1：同步协议与跨层契约（显性化）

**执行记录（2026-04-01）**：**1.1–1.6、1.5** 同前。**1.7**：协议 **§9 选定语义 B**（Rust `apply_snapshot` 先 `DELETE` 再写帧内行 = head 分区重置，prepend 不保留）；与 Gateway stream op-log gap → `head_n` 一致。**阶段 2**：见 §六执行记录。

**目标**：用文档 + 实现把「口头约定」变成可版本化的协议与测试向量。

### 5.1 工作项（详细）

| ID | 内容 | 交付物 |
|----|------|--------|
| 1.1 | 编写 **Sync Envelope v1**：字段表（`entity`、`params`、`mode`、`version`、`idField`、delta 的 `baseVersion`、`ops` 等）、必填/可选、向后兼容规则 | `docs/entangled-sync-protocol-v1.md` |
| 1.2 | Notifier 下发的 **delta 帧附带 `idField`**（与 subscribe 首帧一致） | Python PR |
| 1.3 | Schema 推送（`to_schema_dict` 或 NovAIC `get_schema`）增加 **`idField`**（可选，与 1.1 一致） | Python + 可选 TS 消费 |
| 1.4 | **Params canonical 规范**：键排序、标量类型、空对象与 null；提供 **JSON 测试向量** | `scripts/` 或 `tests/` + 文档节 |
| 1.5 | 实现 **Python state key 与 Rust `hash_params` 对同一向量输出一致**（或文档说明刻意差异并禁止该用法） | 双端测试 |
| 1.6 | **`up_to_date` 语义**：是否更新本地 `entity_meta.version`；实现与 1.1 一致 | Rust + 文档 |
| 1.7 | **Stream 缺口恢复**：选定语义 A（仅替换 head、保留更老页）或 B（整 key 重置并带原因码）；实现 + 1.1 更新 | Rust + Python |

### 5.2 阶段 1 检查清单

- [x] **1.1** 已添加 [entangled-sync-protocol-v1.md](./entangled-sync-protocol-v1.md)（评审签字仍建议补在文档修订表）
- [x] **1.2** delta / 级联帧含 `idField`；客户端仍兼容缺字段（`process_sync` 回退）
- [x] **1.3** `to_schema_dict()` 含 `idField`（TS 消费可选）
- [x] **1.4** [entangled-params-canonical.md](./entangled-params-canonical.md)（**1.5** 测试向量仍待办）
- [x] **1.5** Python `_state_key` 向量测试（`test_params_state_key.py`）；Rust `hash_params` 性质测试（无跨语言 u64 golden，见 [entangled-params-canonical.md](./entangled-params-canonical.md)）
- [x] **1.6** `up_to_date` 调用 `align_version_from_server` 写回 `entity_meta.version`
- [x] **1.7** v1 = 语义 B；协议 §9 与 `apply_snapshot` 行为一致
- [ ] 老客户端连接新服务端：冒烟通过（向后兼容）— **发布前人工勾选**
- [x] 新客户端连接旧服务端：缺 `idField` 时用 `default_id_field_for_entity`（见协议 §4）

### 5.3 里程碑 M1

- [ ] 阶段 1 检查清单：**老客户端冒烟**仍待人工勾选（§5.2）
- [ ] 发布说明含「协议/客户端最低版本」说明（若需要）

---

## 六、阶段 2：运行时 — SQLite 退出热路径脊梁

**执行记录（2026-04-01）**：**2.1**：有界队列 + `run_entangled_sync_worker` + `spawn_blocking`。**2.3**：`cache.rs` 全路径 `pool.get()` 失败 → `tracing::error`（`target=entangled_cache`，`op`）+ 安全返回；`apply_snapshot` / `apply_delta` / `prepend_older` 事务开启失败亦记录。**2.4**：慢 sync + 队列饱和日志。**2.5**：[entangled-load-test.md](./entangled-load-test.md)。**2.2**：`ws_handler`：`subscribe`（snapshot + `to_thread` + 校正）、`load_more`、`request`/`_dispatch`（除 `action`）均 **`asyncio.to_thread`**；测试见 `tests/test_sync_snapshot.py`。

**目标**：WS 与 UI 不因同步 SQLite 长时间占用事件循环/读循环而卡顿；背压与失败可观测。

### 6.1 工作项（详细）

| ID | 内容 | 交付物 |
|----|------|--------|
| 2.1 | 桌面端：`IncomingMessage::Sync` **入有界队列**，**专用线程或 `spawn_blocking`** 执行 `process_sync` | Rust PR：`app_bridge.rs` 等 |
| 2.2 | Gateway：DB 访问从 async handler 逐步迁到 **`asyncio.to_thread`** 或 worker 池 | Python PR + 配置 |
| 2.3 | Rust `cache`：`pool.get()` 等失败路径 **可恢复错误 + 日志**，减少裸 `unwrap` | Rust PR |
| 2.4 | 指标/日志：sync **处理耗时**、**队列深度**、队列满时**丢弃或反压**策略 | 运维文档 + 代码 |
| 2.5 | **压测脚本或步骤**记录（前后对比） | 附录或 `docs/entangled-load-test.md` |

### 6.2 阶段 2 检查清单

- [x] **2.1** 背压路径与 heartbeat 交错（`try_send` 满时 `select!`）；SLA 阈值见 [entangled-load-test.md](./entangled-load-test.md) 基线表（人工填数）
- [x] **2.1** 无死锁设计：单 `mpsc` sender、连接结束 drop sender → worker 退出；未上 loom
- [ ] **2.2** 压测下事件循环阻塞前后对比 — **实现已上**；数值填入 [entangled-load-test.md](./entangled-load-test.md)
- [x] **2.3** 池耗尽/检出失败：打日志并返回空/默认，不 panic
- [x] **2.4** 慢 `process_sync` 与队列饱和可按 `entity` / `conn_seq` 检索（精确队列深度指标仍可选）
- [x] **2.5** [entangled-load-test.md](./entangled-load-test.md)

### 6.3 里程碑 M2

- [ ] 阶段 2 检查清单 **2.2** 仍待压测表填数后勾选
- [ ] 发布说明含性能与行为变更（若有）

---

## 七、阶段 3：领域模型与 codegen（单一真源）

**执行记录（2026-04-01 续 — Gateway）**：**3.1** 已按域拆分为 `gateway/entity/defs_lazy.py`、`defs_models.py`、`defs_stream.py`、`defs_agent_forms.py`、`defs_users.py`；`defs.py` 保留 `ALL_ENTITIES`、`register_all_entities` 及既有 `from gateway.entity.defs import …` 兼容。**3.2** Gateway 侧 `scripts/export_entity_id_fields.py` + `generated_entity_id_fields.json` + CI/smoke `--check` 已接入；TS/Rust 生成消费仍属 **3.3 / 3.4**。**C.2（种子）**：业务侧实体变更推送统一经 `gateway.entity.sync_push.notify_entity_change` → `SyncPushPort`，不再直 `from entangled.server.notifier import notify_entity_change`（`register_client` / `set_store` 等仍用 notifier）。

**执行记录（2026-04-01 — Rust + 前端）**：**3.3** `entangled-client` 增加 `build.rs`，从 `generated_entity_id_fields.json`（或 crate 内 `entity_id_fields.json`）生成 `default_id_field_for_entity`；单测校验与嵌入 JSON 一致。**3.4** `novaic-app` 引入 `generated_entity_id_fields.json`、`defaultIdFieldForEntity`、`buildEntangledQueryKey*`，`hooks` 与 `entities_changed` 共用排序规则；仓库根 `scripts/sync_entity_id_fields.sh` + Tauri CI `cmp` 三份 JSON 防漂移。

**目标**：`defs.py` 可维护；TS/Rust 主键与 keyParams 少手工抄。

### 7.1 工作项（详细）

| ID | 内容 | 交付物 |
|----|------|--------|
| 3.1 | 按域拆分 `defs.py`（agents、devices、models、messages…），聚合入口不变 | Python 重构 |
| 3.2 | 扩展或新增脚本：从 `ALL_ENTITIES` 生成 **实体→idField**（TS 常量 + Rust include / build.rs） | `scripts/` + CI `--check` |
| 3.3 | Rust `default_id_field_for_entity` 以生成结果为准，手写 match 仅保留 `_ => "id"` | Rust PR |
| 3.4 | 前端 `queryKey` / invalidation 与 **keyParams + canonical params** 共用生成或单一 helper | TS PR |
| 3.5 | 与阶段 **1.4** 对齐：canonical 规则只有一处「权威描述」 | 文档交叉链接 |

### 7.2 阶段 3 检查清单

- [x] **3.1** Gateway：`pytest` 全绿；`defs` 拆模块、聚合入口不变（合并前建议再跑一轮完整网关冒烟）
- [x] **3.2** Gateway：`export_entity_id_fields.py --check` + Tauri CI 三文件 `cmp`；变更 defs 后须跑 `sync_entity_id_fields.sh`
- [x] **3.3** `entangled-client`：`build.rs` + `entity_id_fields.json` + `cargo test` 对齐 JSON
- [x] **3.4** `buildEntangledQueryKey*` 与 `startSyncListener` 同源规则；全量多键实体建议仍做一次手工冒烟
- [ ] 新增实体演练：从 defs 到 UI 类型更新 ≤1 个 PR（演练记录勾选）

### 7.3 里程碑 M3

- [ ] 阶段 3 检查清单全部勾选
- [ ] 团队 onboarding 文档指向 codegen 命令

---

## 八、阶段 4：横向扩展（按需）

**前提**：单机连接数/CPU 成为瓶颈，或必须多 worker / 多机房。

### 8.1 工作项（详细）

| ID | 内容 | 交付物 |
|----|------|--------|
| 4.1 | 梳理 registry：`client_id` / `user_id` 与推送过滤关系；安全评审 | 设计文档 |
| 4.2 | 引入 **Redis 或 NATS** 广播变更事件；worker 仅推本机 WS | 基础设施 + 代码 |
| 4.3 | 粘性会话或 **user 级 channel** 策略（Nginx、网关路由） | 运维 Runbook |
| 4.4 | Subscribe 级联：**批量读库**、合并 sync 帧（可与 4.2 分步） | Python PR |

### 8.2 阶段 4 检查清单

- [ ] **4.1** 多租户误推送场景有 threat model 与结论（即使结论为「当前单用户单连接故风险低」）
- [ ] **4.2** 双 worker 下功能与粘性策略验证通过
- [ ] **4.3** Runbook 含故障切换与回滚
- [ ] **4.4** subscribe P99 有前后数据（若实施）

### 8.3 里程碑 M4

- [ ] 阶段 4 检查清单全部勾选
- [ ] 容量规划更新

---

## 九、阶段 5：前端宿主抽象与安全边界

**目标**：测试/HMR 可预期；OTA WebView 与敏感能力分离。

### 9.1 工作项（详细）

| ID | 内容 | 交付物 |
|----|------|--------|
| 5.1 | **EntangledHost**（Context）：`onEntitiesChanged`、`enqueueNav`、可选 `invoke` 包装 | TS PR |
| 5.2 | Tauri **capabilities**：敏感 command 从 OTA 集剔除或二次校验 | `capabilities/*.toml` + 说明 |
| 5.3 | 替换脆弱依赖：`JSON.stringify(params)` → **稳定序列化 helper** | TS PR |
| 5.4 | `dispatch` 测试注入缝（可选）：wrapper 或 DI | TS PR + 测试示例 |

### 9.2 阶段 5 检查清单

- [ ] **5.1** Storybook 或单元测试可 mock Host，不启 Tauri
- [ ] **5.2** 安全评审 checklist 完成（见下文「主检查清单 — 安全」）
- [ ] **5.3** 相关 hooks 依赖数组稳定，无隐式因 key 序导致的漏刷新
- [ ] **5.4**（若做）至少一个 dispatch 单测不 mock 全局 `window`

### 9.3 里程碑 M5

- [ ] 阶段 5 检查清单全部勾选

---

## 十、主检查清单（发布前总表）

在任一「里程碑」对外发布前，建议复核以下条目（与阶段清单互补）。

### 10.1 协议与数据

- [ ] Sync 文档版本号与实现一致（见 `entangled-sync-protocol-v1.md` 若已创建）
- [ ] 非 `id` 主键实体全链路清单已更新（defs、Rust、Python、load_more）
- [ ] Params canonical 测试向量在 CI 中通过

### 10.2 运行时与可靠性

- [x] 桌面端 sync：`spawn_blocking` + 有界队列 + 背压（见 `app_bridge.rs`）
- [x] Gateway：`subscribe` / `load_more` 热路径已 `to_thread`（对比数据见 [entangled-load-test.md](./entangled-load-test.md) 表）
- [x] 队列满策略：背压 + 日志（`entangled sync queue full`）

### 10.3 工程与可维护性

- [ ] codegen / `--check` 已接入 CI
- [ ] `defs` 拆分后 import 循环与 lazy action 无回归

### 10.4 安全

- [ ] OTA 使用的 capability 列表与「敏感 command」列表已对照
- [ ] 伪造 sync / 清缓存等能力不在不可信 WebView 暴露（或已有等价控制）
- [ ] 多实例场景下推送隔离结论已记录（若已部署阶段 4）

### 10.5 运维与发布

- [ ] CHANGELOG / 发布说明含：协议版本、客户端最低版本、回滚步骤
- [ ] 关键日志字段（如 `conn_seq`、`entity`）在排障文档中有说明

---

## 十一、工时粗估（人日，可并行压缩）

| 阶段 | 粗估（人日） | 说明 |
|------|----------------|------|
| 0 | 2.5–4 | 视 Python 审计面 |
| 1 | 6–9 | 含 stream 语义与双端测试 |
| 2 | 5–10 | 含压测与排障 |
| 3 | 5–8 | 拆分 defs 占大头 |
| 4 | 10–30+ | 视基础设施 |
| 5 | 4–8 | 可与 1–3 并行 |

---

## 十二、风险与回滚

| 风险 | 缓解 | 回滚 |
|------|------|------|
| 协议变更破坏老客户端 | 特性协商、双发字段、老客户端忽略 | 网关开关回旧帧格式 |
| 线程/队列引入竞态 | 单 writer、清晰 shutdown 顺序、压测 | 功能开关切回同步路径 |
| codegen 漂移 | CI `--check` | 回退生成文件与脚本 |
| 多 worker 粘性错误 | Runbook、灰度 | 回单 worker |

---

## 十三、修订历史

| 日期 | 作者 | 说明 |
|------|------|------|
| 2026-04-01 | — | 初版：详细计划 + 分阶段与主检查清单 |
| 2026-04-01 | — | 阶段 0 部分落地：Rust `id_field` 模块、`get_list_with_pending`、Python sync/store/ws_handler、PK 约定文档 |
| 2026-04-01 | — | 阶段 1 部分落地：协议 v1 文档、notifier delta `idField`、schema `idField`、`up_to_date` 版本对齐、params 约定文档、pytest |
| 2026-04-01 | — | 阶段 2.3 `pool` 错误路径、2.5 load-test 文档、1.7 语义 B、0.2 Rust 测试、`item_id` 用例 |
| 2026-04-01 | — | 阶段 2.2：`SyncStateSnapshot`、`asyncio.to_thread` subscribe + load_more、pytest `test_sync_snapshot` |
| 2026-04-01 | — | 阶段 2.2 续：`_dispatch` 同步实体 op 经 `to_thread`，`action` 仍 `await store.action` |

---

## 十四、相关文档

- [entangled-architecture-upgrade-design-complete.md](./entangled-architecture-upgrade-design-complete.md) — **完备目标架构 + ADR + 扩展分期**（在本文执行清单之上的总设计）
- [HANDOVER.md](../HANDOVER.md) — 项目交接与 Path C、nav、Entangled 现状
- [entangled-pk-conventions.md](./entangled-pk-conventions.md) — 主键字段全链路约定（阶段 0）
- [entangled-sync-protocol-v1.md](./entangled-sync-protocol-v1.md) — 同步协议 v1（阶段 1）
- [entangled-params-canonical.md](./entangled-params-canonical.md) — params 规范化（阶段 1.4）
- [entangled-load-test.md](./entangled-load-test.md) — 压测步骤与 2.2 说明（阶段 2.5）

---

## 十五、范围说明（「全部」与后续专项）

**本轮已收口**：阶段 **0（除联调勾选）**、**1（除老客户端冒烟签字）**、**2（除 2.2 压测数字）** 中与 Entangled 桌面 + Rust cache + Gateway `to_thread` + 协议文档直接相关的项。

**未在本仓库一次性完工（独立里程碑）**：

- **阶段 3**：`defs` 拆分、idField codegen、TS queryKey 生成 — 见 §七。
- **阶段 4**：多 worker / Redis — 见 §八。
- **阶段 5**：EntangledHost、capabilities 审计 — 见 §九。

以上保留原文工作项与检查清单，避免与「已交付的 0–2 子集」混淆。
