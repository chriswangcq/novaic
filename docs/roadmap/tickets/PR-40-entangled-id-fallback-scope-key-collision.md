# PR-40  Entangled `_sql_create / append` 自动 id 兜底错用 scope-key（chat_reply UNIQUE 崩溃根因）

| 字段 | 值 |
| --- | --- |
| **Phase** | hotfix（Entangled 核心 ID-生成路径的设计缺陷修复） |
| **Milestone** | — |
| **承诺** | 架构原则：**系统简单** + **无隐式契约** + **fail-fast** |
| **Status** | `[x]` 2026-04-21 完成 — Entangled `a193099` + 4 unit tests + 104 回归全绿 |
| **Depends on** | — |
| **Blocks** | — |
| **估时** | 0.5 d |
| **Owner** | wangchaoqun |
| **PR 标题** | `fix(entangled): only use key_params[0] as id when id_field==key_params[0]` |

## 事件摘要

生产 `chat_reply` 工具**连续多次**失败，错误栈：

```
POST /internal/entities/messages → HTTP 400
reason=API error (400): API error (400): UNIQUE constraint failed: chat_messages.id
```

表现：Agent 能成功回复第一条消息，之后所有回复都被 UNIQUE 顶回来，用户侧静默（`event=tool_call_failed` 被 tool handler 吞到 `tool_output` 里）。

**DB 现场铁证**（生产 `/opt/novaic/data/entangled.db`）：

```sql
SELECT COUNT(*) FROM chat_messages WHERE id = agent_id;
-- 1

SELECT id, agent_id, type FROM chat_messages WHERE id = agent_id;
-- 415f6cfd4e5b4a04911b66cb8ab2cad7 | 415f6cfd4e5b4a04911b66cb8ab2cad7 | AGENT_REPLY
```

每条 `AGENT_REPLY` 的 `id` 都被写成了 `agent_id`。第一条 INSERT 成功，之后全部 UNIQUE 冲突。

## 根因

### 触发调用（caller 没错）

`novaic-agent-runtime/task_queue/handlers/tool_handlers.py:105`：

```python
gw.entity_create("messages", {
    "type": "AGENT_REPLY",
    "content": message,
    "attachments": attachments,
    "sender": "agent",
    "read": 1,
    "timestamp": utc_now_iso(),
}, params={"agent_id": deps["agent_id"]})
```

**没传 `id`**，依赖 Entangled 自动生成。这符合"通用 CRUD 代理"的语义约定（caller 不知道 per-entity id 策略）。

### Entangled 兜底逻辑（bug 现场）

`Entangled/packages/server-python/entangled/sql/entity_store.py:367-377` (`_sql_create`) 与 `:572-582` (`append`) 两处完全相同的代码块：

```python
id_f_def = defn.field_map.get(defn.id_field) if defn.fields else None
is_auto_int = id_f_def and id_f_def.kind.name == "INTEGER"
res_id = row.get(defn.id_field, "")
if not res_id and not is_auto_int:
    if params and defn.key_params:
        res_id = params.get(defn.key_params[0], "")   # ← 缺陷点
        if res_id:
            row[defn.id_field] = res_id               # ← 把 scope-key 塞成主键
    if not res_id:
        res_id = uuid.uuid4().hex
        row[defn.id_field] = res_id
```

`MESSAGES_DEF`：

```python
# novaic-business/business/schema_push.py:404-419
MESSAGES_DEF = SqlEntityDef(
    name="messages",
    table="chat_messages",
    id_field="id",
    user_scoped=False,
    key_params=["agent_id"],          # ← scope 键
    parent=("agents", "agent_id", "id"),
    ...
)
```

`id_field="id"` ≠ `key_params[0]="agent_id"`。兜底逻辑不区分这两种语义，无脑拿 `params["agent_id"]` 当 id 写入 → 每条 agent 消息的 `id` 都塞成该 agent 的 id。

### 为什么 USER_MESSAGE 路径没事

