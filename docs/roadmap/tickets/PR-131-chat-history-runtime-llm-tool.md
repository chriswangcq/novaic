# PR-131: Promote `chat_history` to a real LLM + Runtime tool

## 背景

`chat_history` 在 common 产品工具目录中存在，但不在 canonical LLM tool schema，也没有 Runtime executor。它当前是“看起来能用、实际不能用”的残留能力。

## Scope

- 将 `chat_history` 加入 `common.tools.llm_builtin.AGENT_BUILTIN_TOOL_SCHEMAS`。
- 将 common `CHAT_TOOLS` 改为从 canonical schema 适配 `chat_reply` + `chat_history`。
- 在 Runtime `tool_handlers` 中实现 `chat_history` executor，通过 Business internal chat history API 读取当前 agent 最近消息。
- 返回结构化、简短的历史消息，供 LLM 在必要时补查。

## 非目标

- 不恢复旧 read/unread 控制流。
- 不在 Cortex 里自动注入完整 chat history。
- 不做自动总结。

## 单元测试

- Common：`chat_history` 出现在 canonical schema 与 `CHAT_TOOLS`，且 metadata 由 canonical schema 适配。
- Runtime：正常返回最近消息；limit clamp；Business API 异常时返回失败。
- Cortex：tool schema 名单包含 `chat_history`。

## 冒烟测试

- LLM request tools 中包含 `chat_history`。
- 模型调用 `chat_history(limit=...)` 后，tool result 中只出现当前 agent 的最近聊天消息。

## 部署 Checklist

- Common / Cortex / Runtime 测试通过。
- 部署 Common、Cortex、Runtime。
- 线上确认 `chat_history` 不再是未知工具。

## GitHub / Merge

- 可单独 merge；建议在 PR-130 后 merge。
- Commit message: `feat(tools): add chat history runtime tool`

