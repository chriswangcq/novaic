# PR-31  `*_state_transitions` 日志表（持久化转移历史）

| 字段 | 值 |
| --- | --- |
| **Phase** | 5 |
| **Milestone** | M4 |
| **承诺** | R8 |
| **Status** | `[x]` |
| **Depends on** | PR-28, PR-29, PR-21 |
| **Blocks** | — |
| **估时** | 1 d |
| **Owner** | 2026-04-15 |
| **PR 标题** | `feat(observability): state_transitions log tables for subagent/scope/message` |

## 目标

把 `transition(...)` 的事件流持久化成可查表，便于事后回放 "这个实体的完整生命周期"。纯观测能力。

## 范围

- Entangled schema：新增 `subagent_state_transitions`、`message_state_transitions`
- Cortex 本地存储：`scope_state_transitions.sqlite` 或 append-only log 文件
- 对应 `transition()` 函数里写入逻辑

## 前置 Checklist

- [ ] PR-21 / PR-28 / PR-29 都已落地（transition 唯一入口）

## 实施 Checklist

### Schema

```sql
-- 模板（subagent_state_transitions、message_state_transitions 结构一致）
CREATE TABLE subagent_state_transitions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    entity_id TEXT NOT NULL,
    from_state TEXT NOT NULL,
    to_state TEXT NOT NULL,
    reason TEXT,
    actor TEXT,                    -- service_name / worker_id
    scope_id TEXT,                 -- 若相关
    metadata_json TEXT,
    created_at INTEGER NOT NULL
);
CREATE INDEX idx_sst_entity ON subagent_state_transitions (entity_id, created_at);
```

### Scope 侧（Cortex）

- [ ] 若 Cortex 独立于 Entangled DB，在 Cortex 的 `scope_locks` 相邻位置放 `scope_state.sqlite`（或追加 `events.ndjson`）
- [ ] 同步写：transition 成功后立即 append

### Transition 函数里写入

```python
def transition(store, entity_id, *, to, reason, actor, extra=None):
    # ... 原有逻辑
    store.execute("""
        INSERT INTO subagent_state_transitions
            (entity_id, from_state, to_state, reason, actor, metadata_json, created_at)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    """, (entity_id, cur, to, reason, actor, json.dumps(extra or {}), now_ms))
```

### 查询端点 / CLI

- [ ] Business `GET /internal/subagents/{id}/history` → 返回 transition 列表
- [ ] Entangled 或 Business 暴露 `GET /internal/messages/{id}/history`
- [ ] Cortex `GET /v1/scope/{id}/history`

### 保留策略

- [ ] 日志表按 entity_id 建 index；默认无 TTL（运维按需清理）

## 测试 Checklist

- [ ] 单测：transition 写一行 log
- [ ] 集成：spawn → sleep → wake → archive → history 返回 4 条记录
- [ ] 集成：message pending → claimed → consumed → history 返回 2 条转移

## 可观测性 Checklist

- [ ] `GET /history` 端点有 metric
- [ ] 日志表 size 作为 DB 体积监控

## 文档 Checklist

- [ ] [message-wake-refactor.md](../message-wake-refactor.md) P5-3 → `[x]`
- [ ] 本工单 Status → `[x]`
- [ ] `docs/runbooks/troubleshooting.md` 加 "按 history 回放实体生命周期"

## 验收命令

```bash
sqlite3 ~/.novaic/data/entangled.db ".schema subagent_state_transitions"
# 存在
sqlite3 ~/.novaic/data/entangled.db \
  "SELECT entity_id, from_state, to_state, reason, actor FROM subagent_state_transitions ORDER BY id DESC LIMIT 5;"
```

## 回滚

`git revert` —— 删 INSERT 路径；表可保留作为空表。

## 备注

- 本 PR 完成后，"这个实体为什么还在 sleeping" 变成一次 history 查询。
- 未来可将 metric emitter（PR-26）改为从 history 表驱动，统一事件源。

---

## 落地实现（2026-04-15）

### 存储分布