`novaic-business/business/message_actions.py:30` 显式生成 id：

```python
msg_id = _uuid.uuid4().hex[:12]
row = {"id": msg_id, ...}
store.append("messages", user_id, row, params={"agent_id": agent_id})
```

USER 路径从不让 Entangled 兜底，所以侥幸躲过了这个雷。

### 设计缺陷本质

Entangled 这个"`params[key_params[0]]` 当 id" 的兜底，原本是给**单例实体**准备的：`id_field == key_params[0]`，意思就是"这个实体按 scope-key 做主键（每个 agent 一行）"。看 `schema_push.py` 的符合此模式的只有三个：

| 实体 | id_field | key_params[0] | 合法性 |
| --- | --- | --- | --- |
| `AGENT_BINDING_DEF` | `agent_id` | `agent_id` | ✅ 合法（单例） |
| `AGENT_TOOLS_DEF` | `agent_id` | `agent_id` | ✅ 合法（单例） |
| `AGENT_STATE_DEF` | `agent_id` | `agent_id` | ✅ 合法（单例） |

对**流式 / 列表实体**（`id_field != key_params[0]`），兜底把 scope-key 当主键就是灾难：

| 实体 | id_field | key_params[0] | 当前状态 |
| --- | --- | --- | --- |
| `MESSAGES_DEF` | `id` | `agent_id` | 🔥 **PR-40 修复目标** |
| `SUBAGENTS_DEF` | `subagent_id` | `agent_id` | 潜雷（调用方都手动填 subagent_id） |
| `AGENT_SKILLS_DEF` | `skill_id` | `agent_id` | 潜雷（调用方都填 skill_id） |
| `AGENT_MEMORY_DEF` | `key` | `agent_id` | 潜雷（调用方都填 key） |
| `API_KEY_MODELS_DEF` | `id` | `api_key_id` | 潜雷 |
| `AGENT_NOTEBOOK_DEF` / `AGENT_TASKS_DEF` / `EXECUTION_LOGS_DEF` / `LOG_PAYLOADS_DEF` | INTEGER `id` | `agent_id` | `is_auto_int` 分支绕开，安全 |

`messages` 是唯一**同时满足**"流式实体 + 调用方依赖自动 id + TEXT 主键"这三个条件的实体，所以它第一个炸。

## 修复方案

### A. 兜底条件收窄（根治）

`_sql_create` 和 `append` 两处 id-兜底改为：**只在 `defn.key_params[0] == defn.id_field` 时用 params 值**，否则直接走 uuid：

```python
if not res_id and not is_auto_int:
    # Only fall back to scope-key when it IS the primary key
    # (singleton-per-key entities: agent-profile, agent-tools, agent-state).
    # For stream/list entities (messages, subagents, agent-memory, ...)
    # id_field != key_params[0] — DO NOT use scope key as id, mint a uuid.
    if (
        params
        and defn.key_params
        and defn.key_params[0] == defn.id_field
    ):
        res_id = params.get(defn.key_params[0], "")
        if res_id:
            row[defn.id_field] = res_id
    if not res_id:
        res_id = uuid.uuid4().hex
        row[defn.id_field] = res_id
```

两处并改，保证语义一致（`_sql_create` 普通 entity，`append` 流式 entity）。

### B. lock_id 保持不变

`append` 下方 `lock_id = res_id or (params.get(defn.key_params[0], "") if params and defn.key_params else "") or "auto"` —— lock 拿 scope-key 做 resource_id 是**正确的**（锁 scope 级别，不是行级别），这一行**不动**。本 PR 只修 id 的生成，不碰锁语义。

### C. 回归测试

新增 `Entangled/packages/server-python/tests/test_id_fallback_scope_key.py`：

