# PR-22  subscriber 成功 dispatch → message transition → `claimed(by_scope)`

| 字段 | 值 |
| --- | --- |
| **Phase** | 3 |
| **Milestone** | M3 |
| **承诺** | R4 |
| **Status** | `[x]` (2026-04-15) |
| **Depends on** | PR-16, PR-21 |
| **Blocks** | PR-23 |
| **估时** | 0.5 d |
| **Owner** | __ |
| **PR 标题** | `feat(business): subscriber transitions messages to claimed(by_scope) on dispatch success` |

## 目标

让"消息被 scope 吸入"这件事落到数据上：subscriber dispatch 成功后，把对应 message lifecycle 从 `pending` → `claimed(by_scope=<scope_id>)`。

## 范围

- `novaic-business/business/subscribers/dispatch_subscriber.py`
- Queue Service `/dispatch` 响应体（确认含 `scope_id`）
- `entangled.message_state.transition` 调用点

## 前置 Checklist

- [ ] PR-21 的 `transition()` 可用
- [ ] PR-16 subscriber 在跑
- [ ] Queue Service `DispatchResult` 必含 `scope_id`（若不含，先补一个 PR 让它返回）

## 实施 Checklist

### subscriber 改动

- [ ] `_deliver_one` 成功路径（dispatch 200）在 `UPDATE message_outbox ... delivered_at` 之后追加：
  ```python
  if result.scope_id:
      try:
          transition(conn, row["message_id"],
                     to="claimed",
                     scope_id=result.scope_id,
                     reason="subscriber_dispatch_ok")
      except InvalidTransition as e:
          # 已被别处（recovery）claim？log + 不 fail delivery
          logger.warning("message already in non-pending state: %s", e)
  ```
- [ ] `buffered=True`（同 agent 已有 active session，消息被归并）：
  - transition 仍 `claimed(by_scope=<existing_scope>)`（Queue 返回同一 scope_id）
  - 或调 Cortex `POST /v1/scope/{id}/append_input`（PR-20）
- [ ] 事务性：`transition` 与 `UPDATE outbox` 最好同 DB 事务（两者都是 Entangled DB）

### 失败路径不 transition

- [ ] `DispatchError` → 不改 lifecycle（保持 pending，PR-26 orphan emitter 会关注）

## 测试 Checklist

- [ ] 集成：发消息 → dispatch 成功 → `SELECT lifecycle FROM chat_messages WHERE id=?` = `claimed`，`claimed_by_scope = <某 scope_id>`
- [ ] 集成：发消息 + 模拟 dispatch 失败 → lifecycle 保持 `pending`
- [ ] 集成：同 agent 2 条消息 → 2 条都 `claimed`，`claimed_by_scope` 相同

## 可观测性 Checklist

- [ ] metric `subscriber_transition_total{result=ok|invalid}` counter
- [ ] log：`subscriber transition msg=... -> claimed scope=...`

## 文档 Checklist

- [ ] [message-wake-refactor.md](../message-wake-refactor.md) P3-3 → `[x]`
- [ ] 本工单 Status → `[x]`

## 验收命令

```bash
./scripts/reset-agent-data.sh
# 发消息 → 等 subscriber
sqlite3 ~/.novaic/data/entangled.db \
  "SELECT id, lifecycle, claimed_by_scope FROM chat_messages ORDER BY created_at DESC LIMIT 5;"
# 预期：lifecycle='claimed'，claimed_by_scope 非空
```

## 回滚

`git revert` — 消息状态回到 pending，非致命。

## 备注

- 别让 transition 失败阻断 outbox delivered 标记（两者虽同 DB，但 dispatch 已经真的发生了）；transition 失败只打警告。
