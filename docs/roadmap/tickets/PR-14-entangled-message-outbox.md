# PR-14  Entangled `message_outbox` schema + 同事务插入

| 字段 | 值 |
| --- | --- |
| **Phase** | 2（主路径切换） |
| **Milestone** | M2 |
| **承诺** | R6 |
| **Status** | `[ ]` |
| **Depends on** | — |
| **Blocks** | PR-15, PR-16, PR-21 |
| **估时** | 1 d |
| **Owner** | __ |
| **PR 标题** | `feat(entangled): message_outbox table + co-transaction insert on chat_messages write` |

## 目标

为 Entangled 的 `chat_messages` 建立 outbox / changefeed。写消息时同事务插 outbox 行，让 subscriber（PR-15/16）能可靠地消费。

## 范围

- `novaic-entangled/<schema>/messages.json`（或对应 schema 定义）
- Entangled 写入 handler（写 `chat_messages` 处追加 outbox insert）
- 迁移 schema push（版本号 +1）

## 前置 Checklist

- [ ] 决策记录：选 **outbox 表 + poller** 方案（已在 `message-wake-refactor.md` P2-1 记录）
- [ ] 确认当前 Entangled 写入 `chat_messages` 的全部入口（通常只有 1-2 个 handler）

## 实施 Checklist

### Schema

- [ ] 新增表：
  ```sql
  CREATE TABLE IF NOT EXISTS message_outbox (
      id INTEGER PRIMARY KEY AUTOINCREMENT,
      message_id TEXT NOT NULL UNIQUE,
      agent_id TEXT NOT NULL,
      trigger_type TEXT NOT NULL,          -- 存 TriggerType.value
      payload_json TEXT NOT NULL,          -- 供 subscriber 直接取 (含 message_ids / metadata)
      created_at INTEGER NOT NULL,         -- unix ms
      delivered_at INTEGER,                -- NULL 表示未投递
      attempts INTEGER NOT NULL DEFAULT 0,
      last_error TEXT,
      locked_by TEXT,                      -- subscriber worker_id; NULL when free
      locked_until INTEGER                 -- unix ms; fencing expiry
  );

  CREATE INDEX idx_outbox_undelivered ON message_outbox (delivered_at, locked_until, id)
      WHERE delivered_at IS NULL;
  ```

- [ ] Schema 版本号 +1，迁移脚本包含 `CREATE TABLE IF NOT EXISTS`

### 同事务插入

- [ ] 在 `chat_messages` 写入路径（entity_store / handler）：
  ```python
  with conn:                      # sqlite 事务
      conn.execute("INSERT INTO chat_messages ...")
      conn.execute("""
          INSERT INTO message_outbox (message_id, agent_id, trigger_type, payload_json, created_at)
          VALUES (?, ?, ?, ?, ?)
          ON CONFLICT(message_id) DO NOTHING
      """, (msg_id, agent_id, trigger_type, json.dumps(payload), now_ms))
  ```
- [ ] 决策：**只对"能触发 wake"的消息类型写 outbox**（`USER_MESSAGE / SUBAGENT_SEND / SPAWN_SUBAGENT`），过滤掉纯 assistant reply
- [ ] `trigger_type` 从消息类型推导：
  ```python
  MSG_TO_TRIGGER = {
      "USER_MESSAGE": "user_message",
      "SUBAGENT_SEND": "subagent_send",
      "SPAWN_SUBAGENT": "spawn_subagent",
  }
  ```

### 不做

- [ ] 本 PR **不**实现消费 → outbox 只会积累行，delivered_at 恒 NULL（这是预期）
- [ ] 不接入 subscriber（PR-15/16）

### 保留期

- [ ] 约定：`delivered_at IS NOT NULL` 超过 7 天可清理；维护脚本在 PR-16 附带

## 测试 Checklist

- [ ] 单测（Entangled）：
  - 写 USER_MESSAGE → `chat_messages` + `message_outbox` 各一行
  - 写 assistant reply（不触发 wake）→ `chat_messages` 一行，`message_outbox` 无变化
  - 并发写 100 条 → outbox 100 行（UNIQUE on message_id 保护）
- [ ] 集成：本地发 `hihi` → `SELECT * FROM message_outbox WHERE delivered_at IS NULL;` 应有 1 行

## 可观测性 Checklist

- [ ] metric `outbox_enqueued_total{trigger_type}` counter（每次 insert outbox 打一次）
- [ ] metric `outbox_backlog_count` gauge（周期性 `COUNT(*) WHERE delivered_at IS NULL`），由后续 subscriber / scheduler 定时刷
- [ ] log：`outbox_enqueue message_id=... agent=... trigger=...`

## 文档 Checklist

- [ ] [message-wake-refactor.md](../message-wake-refactor.md) P2-2 → `[x]`
- [ ] 本工单 Status → `[x]`
- [ ] 在 [entangled/README.md](../../entangled/README.md) 加一节 "Message outbox（服务端 changefeed）"
- [ ] 在 [message-wake-principles.md](../../architecture/message-wake-principles.md) §R6 引用本 schema

## 验收命令

```bash
sqlite3 ~/.novaic/data/entangled.db ".schema message_outbox"
# 应看到 CREATE TABLE 定义

./scripts/reset-agent-data.sh
# 发一条 USER_MESSAGE 后：
sqlite3 ~/.novaic/data/entangled.db \
  "SELECT id, message_id, agent_id, trigger_type, delivered_at FROM message_outbox ORDER BY id DESC LIMIT 5;"
# 应有一条，delivered_at=NULL
```

## 回滚

- Schema rollback 困难但可接受："DROP TABLE message_outbox" + schema 版本号 -1。
- 本 PR 合并后，outbox 仅积累不消费；即使不回滚也不影响既有功能（HealthWorker 兜底路径仍在 PR-12 后工作）。

## 备注

- **关键**：co-transaction 必须真正同事务。如果 Entangled 用 sqlite WAL，`conn.execute ... conn.execute` 包在同一 `with conn` 即可。
- **不**把 payload_json 展开成多列；subscriber 直接反序列化使用更灵活。
- `locked_by` / `locked_until` 现在就加，PR-16 的 multi-subscriber 抢占会用到。
