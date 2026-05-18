# PR-40  Entangled id 兜底路径删除（fail-fast / 无静默失败）

| 字段 | 值 |
| --- | --- |
| **Phase** | hotfix（Entangled 核心 ID-生成路径的设计缺陷修复） |
| **Milestone** | — |
| **承诺** | 架构原则：**无静默失败** + **系统简单** + **fail-fast** |
| **Status** | `[x]` 2026-04-21 完成 — Entangled 删 fallback + `_exec_chat_reply` 显式填 id + 5 unit tests + 105 回归全绿 |
| **Depends on** | — |
| **Blocks** | — |
| **估时** | 0.5 d |
| **Owner** | wangchaoqun |
| **PR 标题** | `fix(entangled): remove id-fallback, fail-fast when caller omits non-auto-int id` |

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
    ...
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
        res_id = params.get(defn.key_params[0], "")   # ← 缺陷 (a)
        if res_id:
            row[defn.id_field] = res_id               # ← 把 scope-key 塞成主键
    if not res_id:
        res_id = uuid.uuid4().hex                     # ← 缺陷 (b) silent uuid mint
        row[defn.id_field] = res_id
```

两层 fallback 都违反「无静默失败」原则：

- **(a) scope-key coercion**：`MESSAGES_DEF.key_params = ["agent_id"]`, `id_field = "id"` —— fallback 拿 `params["agent_id"]` 当主键，流式实体每条记录 id 都等于 `agent_id`，第一条 INSERT 成功，之后全部 UNIQUE 冲突（**这次生产症状**）。
- **(b) silent uuid mint**：即便 (a) 不命中，`uuid.uuid4().hex` 会静默造一个 id 写入，调用方"忘了生成 id"的 bug 从此永远静默存在 —— 插入成功但调用方自己的 id-tracking 逻辑错了，没人发现。

### 对照：USER_MESSAGE 路径为什么没事

`novaic-business/business/message_actions.py:30` 显式生成 id：

```python
msg_id = _uuid.uuid4().hex[:12]
row = {"id": msg_id, ...}
store.append("messages", user_id, row, params={"agent_id": agent_id})
```

USER 路径从不依赖 Entangled 兜底，所以永远没事。`AGENT_REPLY` 路径（通用 CRUD 代理）因为偷懒走兜底，踩了雷。

### 设计判定

Entangled 这条兜底路径，本意是给**单例实体**准备的：`id_field == key_params[0]`，意思就是"这个实体按 scope-key 做主键（每个 agent 一行）"。符合此模式的只有三个：

| 实体 | id_field | key_params[0] |
| --- | --- | --- |
| `AGENT_BINDING_DEF` | `agent_id` | `agent_id` |
| `AGENT_TOOLS_DEF` | `agent_id` | `agent_id` |
| `AGENT_STATE_DEF` | `agent_id` | `agent_id` |

**但其实这三个根本用不着 fallback**：`_sql_create` / `append` 最开头有段"scope-key-copy"循环：

```python
if params:
    for kp in defn.key_params:
        if kp in params and kp not in row:
            row[kp] = params[kp]
```

对 `AGENT_TOOLS_DEF`（`key_params = ["agent_id"]`, `id_field = "agent_id"`），这段循环会在 fallback 之前就把 `row["agent_id"] = params["agent_id"]` 填好，`res_id = row.get(defn.id_field, "")` 已经是 `"agent_id"` 值，完全不进 fallback 分支。

所以**整个 fallback 块其实从一开始就没有合法用例**。它只服务于两种场景：
1. 调用方漏填 id（应该 fail-fast 而不是兜底）
2. scope-key-coercion 这个 bug 本身（应该删除而不是保留）

## 修复方案（fail-fast，拒绝 fallback）

### A. Entangled：删除 fallback，改 fail-fast

`_sql_create` 和 `append` 两处完全相同的 fallback 块，替换为一个 loud `ValueError`：

```python
if not res_id and not is_auto_int:
    raise ValueError(
        f"missing required '{defn.id_field}' on entity="
        f"'{defn.name}': caller must provide a value. "
        f"Entangled does not mint ids for non-auto-int "
        f"primary keys (PR-40 fail-fast)."
    )
