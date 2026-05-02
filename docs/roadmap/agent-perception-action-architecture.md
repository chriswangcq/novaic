# Agent Perception-Action 统一方案

| 字段 | 内容 |
| --- | --- |
| 状态 | 统一技术设计稿 |
| 创建时间 | 2026-05-02 |
| 方案入口 | 本文是唯一主方案；`agent-subject-environment-im.md` 和 `agent-activity-timeline.md` 只保留专题索引 |
| 目标 | 统一 Agent 主体化、Environment 通知、工具观察、Cortex 工作轨迹和用户可见 Activity Timeline |
| 非目标 | 不把 authority prompt 环境化；不把 Activity Timeline 当事实源；不新增绕过 Cortex 的连续性通路；不让 Runtime 自动总结 payload |

## 一句话

Agent 是主体；Environment 只通知“外界有事发生”；Agent 通过工具观察世界；Cortex 记录 Agent 的工作轨迹；Activity Timeline 只是这条轨迹的用户可见投影。

## 核心不变量

```text
Notification is not Observation.
Observation must come from a tool.
Environment owns event envelopes, IM messages, notifications, and refs.
Cortex active scope is the working-trace source of truth.
Activity Timeline is a projection, not a source of truth.
Closed scope exposes summary.md, not raw working trace.
Cortex stores percepts by default; summaries require explicit interpretation actions.
Raw payload must never be default Cortex content.
```

## 整体模型

```text
External world
  ├─ user message
  ├─ subagent message
  ├─ system event
  └─ resource refs: shell / file / display / audio / browser / device
  ↓
Environment
  ├─ event envelope
  ├─ IM message
  ├─ notification lifecycle
  └─ resource ref
  ↓
Agent wake
  ├─ authority prompt
  ├─ tool schemas
  ├─ Cortex visible context
  └─ Environment notifications
  ↓
Agent actions
  ├─ observe: im_read / display / audio_qa / shell / payload_*
  ├─ think: LLM reasoning_content
  └─ act: im_reply / im_send / skill_begin / skill_end / ...
  ↓
Cortex active scope
  ├─ notification
  ├─ observation percept
  ├─ explicit interpretation observation
  ├─ reasoning
  ├─ action
  └─ payload refs
  ↓
Activity Timeline
  └─ user-facing projection
  ↓
skill_end(report=...)
  └─ summary.md exposed after scope closes
```

## 服务边界

| 模块 | 拥有 | 不拥有 |
| --- | --- | --- |
| Environment | event envelope、IM message、sender/channel/thread、notification queue、claim/read/processed lifecycle、resource ref、subagent communication envelope | device truth、file contents、shell process state、browser state、audio blob、prompt 拼装、Cortex scope、reasoning、`summary.md` |
| Runtime | LLM loop、tool call execution、把 tool action / observation / reasoning / reply 写入 Cortex | 业务事实源、Environment storage、Cortex 折叠规则、用户画像记忆推断 |
| Cortex | LIFO scope 树、active trace、closed scope `summary.md`、LLM context 拼装 | 自动总结、用户画像、业务任务系统、payload 原文、Activity Timeline source of truth |
| Activity Timeline | 从 Cortex trace 投影用户可见活动流 | 原始事实源、诊断 payload、长期记忆 |
| Execution log | 开发诊断、raw payload 链接、排障细节 | 普通用户面 Agent Monitor |

## Authority 与 Environment

必须拆开两类 system：

| 类型 | 是否环境化 | 说明 |
| --- | --- | --- |
| Authority prompt | 否 | 模型身份、安全规则、developer 指令、工具边界，必须直接进入 LLM prompt |
| Environment event | 是 | 定时唤醒、消息到达、subagent 消息、外部事件，只作为 notification |

不能把 authority prompt 做成 `im_read` 可选观察项，否则 Agent 可以“忘记读取规则”，安全边界会坏。

## Notification / Observation / Percept

Notification 是外界提示：

```text
你收到一条来自 user:155cc... 的消息。
```

Notification 可以进入 prompt，但它不是事实观察。Agent 需要调用工具读取：

```text
action: im_read(msg_123)
observation percept: user said "帮我看看消息为什么发不出去"
```

Observation 默认写入的是 **percept**，即 Agent 第一眼能看到的东西：metadata、状态、preview、head/tail、截断标记、payload/ref。

```json
{
  "kind": "shell_result",
  "percept": {
    "exit_code": 1,
    "stdout_head": "...",
    "stdout_tail": "...",
    "stderr_tail": "TypeError: ...",
    "stdout_bytes": 512000,
    "stderr_bytes": 32000,
    "truncated": true
  },
  "payload_ref": "payload://shell/abc123"
}
```

这就是“像人看电脑”：先看到屏幕窗口、head/tail、错误尾部、文件预览和元数据。

## Payload 解释规则

大型或敏感内容不直接进入 Cortex。默认只写：

