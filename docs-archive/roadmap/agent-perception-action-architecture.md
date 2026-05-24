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
  ├─ observe: shell CLI / display
  ├─ think: LLM reasoning_content
  └─ act: shell CLI / skill_begin / skill_end / sleep
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
| Developer diagnostics | 开发排障入口，可追踪 payload/ref、HTTP/MCP 细节、异常栈 | 普通用户面 Agent Monitor、业务事实源、单独的 `execution-logs` 产品实体 |

## Authority 与 Environment

必须拆开两类 system：

| 类型 | 是否环境化 | 说明 |
| --- | --- | --- |
| Authority prompt | 否 | 模型身份、安全规则、developer 指令、工具边界，必须直接进入 LLM prompt |
| Environment event | 是 | 定时唤醒、消息到达、subagent 消息、外部事件，只作为 notification |

不能把 authority prompt 做成可选环境观察项，否则 Agent 可以“忘记读取规则”，安全边界会坏。

## Notification / Observation / Percept

Notification 是外界提示：

```text
你收到一条来自 user:155cc... 的消息。
```

Notification 可以进入 prompt，但它不是事实观察。Agent 需要通过 shell 中的 Environment CLI 读取：

```text
action: shell("agentctl im read --notification-id msg_123")
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

如果 Agent 需要理解完整 payload，必须显式调用 shell 中的 payload CLI：

```text
cortex payload read payload_ref --range tail:500
cortex payload search payload_ref --query "FAILED"
cortex payload summarize payload_ref --focus "test failures"
cortex payload qa payload_ref --question "失败原因是什么？"
```

这些 CLI 结果才是 payload slice / match context / summary / answer，并作为新的 Observation 写入 Cortex。summarize/QA 必须由 Agent 显式调用，不能由 Runtime 或 Cortex 自动触发。

Runtime 不应该替 Agent 自动总结长 payload；否则会变成第二条隐式记忆通路。

## Reasoning

Reasoning 来自 LLM Factory 的 `reasoning_content`。

规则：

- 写入 Cortex active scope，作为完整工作轨迹。
- 可物化到 Agent Monitor product projection，默认预览/可展开。
- 不作为系统事实、用户画像、记忆推断、任务状态或业务控制依据。
- closed scope 后，父层只看到 `summary.md`，不会展开历史 raw reasoning。

不再设计额外 monitor-only reasoning summary。

当前 PR-193 后，用户面 Agent Monitor 不再直查 Cortex `/v1/trace/project`；Runtime 在执行过程中把 provider-authored `reasoning_content` 物化到 `agent-activity-records`，不会再生成一条 monitor-only reasoning summary。

## Action

Action 是 Agent 对环境或系统发起的动作，例如：

- `shell`
- `display`
- `skill_begin`
- `skill_end`
- `sleep`

其中 `shell` 是 CLI 总线，不只是普通命令执行。当前 IM、subagent、audio、payload、device 等接口类能力都通过 shell 内 CLI 暴露，例如：

- `agentctl im read/reply/send/history/search/context`
- `agentctl subagent spawn`
- `agentctl media audio-qa`
- `cortex payload read/search/summarize/qa`
- `devicectl hd screenshot`

Action 的结果不塞回 Action 本身；工具结果默认成为下一条 Observation percept，显式解释工具的结果再成为解释性 Observation。

## Summary

Summary 只有一条正路：

```text
skill_end(report=...) -> current scope summary.md
```

它是 closed scope 向父 scope / future wake 暴露的默认内容。

禁止：

- 从 reply action 猜长期记忆。
- 从 reasoning 自动总结。
- 从 tool result 自动总结。
- 引入 wake summary / fallback summary / 多条并行摘要通路。

## IM / Environment CLI 方向

当前 Environment IM 能力不再作为一组独立 LLM 工具暴露，而是通过 shell 中的 `agentctl im` CLI 暴露：

| CLI | 语义 |
| --- | --- |
| `agentctl im read` | 读取用户/subagent/system-event 消息正文 |
| `agentctl im reply` | 回复用户 |
| `agentctl im send` | 给 subagent 或其他 Agent 发送 IM |
| `agentctl im history` | 主动翻阅 bounded IM 历史 |
| `agentctl im search` | 显式搜索 bounded IM 历史 |
| `agentctl im context` | 围绕 anchor message 读取 bounded 上下文 |

notification 的 claim / processed / failed 是 Runtime lifecycle 行为，不暴露成 LLM 工具。

当前直接 LLM 工具面只保留少量 harness 能力：`shell`、`display`、`skill_begin`、`skill_end`、`sleep`。旧 `chat_reply`、`chat_history`、`subagent_send`、`subagent_report`、`subagent_query`、`subagent_cancel` 不再作为 LLM 工具暴露；IM/subagent/audio/payload 能力统一走 shell CLI。

用户消息、subagent 消息、系统事件都走同一 sender/channel/thread/message_id 模型。

### IM history

Agent 可以主动翻 IM 历史，但不能恢复旧 `chat_history` 那种绕过 Environment 的第二观察通路。Environment 提供显式观察工具：

- `agentctl im history --thread-id ... --before ... --limit ...`
- `agentctl im search --query ... --thread-id ... --limit ...`
- `agentctl im context --anchor-message-id ... --before ... --after ...`

这些工具只返回 bounded percept 和 attachment/resource refs；调用结果写入 Cortex Observation。Prompt 仍不能自动注入历史正文，message read/status 也不能重新驱动 Agent loop。

## Activity Timeline

Activity Timeline 是用户可见的 Agent Monitor，不是诊断面板。

| Runtime/Cortex activity event | Timeline phase | 用户看到 |
| --- | --- | --- |
| notification | Observation precursor | 收到一条消息通知 |
| shell action: `agentctl im read` | Action | 读取用户消息 |
| shell result percept | Observation | 用户说：“...” |
| `reasoning_content` | Reasoning | 正在思考 / reasoning preview |
| tool call | Action | 执行命令 / 查看附件 / 派生子 Agent |
| tool result percept | Observation | 命令完成，显示状态、preview、head/tail、payload/ref |
| payload interpretation result | Observation | Agent 已分析 payload，得到失败原因/摘要/答案 |
| shell action: `agentctl im reply` | Action | 回复用户 |
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
5. Agent calls `shell` with `agentctl im read`.
6. CLI read result becomes Observation percept in Cortex.
7. Runtime records the read message ids as observed in the current wake checkpoint.
8. Agent acts: tools / reply / skill_end. `agentctl im reply` is blocked until current wake input notifications have been observed with `agentctl im read`.
9. Activity Timeline projects Cortex trace.
10. summary.md becomes future context after scope closes.
```