```

副作用清理：`import uuid` 在 `entity_store.py` 删除（再无引用）。

### B. `_exec_chat_reply`：显式填 id（和 USER 路径对齐）

```python
import uuid as _uuid
...
gw.entity_create("messages", {
    "id": _uuid.uuid4().hex[:12],
    "type": "AGENT_REPLY",
    ...
}, params={"agent_id": deps["agent_id"]})
```

格式故意跟 `business/message_actions._store_add_message` 一致（都是 `uuid4().hex[:12]`），两个写消息的路径收敛到一个 shape。

### C. Audit：现存所有 TEXT 主键的 `create/append` 调用方

全仓 `rg` + 手工审计结果 —— **唯一违规者就是 `_exec_chat_reply`**，其它调用方都已显式填 id：

| 调用方 | 状态 |
| --- | --- |
| `business/message_actions._store_add_message` | ✅ `_uuid.uuid4().hex[:12]` |
| `gateway/files/registry.py:register_file` | ✅ `"f_" + uuid.uuid4().hex[:12]` |
| `business/model_actions.py` (3 处) | ✅ `str(_uuid.uuid4())` |
| `business/api_key_actions.add_action` | ✅ 显式 `key_id` |
| `business/internal/subagent*.py` (3 处 `create("subagents")`) | ✅ 显式 `subagent_id` |
| `business/internal/agent.py:create("agent-memory")` | ✅ 显式 `key` |
| `novaic-device/device/devices.py:_store_create` | ✅ `device.id` |
| singleton 家族（`agent-tools` / `agent-state` / `agent-binding`） | ✅ 走 scope-key-copy 循环填 id，fallback 从不触发 |
| INTEGER 自增家族（`execution-logs` / `agent-tasks` / `agent-notebook` / `log-payloads`） | ✅ `is_auto_int` 分支短路 |
| **`_exec_chat_reply`** | ❌ **唯一违规者 → 本 PR B 节修复** |

所以 A（Entangled 删 fallback）+ B（chat_reply 填 id）两笔改动就足够封闭所有现有调用方。未来新调用方漏填 id → `ValueError` 当场报错，再也没有静默兜底。

### D. 回归测试

**D1 — Entangled 侧 `tests/test_id_fallback_scope_key.py`**（5 cases）：

| 测试 | 断言 |
| --- | --- |
| `test_stream_entity_without_id_raises_value_error` | 流式实体漏填 id → `ValueError`，错误消息含 `entity='messages'` / `missing required 'id'` / `PR-40` |
| `test_stream_entity_with_caller_minted_id_succeeds` | 显式填 id → 正常写入，两条记录 id 独立 |
| `test_singleton_entity_still_uses_scope_key_as_id` | `agent-tools` 依赖 scope-key-copy 路径，不填 id 仍成功（锁定未回归） |
| `test_integer_autoincrement_id_unaffected` | INTEGER id 继续自增 |
| `test_error_message_names_the_entity_and_field` | 错误消息 grep-friendly（含实体名、字段名、"does not mint"）|

**D2 — agent-runtime 侧 `test_tool_handlers_chat_reply.py`**（新增 1 case）：

| 测试 | 断言 |
| --- | --- |
| `test_chat_reply_mints_its_own_id` | 连发两条 chat_reply → body 必含 `id`，两个 id 都是 hex12 shape（`^[0-9a-f]{12}$`），互不相等，且都不等于 `agent_id`（回归守卫） |

### E. 脏数据处理

生产 DB 里那一条 `id == agent_id == "415f6cfd4e5b4a04911b66cb8ab2cad7"` 的旧 AGENT_REPLY 行：

- 不影响查询（API 按 `agent_id` 过滤，仍能正确返回）。
- **建议保留不动**，当考古痕迹；用 `SELECT id FROM chat_messages WHERE id = agent_id` 任何时候能溯源到"PR-40 之前被兜底路径污染的消息"。
- 如果洁癖党介意，可单独起一个 one-shot 脚本改 id。本 PR 不包含。

## 子 PR

| # | Repo | Branch | 内容 |
|---|---|---|---|
| 1 | `Entangled` | `fix/id-fallback-fail-fast` | A：`_sql_create` + `append` 的 fallback 块换成 `ValueError` + 删 `import uuid` + D1 测试文件 |
| 2 | `novaic-agent-runtime` | `fix/chat-reply-explicit-id` | B：`_exec_chat_reply` 显式 `_uuid.uuid4().hex[:12]` + D2 测试 |
| — | 主仓 | `fix/chat-reply-unique-collision-40` | 两个 submodule bumps + HANDOVER 追记 |

**Merge 顺序**：1 和 2 可并行（互不依赖）。两个都 merge 后主仓 bump。

## 验收

- `pytest Entangled/packages/server-python/tests/` 全绿（**105/105**，+1 新）
- `pytest novaic-agent-runtime/tests/` 全绿（**72/72**，+1 新）
- `pytest novaic-business/tests/` 全绿（**74/74**，不回归）
- `ReadLints` 干净
- 生产验证：部署后用户连发 3 条消息，prod `task-worker-execution-*.log` 不再出现 `UNIQUE constraint failed: chat_messages.id`；`sqlite3 entangled.db "SELECT id, type FROM chat_messages WHERE agent_id='...' AND type='AGENT_REPLY' ORDER BY timestamp DESC"` 新行 id 都是 12 位 hex，`id != agent_id`。
- `HANDOVER.md` 追一条 `2026-04-21：PR-40 —— Entangled id-fallback 删除（fail-fast），chat_reply 显式填 id`。

## 回滚

- Entangled：`git revert <commit>` 恢复 fallback 块。chat_reply 继续运行（因为 B 节已经显式填 id，不依赖兜底）。回滚后只是"漏填 id 的其它调用方"继续静默兜底。
- agent-runtime：`git revert <commit>` 会让 `_exec_chat_reply` 重新漏填 id → Entangled 立刻 `ValueError` → `chat_reply` 工具报错。所以 **agent-runtime 的回滚前提是 Entangled 也先回滚**。文档在此记明耦合。

无 schema migration，无数据迁移。

## 架构判定沉淀

- **"无静默失败" 高于 "使用方便"**：一个看似"智能自愈"的 fallback，长期来看制造的 bug 远多于省掉的几行样板代码。PR-40 删掉后，任何漏填 id 的调用方第一次压测就会 `ValueError` 砸脸，消灭潜雷成本从 "线上 debug 几小时" 降到 "CI 第一次跑就红"。
- **通用 CRUD 代理的契约是"caller 显式一切"**：id / timestamp / 其它 NOT NULL 字段 —— 全部由调用方提供。Entangled 只做 runtime-fill-default（PR-35）和 runtime-required-check（PR-35），不做"猜你想要什么"。
- **隐式行为必须有显式触发器**：singleton 实体（`id_field == key_params[0]`）依赖 scope-key-copy 拿到 id，这是"显式"的 —— 因为 caller 传了 `params[key_params[0]]`。被删掉的兜底 `params.get(defn.key_params[0])` 则是"隐式"的 —— 它利用了"scope-key 顺手读出来"这个凑巧。`agent-tools` 等单例照常工作，证明 scope-key-copy 循环已经涵盖所有合法需求。
- **把隐患一次扫干净**：`SUBAGENTS_DEF` / `AGENT_SKILLS_DEF` / `AGENT_MEMORY_DEF` / `API_KEY_MODELS_DEF` 这几个 `id_field != key_params[0]` 的实体，PR-40 合了之后它们的调用方若有漏填 id 会立刻爆 `ValueError`，再也不会有第二个"chat_reply stuck after one reply"式的慢性症状。