1. **stream entity 独立 id**：两次 `append("messages", ..., params={"agent_id": "A"})`，不传 `id` → 返回两行 `id` 都是 uuid hex，互不相等，且都 `!= "A"`。
2. **singleton entity 用 scope-key 做 id**：`append/create` `agent-tools`, params={"agent_id": "A"} → 返回 `agent_id == id == "A"`（既有行为保留）。
3. **caller 显式 id 最高优先级**：传 `{"id": "explicit-123"}` 即使 key_params 匹配 id_field，最终 id 仍是 `"explicit-123"`。
4. **is_auto_int 分支不受影响**：`execution-logs` INTEGER id 仍自增。

### D. 脏数据处理

生产 DB 里那一条 `id == agent_id == "415f6cfd4e5b4a04911b66cb8ab2cad7"` 的旧 AGENT_REPLY 行：

- 不影响查询（API 按 `agent_id` 过滤，仍能正确返回）。
- **建议保留不动**，当考古痕迹；用 `SELECT id FROM chat_messages WHERE id = agent_id` 任何时候能溯源到"PR-40 之前被兜底路径污染的消息"。
- 如果洁癖党介意，可单独起一个 one-shot 脚本改 id。本 PR 不包含。

## 子 PR

| # | Repo | Branch | 内容 |
|---|---|---|---|
| 1 | `Entangled` | `fix/id-fallback-scope-key-collision` | A：`_sql_create` + `append` 兜底条件加 `key_params[0] == id_field` 守卫 + D 测试文件 |
| — | 主仓 | `fix/chat-reply-unique-collision-40` | submodule bump + HANDOVER 追记 |

**Merge 顺序**：Entangled 先单独通过 CI 后合，主仓再 bump 指向新 commit。`./deploy services` 部署。

## 验收

- `pytest Entangled/packages/server-python/tests/test_id_fallback_scope_key.py -v` 全绿（4 个 case）。
- 既有 Entangled 测试（`test_apply_defaults.py` / `test_outbox_insert.py` / `test_outbox_endpoints.py` / `test_outbox_schema_bootstrap.py`）不回归。
- 生产验证：部署后用户连发 3 条消息，prod `/opt/novaic/data/logs/task-worker-execution-*.log` 不再出现 `UNIQUE constraint failed: chat_messages.id`；`sqlite3 entangled.db "SELECT COUNT(*) FROM chat_messages WHERE id=agent_id"` 计数 = 1（仅保留那条旧行），`AGENT_REPLY` 新行 id 都是 12 位 hex。
- `HANDOVER.md` 追一条 `2026-04-21：PR-40 —— Entangled id 兜底路径把 scope-key 误当主键导致 chat_reply UNIQUE 冲突，兜底条件加 id_field==key_params[0] 守卫，根治`。

## 回滚

`git revert <commit>` 在 Entangled 仓恢复原兜底逻辑。无 schema migration，无数据迁移。回滚后的"脏"行为是 chat_reply 再度 UNIQUE（退回 PR-40 前症状）。

## 架构判定沉淀

- **兜底的边界语义要在代码里表达**：Entangled 这条兜底路径原先的意图（"单例实体用 scope-key 当主键"）只能从调用方行为倒推，代码自己没声明。PR-40 把这个约束显式写进条件 `key_params[0] == id_field`，未来 schema review 时 `id_field != key_params[0]` 的实体自动落到 uuid 分支，不需要调用方记住"要手动填 id"。
- **通用 CRUD 代理的契约应是 "caller 不传 id → 得到唯一 id"**，不能依赖 scope-key 的形状。`tool_handlers._exec_chat_reply` 不填 id 是**合法用法**，这次 bug 不是 caller 的问题，是 Entangled 的问题 —— 本 PR 把这个责任边界还给 Entangled。
- **把潜雷一次扫干净**：`SUBAGENTS_DEF` / `AGENT_SKILLS_DEF` / `AGENT_MEMORY_DEF` / `API_KEY_MODELS_DEF` 当前靠调用方"自律填 id" 侥幸，PR-40 合了之后它们自动变成"即使哪天有调用方忘记填 id，也只会拿到 uuid 而不是 scope-key 污染"。这是一次根治型清理，对整个流式实体家族免疫。
