# Scope / Notification Lifecycle

当前 Agent-loop 生命周期由两套最小结构组成：

1. **Environment notifications**：负责“外部事件是否已被 Agent 处理”。
2. **Cortex scopes**：负责“Agent 本轮工作轨迹如何展开、折叠、归档”。

`chat_messages.lifecycle`、`message_outbox`、message orphan/stuck-claimed recovery
已退出主路径；不要把它们当作 Agent-loop 状态来源。

## Environment Notification

状态机：

```text
pending -> claimed -> processed
pending -> failed
claimed -> failed
failed  -> claimed
```

含义：

| 状态 | 含义 |
| --- | --- |
| `pending` | 已收到外部事件，尚未被 Runtime wake scope 认领 |
| `claimed` | Runtime 已把 notification 绑定到当前 wake scope |
| `processed` | wake scope 已完成并写入 summary.md |
| `failed` | 调度或执行失败，保留诊断信息，可被重新认领 |

DispatchSubscriber 只负责从 pending notification 生成 Queue dispatch；Runtime 在
`session.init` 认领 notification，在 `scope_end` 成功后标记 processed。

## Cortex Scope

Cortex 只维护 LIFO scope 树：

- active scope 展开完整轨迹。
- closed scope 只通过 `summary.md` 折叠到父 scope。
- Agent root 不关闭。
- 当前 wake scope 完成时由 LLM 调用 `skill_end(report=...)` 写入本轮摘要并关闭。

## 排查顺序

1. 查 `environment_notifications`：确认是否 pending/claimed/processed/failed。
2. 如果 claimed，拿 `claim_scope_id` 去跨日志 grep。
3. 查 Cortex scope：确认 active/archived 状态和 `summary.md`。
4. 查 Queue/Saga：确认 dispatch 是否启动、是否超时。

常用查询：

```bash
sqlite3 /opt/novaic/data/entangled.db \
  "SELECT id, agent_id, source_id, state, claim_scope_id, dispatch_attempts, dispatch_error, created_at, updated_at
     FROM environment_notifications
    ORDER BY created_at DESC LIMIT 20;"
```

## Guardrail

- 不允许重新暴露 `/v1/messages/{id}/transition` 或 `/internal/messages/bulk-transition`。
- 不允许重新引入 `message_outbox` wake queue。
- 不允许 HealthWorker 扫描 chat-message lifecycle 并 redispatch。
- 不允许从 `im_reply` 或历史 transcript 推断长期记忆；连续性只来自 Cortex scope tree 和显式 summary。
