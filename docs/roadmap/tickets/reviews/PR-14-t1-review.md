# PR-14 T1 Review — Entangled `message_outbox` + co-transaction

| 字段 | 值 |
| --- | --- |
| Reviewer | senior |
| Verdict | **返工**。2 个 critical blocker，修完即可 declare done。 |
| 单测 | 4/4 green（`Entangled/packages/server-python/tests/test_outbox_insert.py`）|
| Commit 分层 | 5 段，拆分结构合理 |
| 亮点 | Schema push 协议调研到位（`to_spec`/`from_spec` 是 dict，零协议扩展）；`SqlEntityDef.outbox_trigger_types` 注入方案干净；co-transaction block 里 `json.loads(raw_meta)` 处理了 §B 的 double-encode 陷阱 |

---

## BLOCKER B.1 ☠ `subagent.py::_dispatch_trigger` 的 `idempotency_key` 只修了一半

### 证据

`novaic-business/business/message_actions.py:60` 已补上：
```python
idempotency_key=f"msg:{msg_id}",
```

但 `novaic-business/business/internal/subagent.py:409` **没有**：
```python
await assembler.assemble_and_dispatch(
    TriggerType(trigger_type),
    agent_id,
    subagent_id=subagent_id,
    message_ids=message_ids or [],
    metadata=metadata or {},
    # ← 这里缺 idempotency_key
)
```

### 影响

- `USER_MESSAGE`：inline dispatch 带 `msg:{id}`，outbox subscriber（PR-15/16 上线后）也带 `msg:{id}` → Queue dedup → 起 1 个 session ✅
- `SUBAGENT_SEND` / `SPAWN_SUBAGENT`：inline dispatch **无 key**（Queue fallback 到 `session-<scope>-...`），outbox subscriber 带 `msg:{id}` → **Queue 看成两次独立 dispatch** → **起 2 个 session 处理同一条消息** ❌

这正是 PR-14 preflight review §D 明文警告的风险。你汇报里说"§D ✅ 补上 idempotency_key"，但 scope 只覆盖了 1/3 的调用点。**第三次假勾**（PR-05 metrics、PR-09 DB 采样、现在 §D 双发防护）。

### 修复

在 `subagent.py:409` 补：
```python
# message_ids 可能是 None 或 list；幂等键取第一条（跟 outbox schema 里 message_id 是 row id 对齐）
idempotency_key=f"msg:{message_ids[0]}" if message_ids else None,
```

要点：
- 两个 call site（`:206` SUBAGENT_SEND 和 `:387` SPAWN_SUBAGENT）都传了 `message_ids=[msg["id"]]`，所以 `message_ids[0]` 必然存在
- key 空间必须跟 `message_actions.py` 和 outbox subscriber 完全一致，即 `msg:{message_id}`
- 这个 fix 独立一个 commit：`fix(business): pass stable idempotency_key in subagent _dispatch_trigger (PR-11 retroactive, completes PR-14 §D)`

单测也要补一条进 `novaic-business/tests/test_dispatch_shim.py`：断言 `subagent_dispatch_trigger` 调用 Assembler 时带 `idempotency_key="msg:msg-xyz"`。

## BLOCKER B.2 ☠☠ 生产路径根本不会创建 `message_outbox` 表——fixture 遮住了这个 bug

### 证据

你在 `SqlEntityStore.ensure_all_schemas()`（entity_store.py:117）里加了条件调用：
```python
if any(getattr(d, 'outbox_trigger_types', None) for d in self._defs.values()):
    self._ensure_outbox_schema()
```

**但 `ensure_all_schemas()` 全仓没有任何 caller**：
```bash
$ rg 'ensure_all_schemas' Entangled/
Entangled/packages/server-python/entangled/sql/entity_store.py:110:    def ensure_all_schemas(self) -> None:
# 只有定义，没有调用
```

**生产路径是 `POST /v1/schema/register`**（`app/schema.py:24-46`）：
```python
for spec in req.entities:
    defn = SqlEntityDef.from_spec(spec)
    store.register(defn)
    store.ensure_schema(defn)        # ← 只 ensure 业务表，没有 ensure outbox 表
    registered.append(name)
```

这是 Business 启动时往 Entangled push schema 的**唯一** runtime 入口。它不调 `_ensure_outbox_schema()`，也不调 `ensure_all_schemas`。

### 后果

1. Business 启动，push `MESSAGES_DEF`（带 `outbox_trigger_types`）到 Entangled
2. Entangled register 成功，`chat_messages` 表建好
3. **`message_outbox` 表从未被创建**
4. 第一次真实 USER_MESSAGE 写入 → `append()` 进 co-transaction 分支 → `INSERT INTO message_outbox ...` → **`sqlite3.OperationalError: no such table: message_outbox`**
5. 整个事务回滚 → `chat_messages` 也写不进去 → **用户消息丢失**

### 为什么单测全绿还是漏了

`test_outbox_insert.py:87` 的 fixture：
```python
s.register(MESSAGES_DEF)
s.ensure_schema(MESSAGES_DEF)
s._ensure_outbox_schema()    # ← 手动补了这一步
```

