# PR-35  消除 chat_reply 静默 400（runtime-fill defaults，双层防护）

| 字段 | 值 |
| --- | --- |
| **Phase** | hotfix（带外 PR-33/34 体系之外的紧急止血） |
| **Milestone** | — |
| **承诺** | 架构原则：**系统简单** + **无静默失败** |
| **Status** | `[x]` prod 已上线 + 端到端验证；review/merge pending |
| **Depends on** | — |
| **Blocks** | — |
| **估时** | 0.5 d（已完成） |
| **Owner** | wangchaoqun |
| **PR 标题** | 见 §子 PR |

## 事件摘要

生产 `chat_reply` 工具 19 次静默失败（2026-04-16 ~ 04-19）。表象：用户发消息，Agent 不回复，但系统无报警；Queue task 仍 `complete`；日志里埋着 `logger.error("[tool] chat_reply failed: ...")` 没人看。

**根因**：`chat_messages.timestamp` 是 `NOT NULL` 无 SQL `DEFAULT`。Business 的内部 helper `_append_message` 显式填这个字段，但 Agent-runtime 走 **通用 CRUD 代理**（`gw.entity_create("messages", {...})`）—— 这条路径不知道 per-entity 语义，写入缺字段 → Entangled 400 → tool handler 把异常塞进 `tool_output` → Queue 标 `complete` → 用户侧沉默。

**这是"隐式契约 + 静默失败"双重违反**，正好撞 PR-33 第一原则。

## 修复方案（两层防护）

### A. 服务端兜底 —— `SqlEntityStore._apply_defaults`（**根因**）

在 Entangled `SqlEntityStore._sql_create / _sql_upsert / append` 三条写入热路径前插入 `_apply_defaults(defn, row)`：对每个 `nullable=False, default=<X>` 且 caller 未提供的字段，按 declaration 填值。

- `default="NOW"` → 新 helper `_iso_now_utc()`（ISO-8601 UTC + ms + `Z`，和 `common.utils.time.utc_now_iso` 格式对齐）
- 其他字面量 → 原样填入
- 显式 `None` **不**覆盖（caller intent 优先，SQL 层 loud-fail）

**Scope 收窄**：只对 `nullable=False` 且 `default is not None` 的字段生效。现有 `F.timestamp(auto=True)` 字段保持 `nullable=True`，行为不变。

### B1. 客户端显式填 —— `_exec_chat_reply`（**belt**）

```python
gw.entity_create("messages", {
    ...,
    "timestamp": utc_now_iso(),  # belt；A 是 suspenders
}, params={"agent_id": deps["agent_id"]})
```

即使 A 被误删或回滚，客户端仍能写入成功。**双层防护，单点失效不破**。

### B2. 静默失败消除 —— 结构化事件日志 + bake 监控

`handle_tool_execute` 的 `except` 块改为：

```
event=tool_call_failed tool=<n> agent=<id> subagent=<id> tool_call_id=<id> reason_type=<ExcClass> reason=<first-160-chars>
```

`scripts/canary/bake-snapshot.sh` 新增 `tool_err` 段：`grep event=tool_call_failed`，`total>0 → verdict=WARN(tool_failed=N)`，并给出 top-5 tool 拆分。下次同类静默失败**在 4h 内**会被 cron 快照打印出来。

### C. Schema 声明配合 A —— `MESSAGES_DEF.timestamp default="NOW"`

`novaic-business/business/schema_push.py` 单行改动，激活 A 的 runtime fill。

## 子 PR

