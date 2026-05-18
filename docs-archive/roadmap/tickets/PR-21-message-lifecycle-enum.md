# PR-21  `chat_messages.lifecycle` 枚举 + `state_transition()` 唯一入口

> Historical ticket archive: this closed ticket/review may mention retired paths such as `message_outbox`, `SPAWN_SUBAGENT`, or removed subagent tools. Do not use it as current architecture or backlog; see `docs/roadmap/message-wake-refactor.md`, `docs/roadmap/agent-perception-action-architecture.md`, and `docs/roadmap/tickets/PR-210-maintenance-tail-cleanup.md`.


| 字段 | 值 |
| --- | --- |
| **Phase** | 3 |
| **Milestone** | M3 |
| **承诺** | R4 + R8 |
| **Status** | `[x]` (merged; see roadmap README index) |
| **Depends on** | PR-14 |
| **Blocks** | PR-22, PR-25, PR-26, PR-30 |
| **估时** | 1 d |
| **Owner** | __ |
| **PR 标题** | `feat(entangled): chat_messages.lifecycle enum + message_state.transition()` |

## 目标

把消息状态从"五字段拼凑"收敛为一个权威状态机，解决 hihi 事件"消息卡在哪看不出来"的诊断盲区。

## 范围

- Entangled schema `chat_messages.json`
- Entangled 写入 handler
- 新增模块：`novaic-entangled/entangled/message_state.py`（或等价位置）

## 前置 Checklist

- [ ] PR-14 `message_outbox` 已就位
- [ ] 确认 `chat_messages` 表当前的状态字段：`read / processed / claimed_by / claimed_at / status`

## 实施 Checklist

### 1. 加字段（保留旧字段一个 release）

- [ ] Schema 增加列：
  ```sql
  ALTER TABLE chat_messages
    ADD COLUMN lifecycle TEXT NOT NULL DEFAULT 'pending'
      CHECK (lifecycle IN ('pending','claimed','consumed','orphaned','deduped'));
  ALTER TABLE chat_messages
    ADD COLUMN claimed_by_scope TEXT;   -- replaces claimed_by semantics
  ALTER TABLE chat_messages
    ADD COLUMN lifecycle_updated_at INTEGER;
  ```
- [ ] 旧字段 `read/processed/claimed_by/claimed_at/status` 保留**至少一个 release**（观察期 + 回滚余地）

### 2. 状态机唯一入口

```python
# entangled/message_state.py
ALLOWED_TRANSITIONS = {
    "pending":   {"claimed", "deduped"},
    "claimed":   {"consumed", "orphaned"},
    "consumed":  set(),              # terminal
    "orphaned":  {"claimed"},         # recovery can re-claim
    "deduped":   set(),              # terminal
}

def transition(conn, message_id: str, *, to: str, scope_id: str | None = None, reason: str = ""):
    row = conn.execute("SELECT lifecycle FROM chat_messages WHERE id=?", (message_id,)).fetchone()
    if not row:
        raise ValueError(f"message not found: {message_id}")
    cur = row["lifecycle"]
    if to not in ALLOWED_TRANSITIONS.get(cur, set()):
        raise InvalidTransition(f"{cur} -> {to} not allowed for {message_id}")
    now = int(time.time() * 1000)
    conn.execute("""
        UPDATE chat_messages
           SET lifecycle = ?, claimed_by_scope = COALESCE(?, claimed_by_scope),
               lifecycle_updated_at = ?
         WHERE id = ?
    """, (to, scope_id, now, message_id))
    logger.info("message_state %s: %s -> %s scope=%s reason=%s", message_id, cur, to, scope_id, reason)
    metrics.incr("message_transitions_total", labels={"from": cur, "to": to})
```

### 3. 迁移现有数据

- [ ] 迁移脚本推断初始 lifecycle：
  ```sql
  UPDATE chat_messages
     SET lifecycle = CASE
         WHEN processed = 1 THEN 'consumed'
         WHEN claimed_by IS NOT NULL THEN 'claimed'
         ELSE 'pending'
     END,
     claimed_by_scope = claimed_by,
     lifecycle_updated_at = strftime('%s','now')*1000
   WHERE lifecycle = 'pending';   -- idempotent
  ```

### 4. 禁止旁路

- [ ] 在 `message_state.py` 顶部加注释，明确"唯一写入入口"
- [ ] 加一条 CI lint（类似 PR-03）：禁止业务代码直接 `UPDATE chat_messages SET lifecycle`（allowlist: `message_state.py`, `tests/`, `migrations/`）

## 测试 Checklist

- [ ] 单测覆盖所有 allowed 转移
- [ ] 单测：非法转移 raise `InvalidTransition`
- [ ] 单测：不存在的 message_id raise `ValueError`
- [ ] 迁移脚本幂等

## 可观测性 Checklist

- [ ] metric `message_transitions_total{from, to}` counter
- [ ] log：每次 transition 打一行带 `message_id / from / to / scope_id / reason`

## 文档 Checklist

- [ ] [message-wake-refactor.md](../message-wake-refactor.md) P3-2 → `[x]`
- [ ] 本工单 Status → `[x]`
- [ ] [architecture/entity-data-models.md](../../architecture/entity-data-models.md) 更新 `chat_messages` 字段表
- [ ] [message-wake-principles.md](../../architecture/message-wake-principles.md) §R4 的状态图与代码对齐

## 验收命令

```bash
sqlite3 ~/.novaic/data/entangled.db "PRAGMA table_info(chat_messages);" | rg 'lifecycle|claimed_by_scope'
# 应看到新字段

python -c "
from entangled.message_state import transition, ALLOWED_TRANSITIONS
print(ALLOWED_TRANSITIONS)
"
```

## 回滚

- Revert 代码 + 保留新列（不强制删列，DEFAULT='pending' 无副作用）
- 若必须回滚 schema：`ALTER TABLE DROP COLUMN lifecycle ...`（sqlite 需要重建表）

## 备注

- 旧字段一并兼容读取（避免破坏现有 API），但**禁止新代码写**旧字段。
- PR-30 在稳定 1 release 后删旧字段。
