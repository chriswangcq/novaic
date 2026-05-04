# PR-41  `AGENT_REPLY` 等非 wake-trigger 消息不应进入 orphan 候选（止血）

> Historical ticket archive: this closed ticket/review may mention retired paths such as `message_outbox`, `SPAWN_SUBAGENT`, or removed subagent tools. Do not use it as current architecture or backlog; see `docs/roadmap/message-wake-refactor.md`, `docs/roadmap/agent-perception-action-architecture.md`, and `docs/roadmap/tickets/PR-210-maintenance-tail-cleanup.md`.


| 字段 | 值 |
| --- | --- |
| **Phase** | hotfix（HealthWorker 误恢复循环 — 自动苏醒） |
| **Milestone** | — |
| **承诺** | R4 + R8（lifecycle 语义闭合）+ 止血 |
| **Status** | `[x]` 实施完成（2026-04-21） |
| **Depends on** | PR-21（`chat_messages.lifecycle` 枚举）、PR-26（orphan 扫描端点） |
| **Blocks** | — |
| **估时** | 0.5 d |
| **Owner** | __ |
| **PR 标题** | `fix(entangled+business): non-trigger chat_messages land in lifecycle=consumed so they never orphan-loop` |

## 事件摘要

生产现场：某 agent 每隔 ~5 分钟自动苏醒一次，`wake_at=NULL`，用户未主动发消息。

`queue-service` 日志呈固定周期：

```
dispatch started caller=runtime-recovery trigger=recovered ...
```

`HealthWorker` 的 `service_name="runtime-recovery"`（见 PR-27）。即是 **orphan re-dispatch 在周期性误报**。

**DB 现场**（生产 `/opt/novaic/data/entangled.db`）：

```sql
SELECT id, type, lifecycle, created_at
  FROM chat_messages
 WHERE lifecycle='pending' AND type='AGENT_REPLY'
 ORDER BY created_at DESC LIMIT 5;
-- 7e569102a31f... | AGENT_REPLY | pending | 2026-04-21T12:58:36.307Z
-- ...多条同样形态
```

对应 outbox：

```sql
SELECT COUNT(*) FROM message_outbox
 WHERE message_id IN (SELECT id FROM chat_messages WHERE type='AGENT_REPLY');
-- 0
```

`AGENT_REPLY` 行全部 `lifecycle='pending'` 且没有 `message_outbox` 伴随行。

## 根因

### 1. 写入侧：`AGENT_REPLY` 不在 outbox_trigger_types

`novaic-business/business/schema_push.py::MESSAGES_DEF` 只声明了 3 个触发类型：

```python
outbox_trigger_types={
    "USER_MESSAGE":   "user_message",
    "SUBAGENT_SEND":  "subagent_send",
    "SPAWN_SUBAGENT": "spawn_subagent",
},
```

`Entangled/.../entity_store.py::append` 的 co-transaction 插入逻辑 (≈line 615)：

```python
if defn.outbox_trigger_types:
    msg_type = row.get("type", "")
    trigger_value = defn.outbox_trigger_types.get(msg_type)
    if trigger_value:
        # 只有在映射里才插 outbox 行
        ...
```

**但 `chat_messages.lifecycle` 的默认值是 `'pending'`**（schema_push.py line ~410 的 `DEFAULT 'pending'`），对所有 type 生效。于是 `AGENT_REPLY` 行诞生即 `pending` 且**永远没人去 transition 它**（subscriber 按 outbox 工作，outbox 里没这条）。

### 2. 读取侧：orphan 扫描不按 type 过滤

`Entangled/.../app/orphans.py::query_orphans`（PR-26）SQL：

```sql
WHERE m.lifecycle = 'pending'
  AND COALESCE(m.lifecycle_updated_at, ...) < :cutoff_ms
```

不区分 type。5 分钟后 `AGENT_REPLY` 行自动变成 `severity=crit`。

### 3. HealthWorker：对 crit orphan 无脑 `RECOVERED` dispatch

`novaic-agent-runtime/task_queue/workers/health_worker.py::_maybe_recover`（PR-27）：

```python
result = self._get_assembler().assemble_and_dispatch_sync(
    TriggerType.RECOVERED, agent_id,
    message_ids=[message_id], ...)
```

→ 新 saga → `subagent_wake` → agent 被唤醒 → 再产出 `AGENT_REPLY` → 同样 pending → 5 分钟后再循环。

