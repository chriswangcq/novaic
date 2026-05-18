# PR-30  删除 `chat_messages` 旧状态字段

| 字段 | 值 |
| --- | --- |
| **Phase** | 5 |
| **Milestone** | M4 |
| **承诺** | R4 + R8 |
| **Status** | `[x]` (2026-04-15, 窄化：保留 `read`) |
| **Depends on** | PR-21, PR-22, PR-23（稳定 ≥ 1 release） |
| **Blocks** | — |
| **估时** | 0.5 d |
| **Owner** | @wangchaoqun |
| **PR 标题** | `refactor(entangled): drop chat_messages legacy dispatch columns (processed/claimed_by/claimed_at/status)` |

## 目标

在 `lifecycle` 字段稳定运行 ≥ 1 个 release 后，彻底删旧字段，结束"双字段维护"成本。

## 范围

- Entangled schema `chat_messages.json`
- 所有读旧字段的代码路径
- 迁移脚本（sqlite `ALTER TABLE ... DROP COLUMN`，需要 3.35+）

## 前置 Checklist

- [ ] PR-21 / PR-22 / PR-23 稳定运行 ≥ 1 release（建议 2 周以上）
- [ ] `rg 'processed|read|claimed_by|claimed_at|\.status' novaic-*/ | rg 'chat_messages' | rg -v 'lifecycle|tests|migrations'` 清点
- [ ] **生产 DB 备份**

## 实施 Checklist

### 1. 代码清理

- [ ] 所有读 `processed` / `read` / `claimed_by` / `claimed_at` / `status`（对 chat_messages）的代码改读 `lifecycle` / `claimed_by_scope`
- [ ] 删除向旧字段写的所有代码
- [ ] 删除读旧字段的 API 响应体字段（或保留只读兼容一个 release）

### 2. Schema 变更

- [ ] sqlite 3.35+ 支持 `ALTER TABLE ... DROP COLUMN`：
  ```sql
  ALTER TABLE chat_messages DROP COLUMN processed;
  ALTER TABLE chat_messages DROP COLUMN read;
  ALTER TABLE chat_messages DROP COLUMN claimed_by;
  ALTER TABLE chat_messages DROP COLUMN claimed_at;
  ALTER TABLE chat_messages DROP COLUMN status;
  ```
- [ ] 若 sqlite < 3.35 → 必须用 "CREATE NEW TABLE + INSERT SELECT + DROP + RENAME" 的五步法
- [ ] Schema 版本号 +1

### 3. 观察窗

- [ ] 合并后观察 24h：无 `column not found` / 字段 KeyError

## 测试 Checklist

- [ ] 单测：所有读/写 `lifecycle` 的代码继续工作
- [ ] 集成：发消息 → 生命周期完整
- [ ] 迁移脚本在一份 snapshot DB 上跑 → 剩余字段正确

## 可观测性 Checklist

- n/a（仅清理）

## 文档 Checklist

- [ ] [message-wake-refactor.md](../message-wake-refactor.md) P5-4 → `[x]`
- [ ] 本工单 Status → `[x]`
- [ ] [architecture/entity-data-models.md](../../architecture/entity-data-models.md) 删除旧字段条目

## 验收命令

```bash
sqlite3 ~/.novaic/data/entangled.db "PRAGMA table_info(chat_messages);"
# 不再包含 processed/read/claimed_by/claimed_at/status

rg '\.processed|\.claimed_by\W' novaic-*/ | rg -v lifecycle | rg -v 'tests/|migrations/'
# 预期：空
```

## 回滚

- **危险**：DROP COLUMN 不可逆。若需要回滚：
  1. 从生产 DB 备份恢复
  2. revert 代码

## 备注

- 一定要等 ≥ 1 release 稳定再做；过早会让老客户端 / 老代码崩溃。
- 本 PR 应在周初合并 + 当周密切观察。

---

## 实施总结（2026-04-15）

### 范围窄化

原工单把 `read` 列为"legacy"，实际 `read` 是用户侧未读回执（unread 徽章），与 `lifecycle`（dispatch 状态机）不是同一维度：

| 列 | 原始意图 | 现状 | 本 PR 处理 |
| --- | --- | --- | --- |
| `processed` | 消息已被 worker 消费 | 被 PR-21 `lifecycle in ('consumed')` 取代 | **DROP** |
| `claimed_by` | worker id（模糊字符串） | 被 PR-21 `claimed_by_scope`（Cortex scope_id）取代 | **DROP** |
| `claimed_at` | 领取时间戳 | 被 PR-21 `lifecycle_updated_at` 取代 | **DROP** |
| `status` | 旧 dispatch 状态 | 生产 145 行里 108 行是脏值 `'0'`、37 行是默认 `'sent'` | **DROP** |
| `read` | 用户未读标记 | 依然在用（`entity_list(filters={"read":0})`、`entity_update({"read":1})`） | **保留** |

因此本 PR 只删前四列，`read` 单独留给后续（必要时另开 PR-30b 重设计 unread 语义）。

### 代码改动

1. **迁移 helper**：`Entangled/.../entangled/sql/message_state.py`
   - 新增 `LEGACY_COLUMNS = ("processed", "claimed_by", "claimed_at", "status")` 常量。
   - 新增 `drop_legacy_message_columns(db) -> list[str]`：逐列 `ALTER TABLE chat_messages DROP COLUMN`，幂等（已删过则返回空列表）。

