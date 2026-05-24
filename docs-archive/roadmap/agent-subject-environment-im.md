# Agent Subject / Environment IM 专题索引

| 字段 | 内容 |
| --- | --- |
| 状态 | 已收敛为专题索引 |
| 主方案 | `agent-perception-action-architecture.md` |

## 说明

Agent 主体化与 Environment IM 的完整设计已经并入 `agent-perception-action-architecture.md`，本文不再复制一份细碎方案，避免“环境通知”和“工具观察”两套描述分叉。

后续讨论和施工以主方案为准。

## 本专题只保留关注点

Agent 是主体；用户消息、subagent 消息和系统事件都是 Environment 里的 notification。Notification 只告诉 Agent “有事发生”，具体内容必须通过工具读取。

```text
你收到一条来自 user:xxx 的消息。
请通过 shell 调用 `agentctl im read` 查看内容。
```

而不是把完整消息正文直接塞进 LLM prompt。

## Environment 边界

Environment 拥有：

- event envelope
- IM message
- sender / channel / thread
- notification lifecycle
- resource ref

Environment 不拥有：

- device truth
- file contents
- shell process state
- browser state
- audio blob contents
- LLM prompt 拼装
- Cortex scope tree
- reasoning / summary

## 当前主方案中的关键规则

- Notification 不是 Observation。
- `agentctl im read` 结果作为 Observation percept 写入 Cortex。
- 用户消息、subagent 消息、system event 统一 sender/channel/thread/message_id 模型。
- subagent report 应退役为普通 IM message。
- processed lifecycle 由 Runtime wake finalize / scope close 成功后处理。
- 历史翻阅走 `agentctl im history/search/context`，不恢复旧 `chat_history` 自动 prompt memory。

## 施工入口

详见主方案：

- `agent-perception-action-architecture.md#IM / Environment 工具方向`
- `agent-perception-action-architecture.md#目标 LLM 调用形态`
- `agent-perception-action-architecture.md#端到端流程`