- percept
- truncation metadata
- payload/ref

如果 Agent 需要理解完整 payload，必须显式调用解释工具：

```text
payload_read(payload_ref, range="tail:500")
payload_search(payload_ref, query="FAILED")
payload_summarize(payload_ref, focus="test failures")  # future interpretation tool
payload_qa(payload_ref, question="失败原因是什么？")     # future interpretation tool
```

这些工具的结果才是 payload slice / match context / summary / answer，并作为新的 Observation 写入 Cortex。当前 PR-164B 已实现 `payload_read` 和 `payload_search`；`payload_summarize` / `payload_qa` 仍是后续解释工具方向，不是当前活工具。

Runtime 不应该替 Agent 自动总结长 payload；否则会变成第二条隐式记忆通路。

## Reasoning

Reasoning 来自 LLM Factory 的 `reasoning_content`。

规则：

- 写入 Cortex active scope，作为完整工作轨迹。
- 可投影到 Activity Timeline，默认预览/可展开。
- 不作为系统事实、用户画像、记忆推断、任务状态或业务控制依据。
- closed scope 后，父层只看到 `summary.md`，不会展开历史 raw reasoning。

不再设计额外 monitor-only reasoning summary。

当前 PR-164C 已提供 Cortex `/v1/trace/project` 投影：reasoning 记录直接来自 provider-authored `reasoning_content`，不会再生成一条 monitor-only reasoning summary。

## Action

Action 是 Agent 对环境或系统发起的动作，例如：

- `im_reply`
- `shell`
- `display`
- `audio_qa`
- `skill_begin`
- `skill_end`
- `subagent_spawn`
- `im_send`
- `payload_read` / `payload_search`

Future interpretation actions, not current live tools:

- `payload_summarize`
- `payload_qa`

Action 的结果不塞回 Action 本身；工具结果默认成为下一条 Observation percept，显式解释工具的结果再成为解释性 Observation。

## Summary

Summary 只有一条正路：

```text
skill_end(report=...) -> current scope summary.md
```

它是 closed scope 向父 scope / future wake 暴露的默认内容。

禁止：

- 从 `im_reply` 猜长期记忆。
- 从 reasoning 自动总结。
- 从 tool result 自动总结。
- 引入 wake summary / fallback summary / 多条并行摘要通路。

## IM / Environment 工具方向

长期工具族：

| 工具 | 语义 |
| --- | --- |
| `im_list` | 查看待处理 notification |
| `im_read` | 读取用户/subagent/system-event 消息正文 |
| `im_reply` | 回复用户 |
| `im_send` | 给 subagent 或其他 Agent 发送 IM |
| `im_mark_processed` | 标记 notification 已处理 |

当前活工具名已经切到 Environment IM：`im_read`、`im_reply`、`im_send`。
旧 `chat_reply`、`chat_history`、`subagent_send`、`subagent_report`、`subagent_query`、`subagent_cancel` 不再作为 LLM 工具暴露。

用户消息、subagent 消息、系统事件都走同一 sender/channel/thread/message_id 模型。

## Activity Timeline

Activity Timeline 是用户可见的 Agent Monitor，不是诊断面板。

| Cortex trace | Timeline phase | 用户看到 |
| --- | --- | --- |
| notification | Observation precursor | 收到一条消息通知 |
| `im_read` action | Action | 读取用户消息 |
| `im_read` result | Observation | 用户说：“...” |
| `reasoning_content` | Reasoning | 正在思考 / reasoning preview |
| tool call | Action | 执行命令 / 查看附件 / 派生子 Agent |
| tool result percept | Observation | 命令完成，显示状态、preview、head/tail、payload/ref |
| payload interpretation result | Observation | Agent 已分析 payload，得到失败原因/摘要/答案 |
| `im_reply` | Action | 回复用户 |
| `skill_end` | Action / Summary | 保存上下文 |

默认用户面不展示：

- result id
- raw MCP content
- raw HTTP payload
- secret
- 内部 stack trace
- 未过滤完整 tool result

message status 只表示发送投递状态：`Sending / Delivered / Failed`。它不承担 Agent 是否已读、是否处理、是否会回复的语义。

## 目标 LLM 调用形态

长期目标下，LLM prompt 包含：

1. Authority prompt。
2. Tool schemas。
3. Cortex visible context：
   - active scope 展开完整工作轨迹。
   - closed child scope 只展开 `summary.md`。
4. Environment notifications。

LLM prompt 不直接包含未观察的用户消息正文。消息正文必须通过 observation tool 读取。

大型 payload 也不直接展开进 prompt。它们以 percept + payload/ref 进入 Cortex；理解性 summary 只能来自 Agent 显式调用解释工具后的新 Observation。

## 端到端流程

### 用户消息