2. **自动在 `ensure_schema` 中跑迁移**：`Entangled/.../entangled/sql/entity_store.py`
   - 原来只跑 `backfill_lifecycle`；现在在 backfill **之后**再跑 `drop_legacy_message_columns`。
   - 顺序不可交换：backfill 依赖读 `processed` / `claimed_by` 把 pre-PR-21 行推进 lifecycle。
   - 幂等：第二次 `ensure_schema`（服务重启）是 noop。

3. **Schema 定义清理**：`novaic-business/business/schema_push.py`
   - 从 `MESSAGES_DEF.fields` 里删掉四条 `F.*(...)` 行，加文档注释解释原因。

4. **Row writer 清理**：5 处写入 `chat_messages` 的 Python 路径
   - `business/internal/message.py::_store_add_message` —— 删 `status=` 形参和 `"status": status`
   - `business/message_actions.py::_store_add_message` —— 同上
   - `business/agent_actions.py::_store_add_message` —— 同上
   - `business/internal/subagent.py`（两处 inline `store.append("messages", ...)`）—— 删 `"status": "sent"`
   - `business/internal/agent.py::_store_add_message` —— 同上
   - `novaic-agent-runtime/task_queue/handlers/tool_handlers.py`（chat_reply AGENT_REPLY 写入）—— 删 `"status": "sent"`

5. **Reader 清理**：`novaic-agent-runtime/task_queue/handlers/context_handlers.py`
   - 原本 `entity_list(params={..., "status": "sent"})` 作为未读拉取的过滤条件 —— 列删了之后这个过滤永远为假，会把所有新消息全部漏掉。
   - 改为只按 `{"read": "0"}` 过滤，语义不变（本来就是按"未读 + 类型"在 Python 侧二次筛选）。

6. **API 响应字段**：`business/message_actions.py::send_action`
   - 响应体原本包 `"status": "sent"` —— 客户端侧 grep 无任何依赖。
   - 改为 `"lifecycle": "pending"`，保留字段为前端可能的状态指示用。

### 测试

- **新增 3 个单测**（`Entangled/.../tests/test_message_state.py`）：
  1. `test_ensure_schema_runs_backfill_then_drops_legacy_columns` —— 端到端：预置 `processed=1` 行 → `ensure_schema` → lifecycle 变成 `consumed` AND 四个列都已 drop。
  2. `test_drop_legacy_message_columns_is_idempotent` —— 第二次调用返回空列表，不报"no such column"。
  3. `test_drop_legacy_preserves_lifecycle_and_read_columns` —— 确认 `read` 和 PR-21 新列存活。
- **改造现有 fixture**：`test_message_state.py::store` 不再走 `store.ensure_schema` 自动建表（因为这会触发 drop hook 在测试插入 legacy 行之前就把列删掉），改为手写 `CREATE TABLE` + `register`；只有一个 end-to-end 测试显式调 `ensure_schema`。
- **修业务侧测试**：`novaic-agent-runtime/tests/unit/task_queue/test_tool_handlers_chat_reply.py::test_chat_reply_body_shape_is_stable` 原本断言 `body["status"] == "sent"`，改为断言 `"status" not in body and "lifecycle" not in body`（row writer 不再写这些列，Entangled 默认 lifecycle='pending'）。
- **Entangled message 相关测试**：`tests/test_message_state.py / test_outbox_insert.py / test_outbox_schema_bootstrap.py / test_orphans.py / test_message_trace.py` 全绿（53/53）。
- **Business 全套测试**：75/75 绿（跳过 `test_schema_invariants.py`，缺依赖与本 PR 无关）。

### CI Lint

新增 `scripts/ci/lint_legacy_message_columns.sh`（接入 `.github/workflows/lint.yml`），禁止：
- 任何 `F.text("claimed_by"|"claimed_at")` / `F.int_("processed")` 形式的 schema 声明；
- 任何 `"processed": 0|1` / `"claimed_by": "..."` / `"claimed_at": "..."` / `"status": "sent"` 形式的 row literal（`"status"` 只卡 `"sent"` 这一个值，以免误伤 subagents/drafts/agent_records 等其他 entity 合法使用的 `status` 列）。

允许列表：Entangled 迁移代码、`tests/`、`docs/`、本脚本自身。

### 不变量

- **INV-7**（新增）：*每一行 `chat_messages` 的 dispatch 状态由且仅由 `lifecycle` 列承载。四个 legacy 列不再存在于生产 schema，任何重新引入都会被 CI lint 拦截。*

### 生产迁移安全性

- sqlite 3.45（生产）原生支持 `ALTER TABLE ... DROP COLUMN`，单语句即删，无需五步法。
- 部署流程：代码上线 → Entangled 服务重启 → `ensure_schema` 跑 → backfill（24 行 `pending` + 108 行 `processed=1` → 118 consumed）→ drop 四列 → 观测 orphan-scan 指标正常。
- 回滚：代码 revert，**数据不可回滚**。但 `lifecycle` 已经是权威列，旧代码 revert 回去会回到 pre-PR-21 读 `processed`——这个路径在 pre-PR-21 数据上仍能工作（只是会少看到 PR-21 之后的新行，因为它们没写 `processed`）。做 PR-30 deploy 前必须有 DB 备份。