| 机器 | 位置 | 写入时机 | 读取入口 |
| --- | --- | --- | --- |
| **message** | Entangled SQL `message_state_transitions` 表 | `message_state.transition` 内部，co-transactional（`transaction("global")` 同块内 INSERT，和 `UPDATE chat_messages` 原子提交） | `GET /v1/state_transitions/message/{id}` / `GET /internal/messages/{id}/trace` 里的 `history[]` |
| **subagent** | Entangled SQL `subagent_state_transitions` 表 | Business `subagent_state.transition` 成功 `store.update` 后，POST `/v1/state_transitions/subagent` （best-effort，失败仅 WARN 不 rollback） | `GET /v1/state_transitions/subagent/{id}` / `GET /internal/subagents/{agent_id}/{subagent_id}/state-history` |
| **scope** | Cortex 本机 NDJSON 追加文件（默认 `~/.novaic/cortex/scope_state_transitions.ndjson`，`CORTEX_SCOPE_STATE_LOG` 覆盖） | `scope_state.transition` 在 meta.json 更新成功后 append | `GET /v1/scope/history?scope_path=...&limit=...` |

Scope 侧选 NDJSON 而非 sqlite：Cortex 不依赖 Entangled，引入 HTTP/SQL 都是新的 coupling；NDJSON POSIX append 已是崩溃安全的写法，量级（每次对话几行）完全够用。跨主机聚合留给 sidecar（tail + 远送），不在本 PR 范围。

### 幂等与静默

- **self-loop 不写日志**。这是从 PR-23 / PR-29 延伸的不变式：订阅者/recovery 重试会触发 A→A 幂等路径，若 log 每次都写，一个 stuck message 就能淹没整张表。测试 `test_message_transition_noop_does_not_log` / `test_self_loop_does_not_log` / `test_self_loop_noop_skips_history_log` 把它钉住。
- **子代理 log POST 失败不 rollback**。`subagents.status` 已经先写了，这时 Entangled 500 也不该让业务面看到假失败——用 `try/except` 吞下，WARN 一行。测试 `test_transition_swallows_log_hook_errors` 覆盖。
- **message log 共事务**。因为它本来就在 Entangled 内部，能塞进同一个 `transaction("global")` 里，就正好不必容忍断档。

### 新文件

- `Entangled/packages/server-python/entangled/sql/state_transitions.py` — 两张表的 schema + reader/writer。
- `Entangled/packages/server-python/entangled/app/state_transitions.py` — FastAPI router（POST/subagent、GET/subagent、GET/message）。
- `Entangled/packages/server-python/tests/test_state_transitions.py` — 10 条用例。
- `novaic-cortex/novaic_cortex/scope_state_log.py` — NDJSON 读写。
- `novaic-cortex/tests/test_scope_state_log.py` — 9 条用例。

### 修改点

- `Entangled/.../sql/message_state.py`：`transition` 内 `INSERT INTO message_state_transitions`（co-tx）。
- `Entangled/.../sql/entity_store.py::ensure_all_schemas`：调用 `ensure_state_transitions_schema(db)`。
- `Entangled/.../app/factory.py`：注册 `state_transitions_router`。
- `novaic-common/common/entangled_client.py`：新增 `record_subagent_transition` / `history_*`。
- `novaic-business/business/internal/subagent_state.py`：`_record_transition` 后置 HTTP 上报。
- `novaic-business/business/internal/subagent.py`：新增 `GET /subagents/{agent_id}/{subagent_id}/state-history`。
- `novaic-business/business/internal/message.py`：`/internal/messages/{id}/trace` 的响应新增 `history[]`（soft-fail）。
- `novaic-cortex/novaic_cortex/scope_state.py`：`transition` 成功后 `await append_transition(...)`。
- `novaic-cortex/novaic_cortex/api.py`：新增 `GET /v1/scope/history`。

### 验收

```bash
# Entangled 本地
cd Entangled/packages/server-python
pytest tests/test_state_transitions.py tests/test_message_state.py
# 10 + 26 passed

# Cortex 本地
cd ../../../novaic-cortex
pytest tests/test_scope_state.py tests/test_scope_state_log.py
# 15 + 9 passed

# Business 本地
cd ../novaic-business
pytest tests/test_subagent_state.py
# 25 passed（含 PR-31 新增的 3 条 hook 用例）
```

### 后续可做

- **PR-31b**（已完成，2026-04-15）：见下方。
- **PR-31c**（已完成，2026-04-15）：见下方。

---

## PR-31b（subagent 状态机 server-side 化，2026-04-15）

### 背景