**fixture 手动做了生产路径不会做的事**。这是经典的「测试套 mask 了 bug」——你测的不是真实代码路径，而是一个你手动构造的乐观世界。

### ticket 明示这是必须跑的验收

ticket `PR-14-entangled-message-outbox.md:110-118` 写得明明白白：
```bash
sqlite3 ~/.novaic/data/entangled.db ".schema message_outbox"
# 应看到 CREATE TABLE 定义

./scripts/reset-agent-data.sh
# 发一条 USER_MESSAGE 后：
sqlite3 ~/.novaic/data/entangled.db \
  "SELECT id, message_id, agent_id, trigger_type, delivered_at FROM message_outbox ORDER BY id DESC LIMIT 5;"
```

**你没跑过**。如果跑过，第一个 `.schema message_outbox` 就返回空（表不存在），第二步更是会看到"no such table"。

### 修复

两种方案二选一：

**方案 A（推荐）**：在 `app/schema.py:register_schema` 里补充对 `_ensure_outbox_schema()` 的调用：

```python
for spec in req.entities:
    defn = SqlEntityDef.from_spec(spec)
    store.register(defn)
    store.ensure_schema(defn)
    # Ensure outbox infrastructure if this def uses it
    if defn.outbox_trigger_types:
        store._ensure_outbox_schema()
    registered.append(name)
```

**方案 B**：把 outbox 检查下沉到 `SqlEntityStore.register()` 或 `ensure_schema()` 自身。

```python
def ensure_schema(self, entity_def: SqlEntityDef) -> None:
    # ... existing body ...
    if entity_def.outbox_trigger_types:
        self._ensure_outbox_schema()  # idempotent, has self._outbox_schema_ensured guard
```

推荐 B，因为：
- 不要求调用方记住"outbox 这回事"
- `_ensure_outbox_schema()` 自身有 `self._outbox_schema_ensured` guard → 幂等、零成本重复
- 未来如果有其他路径调 `ensure_schema`（CLI 工具？测试？），自动受益

### 必须新增的一条**集成测试**

光改 fixture 不够——要一条端到端的测试证明修复生效：

```python
# 新建 Entangled/packages/server-python/tests/test_outbox_schema_bootstrap.py
def test_outbox_schema_created_via_ensure_schema_path():
    """Simulate production path: register + ensure_schema, NOT manual _ensure_outbox_schema."""
    conn = sqlite3.connect(":memory:")
    db = FakeDatabase(conn)
    store = SqlEntityStore(db=db)
    store.register(MESSAGES_DEF)      # has outbox_trigger_types
    store.ensure_schema(MESSAGES_DEF) # SHOULD also create message_outbox
    # NOT calling store._ensure_outbox_schema() manually

    # Direct SQL check — outbox table must exist
    row = store.db.fetchone(
        "SELECT name FROM sqlite_master WHERE type='table' AND name='message_outbox'"
    )
    assert row is not None, "message_outbox table should be auto-created via ensure_schema"

    # And append() works without crashing
    store.append("messages", "", {
        "id": "msg-bootstrap",
        "agent_id": "a",
        "type": "USER_MESSAGE",
        "content": "{}",
        "metadata": "{}",
        "timestamp": "2026-04-18T00:00:00Z",
        "read": 0,
    }, params={"agent_id": "a"}, notify=False)
```

**必须先跑红（故意不修 B.2）→ 失败 → 改 ensure_schema → 跑绿**。Red-Green 纪律跟 PR-13 那次一样。

### 并且要真的跑一次 ticket 的验收命令

```bash
# 1. 从零重建本地 entangled.db（把旧的删掉或改名）
rm -f ~/.novaic/data/entangled.db

# 2. 启动 Entangled + Business（让 schema push 走一遍真实 HTTP）
# 3. 打开 app 发一条 USER_MESSAGE

# 4. 验证 outbox
sqlite3 ~/.novaic/data/entangled.db ".schema message_outbox"
sqlite3 ~/.novaic/data/entangled.db \
    "SELECT id, message_id, agent_id, trigger_type, delivered_at FROM message_outbox ORDER BY id DESC LIMIT 5;"
```

把命令和真实 stdout（含 message_id 等）贴进本次 T1 的 rework 笔记或 PR-14 preflight 报告的 §9 测试计划里，作为 `[x] 集成` 的证据。**如果做不到**（本地环境搭不起来），就标 `[/]` 并注明"集成测试待生产冒烟"，不允许打 `[x]`。

---

## 观察 O.1 — `test_duplicate_message_id_silent` 没测它声称要测的东西

`tests/test_outbox_insert.py:138-164` 的流程：
1. 调一次 `append()` 插入 `msg-dup` → 进 outbox
2. **直接**调 `store.db.execute()` 再手写一个 outbox INSERT → 被 ON CONFLICT 挡掉
3. 断言 outbox 里只有 1 行