**自激周期 = `PENDING_CRIT_SEC`（默认 300s）**。

## 方案

**核心原则**：消息 type 与 lifecycle 语义对齐 —— "没有消费通道"的 type，**不应**出现 `pending` 状态，应当直接进入终态。

### 采纳方案 A：写入侧落入 `consumed`（主）

`Entangled/.../entity_store.py::append` 的 co-insert 段：

```python
# 当前（简化）
if defn.outbox_trigger_types:
    msg_type = row.get("type", "")
    if defn.outbox_trigger_types.get(msg_type):
        # 插 outbox，lifecycle 保持默认 pending
        ...

# 改为
if defn.outbox_trigger_types:
    msg_type = row.get("type", "")
    if defn.outbox_trigger_types.get(msg_type):
        # 正常路径：插 outbox + 保持 pending，等 subscriber claim
        ...
    else:
        # 非 trigger 类型：该行永远不需要 wake dispatch
        # → 写入时直接落 consumed，避免被 orphan scan 误报
        # lifecycle_updated_at 同事务内一起写，保证 PR-21 审计链完整
        cur.execute(
            f"UPDATE {defn.table} SET lifecycle='consumed', lifecycle_updated_at=? "
            f"WHERE {defn.id_field}=?",
            (int(time.time()*1000), entity_id_val),
        )
```

**为什么不让插入 SQL 直接 `DEFAULT 'consumed'`**：
- schema 级别的默认值需要按 type 条件，SQLite 没有"CASE-based default"；
- 要么所有消息默认 consumed（破坏 pending→claimed→consumed 的主路径语义），要么写入侧判断。选后者。

**为什么不改 `MESSAGES_DEF.lifecycle` 的默认值**：
- PR-21 的状态机明确"pending 是所有待消费消息的入口"。如果把默认改掉，`USER_MESSAGE` 也会受影响。
- 让 append 逻辑根据"当前这条消息有没有 outbox 消费者"决定落 pending / consumed，比改 schema 默认更精确。

### 配套方案 B：读取侧防御过滤（辅）

`orphans.py::query_orphans` SQL 增加：

```sql
WHERE m.lifecycle = 'pending'
  AND m.type IN ('USER_MESSAGE','SUBAGENT_SEND','SPAWN_SUBAGENT')  -- 新增
  AND COALESCE(m.lifecycle_updated_at, ...) < :cutoff_ms
```

类型列表的权威来源是 `MESSAGES_DEF.outbox_trigger_types`。端点签名保持不变（避免 HealthWorker 那侧连带改动）；从 `SqlEntityDef` 拿 keys 即可。

**双保险动机**：方案 A 解决根因，方案 B 保证即使将来新增非 trigger 类型忘了考虑（或存量脏数据），orphan 视图不会再把它们当 crit。

### 一次性清理存量脏数据

上线时执行迁移 SQL（写到 `novaic-business/business/migrations/` 或 schema push hook）：

```sql
UPDATE chat_messages
   SET lifecycle='consumed',
       lifecycle_updated_at=CAST(strftime('%s','now') AS INTEGER)*1000
 WHERE lifecycle='pending'
   AND type NOT IN ('USER_MESSAGE','SUBAGENT_SEND','SPAWN_SUBAGENT');
```

迁移完预期生产 `/orphans?min_age_sec=30` 返回 `count=0`（如果此时没有真实卡消息）。

## 范围

- `Entangled/packages/server-python/entangled/sql/entity_store.py`（append co-insert 分支）
- `Entangled/packages/server-python/entangled/app/orphans.py`（SQL 加 type 过滤）
- `novaic-business/business/schema_push.py`（可选：给 `outbox_trigger_types` 加个 `.keys()` 的 helper，让 orphans.py 能权威读到类型清单；或者 orphans.py 硬编码 3 类并加注释"与 MESSAGES_DEF.outbox_trigger_types 同步"）
- 迁移脚本：一次性 UPDATE 存量脏行

## 前置 Checklist

- [x] PR-21 `lifecycle` 状态机已生效（生产已 `[x]`）
- [x] PR-26 `/orphans` 端点已部署
- [x] 确认无其他 consumer 依赖 `type=AGENT_REPLY AND lifecycle=pending` 这种组合（grep `rg "lifecycle.*pending" --type py`）