PR-31 原始实现里 Business 的 `subagent_state.transition` 走了 3 次 HTTP：

1. `GET /v1/entities/subagents/{id}`（读当前 status）
2. `PATCH /v1/entities/subagents/{id}`（写新 status）
3. `POST /v1/state_transitions/subagent`（best-effort 写历史）

步骤 2 和 3 之间不具原子性——Business 在这两步之间崩溃会导致 history 丢一条，这是 PR-31 最初就承认的观测性妥协。既然 `message_state.transition` 早在 PR-21 就做到"server-side transition + co-tx 历史"的范式，用同样的模式收掉 subagent 的历史断档显然是顺手的事。

### 架构变化

| 维度 | Before（PR-31） | After（PR-31b） |
| --- | --- | --- |
| HTTP 往返数 | 3（GET / PATCH / POST） | 1（POST `/v1/subagents/{agent_id}/{subagent_id}/transition`） |
| 原子性 | status 写入独立于 history；crash 丢 history | `subagents.status UPDATE` + `subagent_state_transitions INSERT` 在同一个 `transaction("global")` 内 |
| 校验位置 | Business 的 ALLOWED matrix + 自环检测 + Entangled 侧 PATCH 无校验 | Entangled 内部再次校验（defense in depth），Business 的 `ALLOWED` 退化为 informational |
| 错误映射 | Business 本地 raise | HTTP 404 → `SubagentNotFound`，HTTP 409 → `SubagentInvalidTransition`；client 翻译回 Business 的 local exceptions |

### 新文件

- `Entangled/packages/server-python/entangled/sql/subagent_state.py` — `ALLOWED_TRANSITIONS` + `EXTRA_ALLOWLIST` + `transition(db, subagent_id, agent_id, *, to, reason, actor, extra)` core。
- `Entangled/packages/server-python/entangled/app/subagent_state.py` — FastAPI router（`POST /v1/subagents/{agent_id}/{subagent_id}/transition`、`GET /v1/subagents/states`）。
- `Entangled/packages/server-python/tests/test_subagent_state.py` — 9 条单测（atomic UPDATE、self-loop extras、illegal transition、missing subagent、bogus `extra` key 被 drop、co-tx history row）。

### 修改点

- `Entangled/.../app/factory.py`：注册 `subagent_state_router`；在 `lifespan` 里 eagerly 调用 `ensure_state_transitions_schema(db)`（PR-31 hotfix：`ensure_all_schemas` 从没被调用过，之前的 wiring 是死代码）。
- `Entangled/.../sql/state_transitions.py`：`append_subagent_transition` 变成 transaction-agnostic（配合 `message_state` 现有模式）；deadlock hotfix，详见下方。
- `Entangled/.../app/state_transitions.py`：遗留 `POST /v1/state_transitions/subagent` shim 显式 wrap 自己的 `transaction("global")`（因为 helper 不再开事务）。
- `novaic-common/common/entangled_client.py`：新增 `transition_subagent`；`EntangledClientError` 挂上 `status_code` 字段；新增 `SubagentNotFound` / `SubagentInvalidTransition` 两个 typed exception。
- `novaic-business/business/internal/subagent_state.py`：`transition()` 全量改为 delegate 到 client。`_record_transition` 改名 `_bump_counter`（不再发 HTTP，只维护进程内 Counter 给测试用）。`ALLOWED` / `SubagentStatus` 保留作后向兼容（introspection callers 还在读）。
- `novaic-business/tests/test_subagent_state.py`：重写成 mock HTTP client 驱动，18 条全绿。

### 部署阶段的两个活坑

1. **死代码 schema wiring（PR-31 hotfix，生产跑了一次就炸）**：`ensure_state_transitions_schema` 最初挂在 `SqlEntityStore.ensure_all_schemas` 里，但那个方法在生产根本没人调用（Entangled 走的是 `POST /v1/schema/register` 动态注册链，只跑 `SqlEntityDef` 注册的实体）。结果第一次部署后 `sqlite3 .tables` 看不到 `message_state_transitions` / `subagent_state_transitions`——幂等 self-loop 过滤器把所有 transition 压住了，没暴露成 500。修：挪进 `app.factory.lifespan`，跑在每次启动的 sync_versions 之后。

