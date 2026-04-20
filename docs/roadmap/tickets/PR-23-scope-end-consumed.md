# PR-23  scope_end → 批量 transition `inputs` 到 `consumed`

| 字段 | 值 |
| --- | --- |
| **Phase** | 3 |
| **Milestone** | M3 |
| **承诺** | R4 |
| **Status** | `[x]` (2026-04-15) |
| **Depends on** | PR-20, PR-21 |
| **Blocks** | — |
| **估时** | 0.5 d |
| **Owner** | __ |
| **PR 标题** | `feat(runtime+business): scope_end transitions consumed for all input messages` |

## 目标

关闭消息生命周期闭环：scope 正常归档成功 → 其所有 input messages → `consumed`。

## 范围

- Cortex scope_end / session.ended handler
- Business 新增内部端点 `POST /internal/messages/bulk-transition`（供 runtime / cortex 调）
- 或：runtime 直接调 Entangled 的 `message_state.transition`（若跨进程不方便，走 Business 端点）

## 前置 Checklist

- [ ] PR-20 scope.input_message_ids 可用
- [ ] PR-21 message_state.transition 可用

## 实施 Checklist

### 推荐路径：通过 Business 端点

- [ ] Business 新增 `POST /internal/messages/bulk-transition`：
  ```json
  {
    "message_ids": ["m1","m2"],
    "to": "consumed",
    "scope_id": "<scope_id>",
    "reason": "scope_end"
  }
  ```
- [ ] Business 端内调用 `message_state.transition` 逐条
- [ ] 对每条失败独立 log，不整体 fail

### scope_end / session.ended 时机

- [ ] runtime 的 `scope.end` / `session.ended` handler 成功路径：
  ```python
  scope_meta = load_scope_meta(scope_id)
  if scope_meta.get("input_message_ids"):
      await business_client.post("/internal/messages/bulk-transition", json={
          "message_ids": scope_meta["input_message_ids"],
          "to": "consumed",
          "scope_id": scope_id,
          "reason": "scope_end",
      })
  ```
- [ ] scope_end 失败 → 不 transition（保持 `claimed`，让 recovery 机制决策是否 orphan）

### 并发 / 重入

- [ ] scope_end 可能被重试 → transition 必须幂等（`claimed -> consumed` 转移允许的，重复调第二次会 InvalidTransition；需要 subscriber-like 的宽容处理）
- [ ] 实现：`transition()` 里若 `to == cur` 直接 return silently（视为 no-op）

## 测试 Checklist

- [ ] 集成：发 1 条消息 → scope 正常 end → `SELECT lifecycle FROM chat_messages WHERE id=?` = `consumed`
- [ ] 集成：发 3 条消息归并同 scope → 全部 consumed
- [ ] 集成：scope 失败 archive → inputs 保持 claimed（不是 consumed）
- [ ] 单测：bulk-transition 端点部分失败 → 返回 per-id result

## 可观测性 Checklist

- [ ] metric `scope_inputs_consumed_total` counter
- [ ] log：`scope_end scope=... inputs=<n> consumed=<m>`

## 文档 Checklist

- [ ] [message-wake-refactor.md](../message-wake-refactor.md) P3-4 → `[x]`
- [ ] 本工单 Status → `[x]`
- [ ] [cortex/scope-lifecycle.md](../../cortex/scope-lifecycle.md) 补 "scope end 对 input messages 的状态传播"

## 验收命令

```bash
# 端到端
./scripts/reset-agent-data.sh
# 发一条 → agent 回复 → session end
sqlite3 ~/.novaic/data/entangled.db \
  "SELECT id, lifecycle FROM chat_messages ORDER BY created_at DESC LIMIT 2;"
# 用户消息 lifecycle='consumed'
```

## 回滚

`git revert` —— 消息停在 claimed；PR-30 删旧字段前都能兼容。

## 备注

- `consumed` 是终态；想重新处理同一消息，需要重新插入消息。