## 实施 Checklist（2026-04-21 实施）

### 1. `entity_store.append` 写入侧分支 ✔

- [x] 定位 `append` 里 co-insert outbox 的 `if defn.outbox_trigger_types:` 块（line ≈ 604）
- [x] **实施方案修正**：相比 ticket 初稿"INSERT 后 UPDATE"，实际改为"INSERT 前在 `row` 里直接把 `lifecycle` 写成 `consumed`"。原因：
  1. 避免触发 `lint_lifecycle.sh` 的 "raw UPDATE chat_messages SET lifecycle" ban —— `entity_store.py` 不在 allowlist
  2. 不构成"状态机转换"（PR-21 `ALLOWED_TRANSITIONS` 里 `pending → consumed` 不合法），而是"出生即终态"，和 PR-21 契约对齐
  3. 不触发 `message_state_transitions` 日志（PR-31）—— 没发生转换，日志保持 signal-only
- [x] 保持幂等：caller 显式传 `lifecycle` 时尊重 caller（`"lifecycle" not in data` gate）
- [x] 单测（`tests/test_outbox_insert.py`）：
  - [x] `test_non_trigger_type_born_consumed`：`append(type=AGENT_REPLY)` → `lifecycle='consumed' lifecycle_updated_at=now_ms`，`message_outbox` 无行
  - [x] `test_trigger_type_keeps_pending_lifecycle`：`append(type=USER_MESSAGE)` → `lifecycle='pending' lifecycle_updated_at=NULL`（回归）
  - [x] `test_caller_provided_lifecycle_is_not_overridden`：`append(type=AGENT_REPLY, lifecycle='pending')` → 保持 `pending`

### 2. `orphans.py` 读取侧过滤 ✔

- [x] `query_orphans` SQL 加 `AND m.type IN (?,?,?)`
- [x] 模块常量 `ORPHAN_ELIGIBLE_TYPES = ('USER_MESSAGE','SUBAGENT_SEND','SPAWN_SUBAGENT')`，docstring 注明与 `MESSAGES_DEF.outbox_trigger_types` 同步关系
- [x] 单测（`tests/test_orphans.py`）：
  - [x] `test_agent_reply_never_appears_in_orphan_view`：插入 `type=AGENT_REPLY lifecycle=pending age=400s` → `count=0`
  - [x] `test_unknown_message_type_never_appears_in_orphan_view`：未来新类型默认 fail-closed
  - [x] `test_trigger_types_still_surface`：参数化回归
  - [x] `test_mixed_types_only_eligible_returned`：混入型 e2e
  - [x] `test_orphan_eligible_types_matches_messages_def`：同步 self-check（跨包导入不可用时 skip，交给 CI lint）
- [x] fixture `chat_messages` 表结构加 `type` 列；`_insert_msg` 默认 `type=USER_MESSAGE` 保持旧测例可运行

### 3. CI 同步 check ✔

- [x] `scripts/ci/lint_outbox_trigger_sync.sh`：提取两边 key，不一致则 fail（手测 drift 场景 exit=1 并打印两边清单）
- [x] 接入 `.github/workflows/lint.yml`（`Lint` job 末位新增 step "Run outbox-trigger sync lint (PR-41)"）

### 4. 迁移脚本 ✔

- [x] `scripts/gateway/migrate_pr41_agent_reply_orphans.sh`（allowlisted in `lint_lifecycle.sh`）
- [x] 功能：备份 → count → breakdown by type → 事务 UPDATE `lifecycle='consumed', lifecycle_updated_at=now_ms` WHERE `lifecycle='pending' AND type NOT IN (...)` → 校验残留=0
- [x] 无需 schema push 版本 bump —— 纯数据清理，运维手动执行

## 测试 Checklist

- [x] 单测（entangled）：type=AGENT_REPLY 插入 → lifecycle=consumed
- [x] 单测（entangled）：type=USER_MESSAGE 插入 → lifecycle=pending + outbox 行（回归）
- [x] 单测（entangled）：orphans SQL 过滤 type
- [x] 全量回归：Entangled 114 passed、novaic-business 74 passed、novaic-agent-runtime 72+16 passed
- [ ] 集成（runtime）：发一条消息让 agent 回复 → wait 6 分钟 → `HealthWorker._scan_and_recover_orphans` 一个 `RECOVERED` 都不触发（部署 staging 后验证）
- [ ] 回归（business）：`GET /internal/messages/orphaned` 在清理后返回 count=0（部署 staging 后验证）