### 工具长输出

```text
1. Agent calls shell.
2. Shell returns terminal text with bounded preview/truncation metadata; large raw output is stored behind a payload/ref.
3. Cortex receives observation percept + payload_ref.
4. If needed, Agent calls `cortex payload read/search/summarize/qa` through shell.
5. Payload inspection or interpretation result becomes a new Observation.
```

### Subagent 消息

```text
1. Subagent sends IM to parent/sibling.
2. Environment creates notification.
3. Recipient calls `agentctl im read` through shell.
4. Message content becomes Observation percept.
5. Any response uses `agentctl im send` through shell.
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
| Developer diagnostics | diagnostic tooling / payload resolver / logs | 开发排障 | 用户面产品事实、Activity Timeline source of truth |

## 实施阶段

1. **P0 概念与 guardrail**：定义 notification / observation / action / reasoning / summary / percept / interpretation 的共享词表。
2. **P1 Environment 服务骨架**：收拢 event envelope、IM message、notification lifecycle 和 ref，不接管 domain truth。
3. **P2 Cortex 工作轨迹写入**：Runtime 写入 tool action、tool percept observation、explicit interpretation observation、LLM reasoning、reply action、scope close summary。
4. **P3 IM read path**：`agentctl im read` 读取结果自动写入 Cortex Observation percept。
5. **P4 Payload interpretation CLI**：为大 payload 建 ref，通过 `cortex payload read/search/summarize/qa` 提供显式解释能力，禁止自动 summary 塞回 Cortex。
6. **P5 Prompt notification-only**：LLM prompt 只注入 notification，不注入未观察消息正文。
7. **P6 Activity Timeline 投影**：Runtime 将 Cortex 工作轨迹物化为 Entangled activity projection；Timeline 从 Entangled cache 读取，开发诊断不作为用户面来源。
8. **P7 物理删除旧通路**：删除正文直塞 prompt、subagent report 特殊注入、旧 execution-log 用户面 fallback、旧 query/cancel/report 工具、tool result 自动 summary 等隐式路径。

## 一致性检查

任何新代码或新设计都要回答：

1. 这是一条 Notification，还是 Observation？
2. 如果是 Observation，它来自哪个工具？
3. 它是 percept，还是显式解释动作产生的 summary/QA/search/read 结果？
4. raw payload 是否只通过 ref 暴露，而不是默认进入 Cortex？
5. 它是否写入 Cortex active scope？
6. 它在 scope close 后是否只通过 `summary.md` 暴露？
7. Activity Timeline 展示的是 Entangled projection，还是偷偷成了 source of truth？
8. 这条路径是否绕过了 Environment / Cortex？
9. 这条路径是否把 authority prompt 环境化了？

## 已决策点

1. Prompt 主路径是 notification-only；消息正文必须通过 `agentctl im read` 观察。
2. notification processed lifecycle 由 Runtime 在 wake finalize / scope close 成功后完成，失败则保留 failed/pending 语义，不靠 UI read 状态驱动。
3. Activity Timeline 读取 Entangled `agent-activity-records` / `agent-activity-participants` projection；旧 execution-log 用户面 fallback 与旧 Cortex HTTP projection 物理删除。
4. Reasoning 直接来自 provider-authored `reasoning_content`，不再生成 monitor-only reasoning summary。
5. Environment 是独立业务域，当前随 Business/Runtime 部署，不做独立进程前置要求。
6. Payload interpretation 能力集合是 `cortex payload read/search/summarize/qa`；后续只优化语义与体验，不新增隐式自动总结通路。
7. Environment IM history 能力集合是 `agentctl im history/search/context`；它们是显式 observation CLI，不是自动 prompt memory。

## 后续增强

- Reasoning 默认展示长度和折叠策略可以继续由 App 体验层调优，但不得新增 LLM summary 通路。
- Developer diagnostics 可以继续改善排障入口，但不得复活 `execution-logs` 作为普通用户 Agent Monitor source。
- `step_ref` / `payload_ref` 命名需要继续收口，避免把 step join key 误叫成 result。

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
