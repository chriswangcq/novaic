# Agent Activity Timeline 专题索引

| 字段 | 内容 |
| --- | --- |
| 状态 | 已收敛为专题索引 |
| 主方案 | `agent-perception-action-architecture.md` |

## 说明

Agent Activity Timeline 的完整设计已经并入 `agent-perception-action-architecture.md`，本文不再复制一份细碎方案，避免同一概念在多处漂移。

后续讨论和施工以主方案为准。

## 本专题只保留关注点

Activity Timeline 是用户可见的 Agent Monitor，不是开发诊断面板，也不是 Cortex source of truth。

它只回答用户关心的三件事：

1. **Observation**：Agent 看到了什么。
2. **Reasoning**：Agent 这一轮怎么想，直接来自 LLM `reasoning_content`。
3. **Action**：Agent 做了什么。

## 与其他概念的边界

| 概念 | 职责 |
| --- | --- |
| message status | 只表示用户消息投递状态：`Sending / Delivered / Failed` |
| Developer diagnostics | 开发诊断，允许 raw payload、step/payload ref、HTTP/MCP 细节 |
| Activity Timeline | 用户可见 Agent 工作过程 |
| Cortex | Activity Timeline 的 source projection 输入，拥有 active working trace |

## 当前主方案中的关键规则

- Timeline 从 Cortex trace 投影，不自己成为事实源。
- 工具结果默认展示 percept/ref，不自动展示 raw payload。
- 理解性 summary / QA / search result 必须来自 Agent 显式 payload interpretation action。
- 默认用户面不展示 result id、raw MCP content、raw HTTP body、secret、内部 stack trace。

## 施工入口

详见主方案：

- `agent-perception-action-architecture.md#Activity Timeline`
- `agent-perception-action-architecture.md#实施阶段`
- `agent-perception-action-architecture.md#一致性检查`
