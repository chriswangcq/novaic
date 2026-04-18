# PR-25  Business `/internal/messages/{id}/trace`

| 字段 | 值 |
| --- | --- |
| **Phase** | 3 |
| **Milestone** | M3 |
| **承诺** | R4 |
| **Status** | `[ ]` |
| **Depends on** | PR-21 |
| **Blocks** | — |
| **估时** | 0.5 d |
| **Owner** | __ |
| **PR 标题** | `feat(business): /internal/messages/{id}/trace — unified message → scope view` |

## 目标

把"这条消息去哪了"做成一个 API 调用，而不是串库。这是 R4 的面向运维出口。

## 范围

- `novaic-business/business/internal/messages.py`（或等价）
- 可选：CLI `novaic-cli msg trace <id>`

## 前置 Checklist

- [ ] PR-21 lifecycle 字段存在
- [ ] Cortex `GET /v1/scope/{id}/meta` 端点可用（若无，在本 PR 里同步加 Cortex 侧）

## 实施 Checklist

### 端点定义

```
GET /internal/messages/{message_id}/trace
→ 200 {
  "message_id": "...",
  "agent_id": "...",
  "sender": "user",
  "lifecycle": "claimed",
  "claimed_by_scope": "scope-...",
  "lifecycle_updated_at": 1700000000,
  "outbox": {
    "delivered_at": 1700000001,
    "attempts": 1,
    "last_error": null
  },
  "scope": {
    "scope_id": "scope-...",
    "state": "active",                # from Cortex (PR-29 之前是 derived)
    "active_session_id": "...",
    "input_message_ids": ["...", "..."]
  },
  "current_session": {                 # from Queue Service
    "session_id": "...",
    "status": "running"
  }
}
→ 404 if message_id unknown
```

### 实现

- [ ] 从 `chat_messages` 读 lifecycle 等基础字段
- [ ] 从 `message_outbox` 读投递状态
- [ ] 若 `claimed_by_scope` 非空 → 调 Cortex `GET /v1/scope/{id}/meta` 取 scope 数据
- [ ] 若 `scope.active_session_id` 可查 → 调 Queue Service 看当前 session 状态
- [ ] 任何下游服务错误 → 仅对应字段留空 + `errors: [...]`，不整体 fail

### 可选 CLI

- [ ] `scripts/cli.py msg trace <id>` 调上面 API 并 pretty print

## 测试 Checklist

- [ ] 单测：msg 不存在 → 404
- [ ] 单测：pending / claimed / consumed / orphaned 四种生命期都能正确显示
- [ ] 集成：发消息 + 等完成 → trace 返回 `lifecycle=consumed`

## 可观测性 Checklist

- [ ] metric `message_trace_requests_total` counter
- [ ] 端点自带慢调用追踪（> 200ms 打 WARN）

## 文档 Checklist

- [ ] [message-wake-refactor.md](../message-wake-refactor.md) P3-6 → `[x]`
- [ ] 本工单 Status → `[x]`
- [ ] `docs/runbooks/troubleshooting.md` 里增加 "消息没回复的 SOP" 的第一步就是 `curl .../trace`

## 验收命令

```bash
MID="<some message id>"
curl -s -H "X-Internal-Key: $NOVAIC_INTERNAL_KEY" \
     -H "X-Internal-Service: cli" \
     http://localhost:8200/internal/messages/$MID/trace | jq .
```

## 回滚

`git revert` —— 排查回到人肉。

## 备注

- 这是运维最实用的一个端点；可以让新人 30 秒学会查 "消息为什么没回复"。
- 后续可以在这个基础上加 "per-agent pending list"、"orphan summary" 等（PR-26 会有类似端点）。
