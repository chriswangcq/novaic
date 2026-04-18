# PR-20  Scope `meta.input_message_ids` 登记

| 字段 | 值 |
| --- | --- |
| **Phase** | 3（trace + lifecycle） |
| **Milestone** | M3 |
| **承诺** | R4 |
| **Status** | `[ ]` |
| **Depends on** | PR-10 |
| **Blocks** | PR-23, PR-24 |
| **估时** | 1 d |
| **Owner** | __ |
| **PR 标题** | `feat(cortex): scope meta.input_message_ids + append_input endpoint` |

## 目标

让每个 scope 知道它吸入了哪些 messages（多对一可能）。为 "消息去哪了"（PR-25）和 scope_end → consumed（PR-23）提供基础数据。

## 范围

- `novaic-cortex/novaic_cortex/scope.py`（或 meta 写入处）
- `novaic-cortex/novaic_cortex/api.py`（新增 endpoint）
- `novaic-agent-runtime/task_queue/handlers/runtime_handlers.py::handle_session_init`（传递 message_ids）
- Queue Service `DispatchRequest` 校验保留 `metadata.message_ids`

## 前置 Checklist

- [ ] PR-10 Assembler 已经把 `message_ids` 放在 `metadata.message_ids`
- [ ] 确认 session_init → scope 创建的字段透传链路

## 实施 Checklist

### 1. Scope meta 扩字段

- [ ] `scope.meta.json` schema 增加：
  ```json
  {
    "input_message_ids": []
  }
  ```
- [ ] 已有 scope 的 meta 不含此字段时，读取 default `[]`（向后兼容）

### 2. session.init 传 message_ids

- [ ] runtime `handle_session_init`：从 `payload.metadata.message_ids` 取出 → 写入 scope meta
- [ ] 若 payload 无 `message_ids` → 写空 list（旧客户端兼容）

### 3. 新增 API：追加 input

- [ ] Cortex `POST /v1/scope/{scope_id}/append_input`:
  ```json
  { "message_ids": ["<id1>", "<id2>"] }
  ```
  - 200 `{"input_message_ids": [...]}`（合并去重后）
  - 404 scope 不存在
- [ ] 幂等：重复传相同 id 不报错，也不重复存储
- [ ] 应在 `_scope_lock_cm` 保护下（复用 Cortex 锁）

### 4. 调用点

- [ ] Queue Service 在 "buffer 消息进同一 session" 时，应调 `append_input`（需要确认 session.buffered 时的调用链：Queue → Cortex 还是 Queue 自己持有 scope_id 再转发？）
- [ ] 也可由 Business subscriber 在 dispatch 成功且 `result.buffered = True` 时调 Cortex 追加

> **TODO during review**: 确认 buffer 场景的数据流，选上面两种之一。

## 测试 Checklist

- [ ] 单测：session.init → scope meta 含 message_ids
- [ ] 单测：append_input 幂等
- [ ] 集成：
  - 连发 3 条消息给同一 agent（1 ms 间隔）
  - 第 1 条起 session，后 2 条 buffered
  - 最终 scope.input_message_ids.length = 3

## 可观测性 Checklist

- [ ] metric `scope_inputs_total{source=init|append}` counter
- [ ] log: `scope_input_appended scope=... messages=<n> total=<m>`

## 文档 Checklist

- [ ] [message-wake-refactor.md](../message-wake-refactor.md) P3-1 → `[x]`
- [ ] 本工单 Status → `[x]`
- [ ] [cortex/scope-lifecycle.md](../../cortex/scope-lifecycle.md) 补一节 "scope 的 input 登记"

## 验收命令

```bash
# 造测试
curl -X POST http://localhost:5000/v1/scope/<id>/append_input \
     -H "Content-Type: application/json" \
     -d '{"message_ids":["m1","m2"]}'

# 查 meta
cat ~/.novaic/cortex/scopes/<id>/meta.json | jq '.input_message_ids'
```

## 回滚

`git revert` — 已产出的 scope meta 字段不受影响（只是旧 scope 不含此字段）。

## 备注

- 这是 R4 "scope 为 trace 载体" 的第一块砖。
- append_input 是 "buffered 消息归并" 场景所需。