2. **嵌套事务死锁（PR-31b hotfix，smoke 15s timeout 才暴露）**：`append_subagent_transition` 原本自己 `with db.transaction("global"):`。遗留 shim 走得通是因为它是唯一 caller。PR-31b 让 `subagent_state.transition` 也调用它时——外层已经拿了 global 写锁——nested acquisition 在真 SQLite 上直接死锁。对比参考 `append_message_transition` 一直都是 transaction-agnostic。修：`append_subagent_transition` 去掉内层事务，让遗留 shim 自己 wrap。**单测没发现因为 `FakeDatabase` 的 CM 是无锁可重入的**。

### 生产 smoke（2026-04-15，api.gradievo.com）

```bash
# Step 1: self-loop sleeping -> sleeping，应为 noop，不写日志
curl -X POST http://127.0.0.1:19900/v1/subagents/$AID/$SID/transition \
     -H "X-Service-Token: $TOKEN" \
     -d '{"to": "sleeping", "reason": "smoke-selfloop", "actor": "ops-smoke"}'
# → HTTP 200, {"noop": true}, history table unchanged

# Step 2: sleeping -> awake，必须原子 UPDATE + 写 history row
curl -X POST http://127.0.0.1:19900/v1/subagents/$AID/$SID/transition \
     -H "X-Service-Token: $TOKEN" \
     -d '{"to": "awake", "reason": "smoke-flip-awake", "actor": "ops-smoke"}'
# → HTTP 200, {"noop": false}, subagents.status='awake', history row id=1

# Step 3: awake -> sleeping with extras（need_rest=0）
curl -X POST http://127.0.0.1:19900/v1/subagents/$AID/$SID/transition \
     -H "X-Service-Token: $TOKEN" \
     -d '{"to": "sleeping", "reason": "smoke-flip-sleeping", "actor": "ops-smoke",
          "extra": {"need_rest": 0}}'
# → HTTP 200, {"noop": false}, subagents.status='sleeping', history row id=2

# History replay
curl -H "X-Service-Token: $TOKEN" \
     "http://127.0.0.1:19900/v1/state_transitions/subagent/$SID?limit=10"
# → {"count": 2, "rows": [id=1 sleeping->awake, id=2 awake->sleeping]}
```

所有三次 call <3ms，端态 `sleeping → sleeping`（幂等无副作用），history 表精确记下 2 条非 noop 转移。

### 验收（local）

```bash
# Entangled
cd Entangled/packages/server-python
pytest tests/test_subagent_state.py tests/test_state_transitions.py
# 9 + 10 passed

# Business
cd ../../../novaic-business
pytest tests/test_subagent_state.py
# 18 passed

# 全量回归
cd ../Entangled/packages/server-python
pytest tests/  # 99 passed
```

### 后续可做

- **PR-31c**（已完成）：见下方。
- **补充 lint**：`scripts/ci/lint_subagent_status.sh` 已经禁止裸 `UPDATE subagents SET status`；PR-31b 后可以再加一条禁止直接 POST 到 `/v1/state_transitions/subagent`（强制走 `transition_subagent`），消除遗留 shim 的诱惑。

---

## PR-31c（删除 in-process `_transitions` Counter，统一事件源，2026-04-15）

### 背景

PR-31 + PR-31b 落地后，transition 事件有三条 parallel 路径：

1. **canonical log line**（`rg subagent_state subagent=<id>` / `rg scope_state scope=<path>`）——operator 扫跨服务时间线用。
2. **durable history table / NDJSON**（`subagent_state_transitions` / `message_state_transitions` / `scope_state_transitions.ndjson`）——机器可查，count/rate 查询 + 单实体生命周期 replay 用。
3. **in-process `collections.Counter`**（`business.internal.subagent_state._transitions` / `novaic_cortex.scope_state._transitions`）——PR-28/29 上线时写的 pre-PR-31 stopgap，key 是 `"<from>-><to>/<reason>"`。

源 3 是死路径：(a) `dump_transition_counters()` 全仓只有测试调，runbook 里写着 "operators can dump via..." 但从没有人真这么做过；(b) 每次部署重置；(c) 跨进程不可见。PR-31 的 durable table 和 PR-26 的 orphan emitter 把这个 Counter 承载的需求全覆盖了——留着只是多一条和真实数据漂移的可能性。