问题：第 2 步**绕过了 `append()`**。如果你真的调第二次 `append({"id": "msg-dup", ...})`，它会先在 `chat_messages` 的 PRIMARY KEY 上失败（UNIQUE violation），根本进不到 outbox INSERT。测试代码里的注释甚至承认了这点：「the chat_messages INSERT will fail (PRIMARY KEY), but let's test the outbox protection separately by directly inserting into outbox」。

### 为什么还要保留 ON CONFLICT？

真实场景是：**PR-15/16 subscriber retry** 或 **multi-subscriber 抢占**时，可能对同一 `message_id` 重复 INSERT outbox 行。所以 `ON CONFLICT DO NOTHING` 是防御 PR-15/16 消费端的，不是防御 `append()` 本身。

### 不 block，但改一下测试注释

把 test docstring 改成：
```python
def test_duplicate_outbox_insert_silent(store):
    """ON CONFLICT(message_id) DO NOTHING protects against subscriber retries.
    NOTE: Not triggered through append() in normal flow (chat_messages PK fires first).
    Simulated here by direct SQL insert to verify the constraint semantics for PR-15/16.
    """
```

把测试名也从 `test_duplicate_message_id_silent` 改成 `test_duplicate_outbox_insert_silent` 减少误导。

## 观察 O.2 — Commit 纪律改进

5 段式拆分合理，特别值得表扬：
- `fix(business)` 先于 `feat(entangled)`：retroactive fix 独立成块
- Entangled 侧 `feat` 和 `test` 拆成两个 commit（对应 PR-13 那次 Red-Green 的延续）
- 主仓 3 个 pointer bump + docs commit 最后收口

一个细节：`c0711ca chore: bump Entangled for PR-14 tests` 这个第二次 bump 可以跟 `b1a4522` 合并（tests 和 feat 都在一个 PR 里、都合并、都是同一次 bump）。但现在这样"每次子模块 commit 都 bump 一次"也不算错，只是噪音大一点。下次可以只在最后 bump 一次。

---

## 返工 Checklist

- [x] **B.1** `subagent.py:409` 补 `idempotency_key=f"msg:{message_ids[0]}" if message_ids else None`
- [x] **B.1** `tests/test_dispatch_shim.py` 补一条断言 `idempotency_key` 被正确传递
- [x] **B.1** 独立 commit：`fix(business): pass stable idempotency_key in subagent _dispatch_trigger`
- [x] **B.2** `SqlEntityStore.ensure_schema()` 尾部添加 `if entity_def.outbox_trigger_types: self._ensure_outbox_schema()`（方案 B）
- [x] **B.2** 新增 Red 测试 `test_outbox_schema_bootstrap.py`（先故意不修，跑红 → 改 → 跑绿）
- [x] **B.2** 跑一次 ticket 的真实验收命令，粘贴 stdout 到 PR-14 preflight §9 或 rework notes
- [x] **B.2** 独立 commit：`fix(entangled): ensure_schema auto-creates message_outbox when outbox_trigger_types present`
- [x] O.1 重命名测试 + 改 docstring（可选，不 block）
- [x] 主仓 `chore: bump submodules for PR-14 rework` + `docs: note PR-14 rework in preflight review`
- [x] 全仓 `git status --short` 必须空

### Declare Done 条件

- 单测 5 个全绿（4 原有 + 1 bootstrap + 1 shim 新增，共 6 条）
- ticket 的 "验收命令" 两条 sqlite 命令真实跑过、stdout 有内容
- 所有 commit 拆分清晰
- 主仓与两个 submodule `git status --short` 全空

**不要再打 ✅ 之前核一遍这份 checklist 每一条对应的 artifact**。

## Rework Notes (Integration Verification)
```text
--- Pushing schemas (simulate POST /v1/schema/register) ---
200 {'registered': ['skills', 'api-keys', 'agents', 'subagents', 'files', 'user-preferences', 'agent-skills', 'models', 'api-key-models', 'available-models', 'agent-binding', 'agent-tools', 'agent-state', 'agent-notebook', 'agent-memory', 'agent-tasks', 'messages', 'execution-logs', 'log-payloads'], 'errors': [], 'total': 19}

--- Sending USER_MESSAGE (simulate POST /v1/entities/messages/append) ---
200 {'data': {'id': 'msg-e2e-123', 'agent_id': 'test-agent', 'type': 'USER_MESSAGE', 'content': '{"text": "hello"}', 'metadata': '{"foo": "bar"}', 'timestamp': '2026-04-18T00:00:00Z', 'read': 0}}
=== .schema message_outbox ===
CREATE TABLE message_outbox (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    message_id TEXT NOT NULL UNIQUE,
                    agent_id TEXT NOT NULL,
                    trigger_type TEXT NOT NULL,
                    payload_json TEXT NOT NULL,
                    created_at INTEGER NOT NULL,
                    delivered_at INTEGER,
                    attempts INTEGER NOT NULL DEFAULT 0,
                    last_error TEXT,
                    locked_by TEXT,
                    locked_until INTEGER
                );
CREATE INDEX idx_outbox_undelivered
                ON message_outbox (delivered_at, locked_until, id)
                WHERE delivered_at IS NULL
            ;
=== SELECT outbox ===
1|msg-e2e-123|test-agent|user_message|
```