```text
1. User sends message.
2. Environment stores message and creates notification.
3. Queue opens wake scope.
4. LLM sees notification only.
5. Agent calls im_read.
6. im_read result becomes Observation percept in Cortex.
7. LLM reasoning_content is written to Cortex.
8. Agent acts: tools / reply / skill_end.
9. Activity Timeline projects Cortex trace.
10. summary.md becomes future context after scope closes.
```

### 工具长输出

```text
1. Agent calls shell.
2. Runtime stores raw output as payload.
3. Cortex receives observation percept + payload_ref.
4. If needed, Agent calls payload_read / payload_search.
5. Interpretation result becomes a new Observation.
```

### Subagent 消息

```text
1. Subagent sends IM to parent/sibling.
2. Environment creates notification.
3. Recipient calls im_read.
4. Message content becomes Observation percept.
5. Any response uses im_send.
```

## 数据所有权

| 数据 | Source of Truth | 用途 | 不应承担 |
| --- | --- | --- | --- |
| 原始用户消息 | Message/IM store | 环境原始数据 | 直接作为 prompt fact |
| Notification | Environment / Queue | 唤醒 Agent、提示有事发生 | Observation、长期记忆 |
| Observation percept | Cortex active scope | Agent 已观察到的第一视图、metadata、head/tail、preview、ref | 未观察消息、模型主观推断、理解性总结 |
| Interpretation result | Cortex active scope | Agent 显式调用 summary/search/QA/read 后得到的解释结果 | 隐式自动总结 |
| Reasoning | Cortex active scope | 当轮 LLM 思考轨迹 | 事实源、记忆、业务控制 |
| Action | Cortex active scope | Agent 行动事实 | 工具结果本身 |
| Tool result payload | Domain store / diagnostic payload | 原始输出、二进制、大 JSON、长 stdout/stderr | 默认塞入 Cortex |
| summary.md | Cortex closed scope | 折叠连续性 | raw trace、自动 wake summary |
| Activity Event | Cortex trace 的物化投影 | 用户可见工作过程数据 | 独立事实源 |
| execution log | Diagnostic store | 开发排障 | 用户面产品事实 |

## 实施阶段

1. **P0 概念与 guardrail**：定义 notification / observation / action / reasoning / summary / percept / interpretation 的共享词表。
2. **P1 Environment 服务骨架**：收拢 event envelope、IM message、notification lifecycle 和 ref，不接管 domain truth。
3. **P2 Cortex 工作轨迹写入**：Runtime 写入 tool action、tool percept observation、explicit interpretation observation、LLM reasoning、reply action、scope close summary。
4. **P3 IM read path**：`im_read` 读取结果自动写入 Cortex Observation percept。
5. **P4 Payload interpretation tools**：为大 payload 建 ref，提供 read/search/summarize/QA 显式解释工具，禁止自动 summary 塞回 Cortex。
6. **P5 Prompt notification-only**：LLM prompt 只注入 notification，不注入未观察消息正文。
7. **P6 Activity Timeline 投影**：Timeline 从 Cortex trace 的物化 activity events 投影，execution log 下沉为开发诊断。
8. **P7 物理删除旧通路**：删除正文直塞 prompt、subagent report 特殊注入、execution log 用户面 fallback、旧 query/cancel/report 工具、tool result 自动 summary 等隐式路径。

## 一致性检查

任何新代码或新设计都要回答：

1. 这是一条 Notification，还是 Observation？
2. 如果是 Observation，它来自哪个工具？
3. 它是 percept，还是显式解释动作产生的 summary/QA/search/read 结果？
4. raw payload 是否只通过 ref 暴露，而不是默认进入 Cortex？
5. 它是否写入 Cortex active scope？
6. 它在 scope close 后是否只通过 `summary.md` 暴露？
7. Activity Timeline 展示的是投影，还是偷偷成了 source of truth？
8. 这条路径是否绕过了 Environment / Cortex？
9. 这条路径是否把 authority prompt 环境化了？

## 待决策问题

1. 第一版是否允许 direct prompt 正文和 `im_read` 共存，还是必须一次切到 notification-only？
2. processed lifecycle 是否由 Runtime 在 `skill_end` / turn finalize 成功后自动完成？
3. Activity Timeline 第一版是否直接基于 Cortex trace 的物化 activity events，还是先从现有 execution log 投影过渡？
4. Reasoning 默认展示多少内容，是否需要用户可配置？
5. Environment 第一版是独立进程，还是独立子模块但随 Business/Runtime 部署？
6. payload interpretation tools 第一版最小集合是否只需要 `payload_read` + `payload_qa`，还是同时提供 search/summarize？

## 结论

这次设计只保留一条主干：

```text
Environment notification
→ Agent tool observation
→ Cortex working trace
→ Activity Timeline projection
→ skill_end summary.md
```

任何绕过这条主干的自动总结、直接注入、诊断面用户化、fallback 兼容分支，都应该被视为维护风险。