| # | Repo | Branch | PR | 内容 |
|---|---|---|---|---|
| 1 | `Entangled` | `hotfix/runtime-fill-defaults` | [chriswangcq/Entangled#1](https://github.com/chriswangcq/Entangled/pull/1) | `_iso_now_utc` + `_apply_defaults` + 7 unit tests |
| 2 | `novaic-business` | `hotfix/messages-timestamp-default` | [chriswangcq/novaic-business#1](https://github.com/chriswangcq/novaic-business/pull/1) | `MESSAGES_DEF.timestamp default="NOW"` |
| 3 | `novaic-agent-runtime` | `hotfix/chat-reply-timestamp` | [chriswangcq/novaic-agent-runtime#1](https://github.com/chriswangcq/novaic-agent-runtime/pull/1) | `_exec_chat_reply` 填 timestamp + `event=tool_call_failed` + 6 unit tests |
| 4 | 主仓 | `refactor/no-tool-system-message` (已 push main-like) | — | submodule bumps + `bake-snapshot.sh` 的 `tool_err` 段 |

**Merge 顺序**：1 → 2（或并行），3 独立随时可 merge。必须 **1 和 2 同批部署**（否则 2 的 declaration 是 no-op）。

## 已部署时间线

| UTC | 北京 | 动作 |
|---|---|---|
| 2026-04-19 20:29Z | 04:29 | 推 #3（agent-runtime hotfix）+ `bake-snapshot.sh` 新版，`systemctl restart novaic.service` |
| 20:30Z | 04:30 | 验证：新代码 import + smoke poll 正常；`bake tool_err total=0 verdict=OK` |
| 20:38Z | 04:38 | 推 #1（Entangled）+ #2（business schema），py_compile + import + runtime assert 通过 |
| 20:38Z | 04:38 | 第二次 `systemctl restart novaic.service` |
| 20:39Z | 04:39 | **端到端 smoke**：`POST /v1/entities/messages` 不带 `timestamp` → `200` + 自动填入 `2026-04-19T20:39:49.443Z`，DB 确认落库后清理 |
| 20:40Z | 04:40 | bake snapshot 全绿：`outbox verdict=OK`, `tool_err verdict=OK`, `redline verdict=OK` |

选择 04:29 am（北京）窗口是出于流量最低谷 + PR-17 Phase 4 bake `outbox pending=0` 的准绿状态。

## 回滚路径（一条命令）

```bash
ssh root@api.gradievo.com '\
  cp /tmp/entity_store.py.bak.20260419T203803Z /opt/novaic/services/Entangled/packages/server-python/entangled/sql/entity_store.py && \
  cp /tmp/schema_push.py.bak.20260419T203803Z /opt/novaic/services/novaic-business/business/schema_push.py && \
  cp /tmp/tool_handlers.py.bak.20260419T202720Z /opt/novaic/services/novaic-agent-runtime/task_queue/handlers/tool_handlers.py && \
  systemctl restart novaic.service'
```

Pre-deploy 备份保留在 prod `/tmp/*.bak.20260419T*Z`。

## 对 PR-17 Canary 的影响

**零影响**。改动：

- Agent-runtime 只改 `_exec_chat_reply`（填字段）+ `handle_tool_execute`（日志格式），不触碰 dispatch 路径
- Entangled 改 `_apply_defaults`，add-only，对现有 caller 行为无变化（未声明 `default` 的字段不受影响）
- Business 只改 `MESSAGES_DEF.timestamp` 一行声明

重启后 bake 指标连续绿。Phase 4 bake 观察期不被打断。

## 架构判定（沉淀）

这个 bug 暴露了三个系统性问题，对应三条沉淀：

1. **"通用 CRUD 代理" + "隐式 NOT NULL 契约"** = 定时炸弹
   → **沉淀**：任何 `nullable=False` 的字段必须在 `SqlEntityDef` 声明 `default=...` 或 `auto=True`。未来 CI 检查点（P3 级别）。

2. **工具执行异常被吞** = 静默失败
   → **沉淀**：tool handler 的 `except` 必须输出 `event=tool_call_failed ...` 结构化 sentinel，且 ops 监控（bake / dashboards）强制消费。新 tool 加进 `_EXECUTORS` 时 code review 检查点。

3. **双写路径**（Business 内部 helper vs 通用 CRUD）行为不一致
   → **沉淀**：所有 per-entity 语义必须下沉到 schema（`default="NOW"` 或类似），不允许散落在 caller-side helper。

## Follow-ups

### ✅ 已落地

- [x] **时间字段 CI 断言** (2026-04-19) — `novaic-business/tests/test_schema_invariants.py` 3 tests：
  - `test_time_like_not_null_fields_declare_default` — 所有 `{timestamp, created_at, updated_at, scheduled_at, claimed_at, delivered_at, processed_at}` 名字的 NOT NULL 字段必须有 `default=...`，否则 fail。
  - `test_messages_timestamp_activates_runtime_fill` — 对 `chat_reply` 故障字段的 loud sentinel。
  - `test_execution_logs_timestamp_activates_runtime_fill` — 对下一颗同形炸弹的 loud sentinel。
- [x] **`EXECUTION_LOGS_DEF.timestamp default="NOW"`** (2026-04-19) — preemptive 修复；0 次发射但 reachable via 通用 CRUD 代理。Commit `6862b79` 在 business hotfix branch。
- [x] **`_check_required` — 非时间 NOT NULL 字段归属感** (2026-04-19) — `Entangled/packages/server-python/entangled/sql/entity_store.py` 在 `_apply_defaults` 之后遍历所有 `nullable=False, non-primary, default is None, missing from row` 字段，一次性列出并抛 `ValueError("missing required field(s) on entity='<name>': <f1>, <f2>")`。原先 caller 漏字段走到 SQLite 拿到 `IntegrityError: NOT NULL constraint failed: <table>.<col>`（HTTP 层 → 不透明 400），现在 Entangled 层就 loud fail，字段名明确、一次列完。Commit `15a11e3` 在 Entangled PR#1，6 new tests covering single-missing / all-missing-enumeration / apply-defaults-filled-no-false-trigger / explicit-None-respected / upsert-path / happy-path。
  - **显式 `None` 契约保留**：caller 提供 `{"agent_id": None}` 视为"明确意图写 NULL"，`_apply_defaults` 不覆盖、`_check_required` 也不抛（`name in row` 通过），SQLite 仍正常 raise NOT NULL — 对调用方的 deliberate None 不做 ergonomics。

### 判定不做（记录理由，避免后人再次考虑）

- ~~`novaic-business/business/internal/message.py:_store_add_message` 清理显式 `timestamp`~~ — **不清理**。该 helper 的显式 `timestamp` 不是 silent-failure 防御，而是业务层 HTTP response shape 的组成部分（`agent_chat_event` 返回 `{"timestamp": msg["timestamp"]}`）。`_apply_defaults` 生效后它只是冗余，无害；移除会让 response shape 依赖 Entangled 返回 row 的字段完整性，引入细微耦合。保留即最简。

### 未落地

- [ ] `handle_tool_execute` 的 `event=tool_call_failed` 正式纳入 ops dashboard（目前只在 4h 一次的 bake cron 里；将来 PR-32 metrics 时升级到实时）
