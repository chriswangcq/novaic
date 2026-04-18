# PR-14 Preflight Review（Entangled `message_outbox` + co-transaction insert）

| 字段 | 值 |
| --- | --- |
| Reviewer | senior |
| Verdict | **条件批准** — 补完 §A/§B/§C 3 个 blocker + §D/§E 2 个细节后直接 T1 |
| 亮点 | §1 正确 pushback 了 ticket 的错误架构假设（Business 跨进程无法同事务），定位 Entangled-side 唯一技术路径 |

---

## §A（BLOCKER）`outbox_trigger_types` 注入机制必须**选一个**，不能"or 更简单"

你 §3 最后给了两个方案但没决策：

1. Schema 驱动：`SqlEntityDef.outbox_trigger_types: Dict[str, str]`
2. Per-call 驱动：Business 调 `store.append()` 时传 `outbox_trigger_type=...`

**选方案 1（Schema 驱动）**，理由：

- 配置归一在 `schema_push.py` 的 `MESSAGES_DEF`，业务调用方无需记忆"哪种 type 要触发"
- 新增 trigger 类型只改一处 schema 定义
- 方案 2 意味着 5 个 `_store_add_message` 调用点都要维护"哪个 type 要传 outbox flag"的逻辑，会产生漂移

### 但方案 1 有个你没回答的子问题

`SqlEntityDef` 在 Entangled 侧定义，Business 通过**schema push 协议**把自己的 entity 定义注册过去。你必须先确认：

**schema push 的 wire format 是否能承载 `outbox_trigger_types` 这个新字段？**

- 如果 wire format 有开放的 `extensions: dict` 或 `meta: dict` 字段 → 可以直接塞进去，Entangled 反序列化时 `SqlEntityDef.from_dict(...)` 读出
- 如果 wire format 是固定 schema（Protobuf / Pydantic 强类型） → PR-14 必须**同时扩展协议**，在 Business 和 Entangled 两侧都加字段，schema 版本号 +1

**T1 开干前必须做一次调研**：
- 读 `novaic-business/business/schema_push.py` 看 push request body 怎么构造
- 读 Entangled 端的 `/v1/schema/register` handler 看它怎么反序列化
- 如果是后者，preflight 要把协议扩展的工作量也列进 §6 的 file:line 清单

给出结论后再开 T1，**不能"到时候看"**。

## §B（BLOCKER）`payload_json` schema 没定义完整，你 §5 的 code snippet 只塞了 `message_ids`，缺关键字段

subscriber（PR-15/16）要用 outbox 行重建 `DispatchAssembler.assemble_and_dispatch(...)` 的完整调用。只有 `message_ids` 显然不够——看 PR-11 现存的三个场景：

| TriggerType | Assembler 调用需要什么 | 来自 chat_messages 哪里 |
| --- | --- | --- |
| `USER_MESSAGE` | `agent_id`, `message_ids` | chat_messages.id + agent_id 字段 |
| `SUBAGENT_SEND` | `agent_id`, `subagent_id`, `message_ids` | `subagent_id` 在 chat_messages.metadata.target_subagent_id |
| `SPAWN_SUBAGENT` | `agent_id`, `subagent_id`, `message_ids`, `metadata.initial_context` | 全部在 chat_messages.metadata |

所以 `payload_json` 最少应该是：
```json
{
  "message_ids": ["<this msg id>"],
  "metadata": <copy of chat_messages.metadata or subset>,
  "subagent_id": "<from metadata if present, else null>"
}
```

preflight §5 必须明确定义 `payload_json` 的 schema（最好给出每个 TriggerType 的示例 payload），并说明从 `row` 的哪些字段如何取。否则 PR-15/16 subscriber 写到一半会发现字段不够要回头改 PR-14 的 schema。

### 特别注意 `metadata` 可能是 JSON 字符串

`chat_messages.metadata` 在表里是 TEXT 存的 JSON string（见 `_store_add_message` 里 `json_module.dumps(metadata or {})`）。Entangled 侧取 `row["metadata"]` 拿到的可能是 string，不是 dict。`payload_json` 构造时要先 `json.loads()` 再组装进去，否则你会得到 double-encoded JSON。这个细节写进 §5。

## §C（BLOCKER）Entangled 文件路径全是 `.../`，T1 之前必须解析

§6 表格里 `Entangled/.../sql/entity_store.py`、`Entangled/.../sql/entity_def.py`、`Entangled/.../app/state.py` 全是占位符。我在 workspace 里没直接找到 Entangled 源码（本仓 submodule 可能不包含），你先确认：

- Entangled 源码在 `novaic-entangled/`（submodule）还是外部仓库？
- `SqlEntityStore.append()` 文件的**真实完整路径**
- `SqlEntityDef` 的定义文件**真实完整路径**
- 如果 Entangled 是外部 submodule，本 PR 需要在 submodule 里建 branch/分支、主仓 bump pointer，commit 拆分也更复杂

preflight §6 的 `.../` 全部改成真实路径，`git log -- <path>` 确认你能访问并修改。

## §D（必做）inline `_dispatch_trigger` vs outbox subscriber 的双发风险，现在就要下决定

你 §10 acknowledge 了这个 risk 但没给方案。虽然 PR-14 本身只写不消费，不会立刻双发，但**PR-15/16 启用 subscriber 的那一刻**这个问题会同时爆发。不能留给未来"到时候再说"。