## 可观测性 Checklist

- [ ] metric `orphans_total{severity=crit}` 在本 PR 上线后 24h 内归零（前提：生产无真实卡消息）
- [ ] log：不再出现 `caller=runtime-recovery trigger=recovered` 的周期性调用（除非有真实卡消息）
- [ ] runbook 更新：`docs/runbooks/troubleshooting.md` 加一条"`orphans_total` 忽然非零时，先用 `SELECT type, COUNT(*) FROM chat_messages WHERE lifecycle='pending' GROUP BY type;` 确认是否真实 trigger 类型卡住"

## 文档 Checklist

- [ ] [message-wake-refactor.md](../message-wake-refactor.md) 附录里加一条 "lifecycle × type 语义矩阵"
- [ ] 本工单 Status → `[x]`
- [ ] `docs/architecture/message-wake-principles.md` §"消息状态机"补注：**"pending"仅对 `outbox_trigger_types` 内的 type 合法**

## 验收命令

```bash
# 1) 生产上线后检查：orphan 清零
curl -s http://127.0.0.1:19998/internal/messages/orphaned?min_age_sec=30 | jq '.count'
# → 0

# 2) 确认写入侧生效
sqlite3 /opt/novaic/data/entangled.db \
  "SELECT lifecycle, COUNT(*) FROM chat_messages WHERE type='AGENT_REPLY' GROUP BY lifecycle;"
# → consumed | N
# → pending  | 0

# 3) 确认周期性误唤醒停止（观察 30 分钟）
tail -f /opt/novaic/logs/queue-service.log | rg 'caller=runtime-recovery'
# → 没有新行（除非真实卡消息）
```

## 部署 Checklist（必走，不部署不算完成）

> 血教训：2026-04-21 首轮代码完成后没部署，bug 又在夜里复现多次。此段强制每张票闭环。

- [ ] **本地代码已合入 main**：`git log --oneline origin/main | rg PR-41`
- [ ] **Entangled 子模块已同步**：父仓库的 submodule ref 已 bump 并推到远端
- [ ] **已 deploy**：在父仓库根 `./deploy gateway`（同步 Entangled + novaic-gateway + novaic-common，远端 `start.sh --stop && start.sh`）
- [ ] **已跑一次性迁移**（**仅一次、带备份**）：
      ```
      ssh api.gradievo.com \
        "bash /opt/novaic/services/novaic-gateway/scripts/gateway/migrate_pr41_agent_reply_orphans.sh /opt/novaic/data/entangled.db"
      ```
      （备份文件会自动落在 `/opt/novaic/data/entangled.db.backup_before_pr41_<ts>`）
- [ ] **线上证据 1 — 写侧**：`ssh api.gradievo.com 'sqlite3 /opt/novaic/data/entangled.db "SELECT lifecycle,COUNT(*) FROM chat_messages WHERE type=\"AGENT_REPLY\" GROUP BY 1"'` 无 `pending` 行
- [ ] **线上证据 2 — 读侧**：`ssh api.gradievo.com 'tail -200 /opt/novaic/logs/queue-service.log | grep caller=runtime-recovery'` 在 30 分钟静默后无 `AGENT_REPLY` 条目
- [ ] **线上证据 3 — 指标**：`curl -s https://api.gradievo.com/metrics | rg 'orphans_total|recovery'`（severity=crit 标签在静默期应持平 0）
- [ ] 把上述三段 paste 进 PR 关单评论

## 回滚

- Entangled + Business 两侧改动独立：回滚任意一侧都能工作
- 脏数据迁移是幂等 UPDATE，回滚无害
- 若回滚，自激循环会重现；这是可接受的短期状态

## 备注

- 本 PR 是"止血"；但它也揭示了 PR-21 状态机设计的一个隐性假设："所有 pending 消息最终都会有消费者"。这个假设成立的前提是**所有消息 type 都被 `outbox_trigger_types` 覆盖**。未来若新增"只给前端看、不触发 wake"的消息类型（如 `SYSTEM_HINT` / `TOOL_TRACE`），必须同步决定它们落 pending 还是 consumed。
- 同理，`docs/architecture/message-wake-principles.md` 的"消息生命周期"章节建议加一张矩阵图。