PR-31c 就是把源 3 砍掉。剩下两条源：log line 做 human-timeline grep，durable table/NDJSON 做机器查询，分工干净。

### 改动

- `novaic-business/business/internal/subagent_state.py`：
  - 删除 `_transitions: Counter`、`dump_transition_counters()`。
  - `_bump_counter()` 改名 `_log_breadcrumb()`，只保留结构化 log 调用。
  - `transition()` 在非 noop 分支调用 `_log_breadcrumb` 而不是 bump counter。
  - `__all__` 去掉 `dump_transition_counters`。

- `novaic-cortex/novaic_cortex/scope_state.py`：
  - 删除 `_transitions: Counter`、`dump_transition_counters()`、`Counter` 导入。
  - `_record_transition()` 改名 `_emit_transition()`，只保留 `logger.info` + `log_cortex`。transition() 仍然 await `append_transition` 写 NDJSON。
  - `__all__` 去掉 `dump_transition_counters`。

- `novaic-business/tests/test_subagent_state.py`：
  - 删除 `_reset_counters` autouse fixture。
  - 把所有 `assert subagent_state._transitions[...] == N` 的断言改成 `fake.transition_subagent.assert_called_once_with(...)` 或 `fake.call_args.kwargs[...] == ...`——比 Counter 断言更精确（直接 pin 了 wire 上的 kwargs）。
  - `test_self_loop_noop_does_not_bump_counter` 改成 `test_self_loop_noop_returns_noop_true`，用 `caplog` 确认 breadcrumb log line 不出现（取代 Counter 为 0 的断言）。
  - `test_metric_key_is_from_to_slash_reason` 改成 `test_each_transition_makes_one_client_call_with_reason`——同样的意图（reason 被正确透传），新的断言基于 mock call_args。

- `novaic-cortex/tests/test_scope_state.py`：
  - 把 `_reset_counters` 替换成 `log_mock` autouse fixture（patch `scope_state_log.append_transition`）。autouse 同时修了一个 pre-existing 隐患：PR-31 之后这些 test 的 `transition()` 非 noop 路径默默往 `$HOME/.novaic/cortex/` 写 NDJSON。
  - 把 `dump_transition_counters()` 断言改成 `log_mock.await_args.kwargs` 或 `log_mock.await_count` 断言。
  - `test_self_loop_is_noop_no_metric_bump` → `test_self_loop_is_noop_and_writes_no_log_row`（INV-5 测的是 "retry 不多写一行"，改成直接看 log_mock 没被 await 即可）。

- `novaic-cortex/tests/test_scope_state_log.py`：删除 `_reset_counters` autouse（Counter 没了没什么可 reset 的）。

### 不影响

- Log line 完全保留——`rg subagent_state subagent=<id>` / `rg scope_state scope=<path>` 还是 operator 扫跨服务时间线的入口。
- Durable table（`*_state_transitions`）+ Cortex NDJSON 完全保留，写入时机和 PR-31/PR-31b 一致。
- Entangled 侧没有 Counter，不在 scope 内。

### 验收（local）

```bash
# Business: 18/18 scope_state tests + 61/61 full suite
cd novaic-business
pytest tests/test_subagent_state.py -q
pytest -q --ignore=tests/contract --ignore=tests/test_outbox_endpoints.py --ignore=tests/test_message_trace.py

# Cortex: 24/24 scope_state + scope_state_log
cd ../novaic-cortex
pytest tests/test_scope_state.py tests/test_scope_state_log.py -q
```

全仓搜索 `dump_transition_counters` 和 `_transitions[` 只剩在 commit message / historical 文档里的引用，运行时代码 0 命中。

### 生产影响

纯代码精简，无 schema 变更，无新 endpoint，无部署 order 约束。部署后唯一的可观察差异：**不再可能**通过 `python -c "from business.internal.subagent_state import dump_transition_counters; print(dump_transition_counters())"` 拿到进程内 counter——该 helper 已删除。operator 想要等价信息，用：

```bash
curl -H "X-Service-Token: $TOKEN" \
     "http://127.0.0.1:19900/v1/state_transitions/subagent/$SID?limit=50"
```

或者对 count/rate 查询直接 `sqlite3 entangled.db` + `SELECT COUNT(*) FROM subagent_state_transitions GROUP BY from_state, to_state, reason`。