### 现状
- PR-11 `_dispatch_trigger` 调 `assembler.assemble_and_dispatch(...)` **没传 `idempotency_key`**
- Queue `session_repo.py:143` fallback 到 `f"session-{session_key}-{scope_id}"`，是 scope 生成的非稳定键
- 未来 subscriber 如果用 `idempotency_key=f"msg:{msg_id}"`，两条路径的 key 空间不重合 → Queue 看成两次独立的 dispatch → **会起两个 session 处理同一条消息**

### 解决方案

**在 PR-14 里做一件小事**：把 `_dispatch_trigger` 的 `assembler.assemble_and_dispatch` 调用补上 `idempotency_key=f"msg:{msg_id}"`，并约定 PR-15/16 subscriber **复用同样的 key 空间**。

这样即使 PR-15/16 启用 subscriber 后两条路径并行，Queue 的 idempotency ledger 会把第二个看成 `deduped`，不会起双 session。

这个 fix 是 PR-11 retroactive 性质。commit 拆独立一个 `fix(business): pass stable idempotency_key in _dispatch_trigger (PR-11 retroactive)`，放在 `novaic-business` submodule 里。

preflight §4 或 §7 增加一节「§8 幂等键对齐」说明这个约定，同时在 ticket 的"备注"里写明 "outbox subscriber 必须用 `idempotency_key=f\"msg:{message_id}\"`"，为 PR-15 preflight 打桩。

## §E（决策）metrics 策略——delete or defer

你 §7 说"不做 metrics"，但 ticket 的"可观测性 Checklist" 明文要求 `outbox_enqueued_total` counter + `outbox_backlog_count` gauge + `log: outbox_enqueue ...`。**不能默认跳过**。

两种合法做法，选一个：

1. **实现 log**（cheap），**defer 两个 metric 到 PR-32 backlog**。结构化 log `event=outbox_enqueue message_id=... agent=... trigger=...` 在 `append()` 追加 outbox 时打一行。Metric counter/gauge 登记到 `PR-32-metrics-prometheus-integration.md` ticket backlog 清单，留 prometheus_client 统一治理时再做。
2. **全部实现**。但 Entangled 的 metrics pipeline 如果目前不存在，等于要额外搭一套——scope 爆炸。

**推荐方案 1**，preflight §7 明文改成 "log 实现、2 个 metrics defer 到 PR-32 backlog"，并在 `docs/roadmap/tickets/PR-32-metrics-prometheus-integration.md` 加两条条目。

## §F（信息性，不 block）

### F.1 Schema 版本与未来迁移
你推荐 `_ensure_outbox_schema()` + `CREATE TABLE IF NOT EXISTS` 是对的起步。但 Entangled 有没有**版本化迁移系统**（类似 Alembic）？如果没有：

- 现在 `CREATE TABLE IF NOT EXISTS` OK
- 未来要加列或加索引，只能靠 `ALTER TABLE IF ... ADD COLUMN ...`（SQLite 支持但受限）
- 无法删列、无法改列类型

这是可接受的代价，但 preflight 应在 §10 补一条 TD：**Entangled outbox schema 无版本化迁移工具，后续只能靠 `ALTER TABLE` 增量演进**。登记到 `technical-debt.md`。

### F.2 `ON CONFLICT(message_id) DO NOTHING` 语义
`message_id UNIQUE` + `DO NOTHING` 意味着：同一 message_id 第二次 append（重试？重复写？）→ 静默忽略。这是正确的（outbox 是 append-only changefeed），但要在 ticket 或 schema 注释里写明这层语义，否则以后有人看到 `DO NOTHING` 会困惑。

### F.3 删除保留期
ticket §保留期 约定 `delivered_at IS NOT NULL` 超过 7 天可清理，维护脚本 PR-16 附带。PR-14 **只写 schema 和 insert**，这一条没你事。但 preflight §7 明文 acknowledge 一下"cleanup 是 PR-16 scope"。

---

## 返工 Checklist

- [ ] §A 确认 schema push 协议能否承载 `outbox_trigger_types`；选择方案 1 并把协议扩展（如需要）列进 §6 file:line
- [ ] §B 给出 `payload_json` 的完整 schema（每个 TriggerType 一个示例）+ 处理 `metadata` 是 JSON string 这个陷阱
- [ ] §C 把 §6 的 `Entangled/...` 占位符全部解析成真实路径
- [ ] §D 决定 `_dispatch_trigger` 补 `idempotency_key=f"msg:{msg_id}"` 作为 PR-11 retroactive fix；在 preflight §8 写明 key 空间约定
- [ ] §E metrics 选方案 1：实现 log、defer 两个 metric 到 PR-32 backlog、在 PR-32 ticket 里加条目
- [ ] §F.1 Entangled schema 无版本化迁移工具登记 TD

修完直接 T1，不用再 review 一轮。

**一个额外提醒**：PR-14 是 Phase 2 第一张票，也是 PR-15/16/17/21 的 block。commit 拆分要特别清晰（schema commit + co-transaction commit + retroactive fix commit + docs commit，至少 4 个独立 commit，跨 submodule 的话还要更多）。按 PR-13 那套严格三段式或四段式走。
