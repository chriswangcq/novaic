# Agent Root Scope Continuity 方案

> Opened: 2026-04-25
> Status: draft for implementation tickets PR-64..PR-69

## 目标

把跨 wake 连续性重新收敛回 Cortex 的 scope-tree 模型：

- active scope 内现有 DFS 逻辑保持不变；
- 跨 wake 不再主要依赖 `<PREV_SCOPE_HISTORY>` / `<PREV_SCOPE_TAIL>` 拼贴；
- 引入一个长期 active 的 agent root scope；
- 每次 wake 是 agent root 下的一个 child scope；
- 已结束 wake child scope 用 `summary.md` 折叠，当前 wake child scope 展开；
- `summary.md` 只表示 scope end report，不再由 `chat_reply` 自动派生；
- 用户画像暂不纳入本轮设计；
- 旧的污染性 archived scope 数据直接清理，不做兼容迁移。

## 核心模型

### Scope 层级

```text
agent-root-scope  (per user_id + agent_id + subagent_id, long-lived active)
├── wake-scope-001  (closed, folded by summary.md)
├── wake-scope-002  (closed, folded by summary.md)
└── wake-scope-003  (open, current wake expanded)
    ├── skill-A     (closed, folded by summary.md)
    └── skill-B     (open, expanded)
```

`agent-root-scope` 是系统管理对象，不是 LLM 需要关闭的工作 scope。LLM 只需要关闭当前 wake scope 和自己显式创建的子 skill scope。

### LLM 上下文装配

LLM context 应从 agent root scope 开始装配：

1. 当前系统提示词。
2. agent root scope 的 DFS 时间线。
3. closed wake child scopes 渲染为 fold summary。
4. current wake child scope 展开其消息和步骤。
5. current wake 内的 closed skill scopes 继续按现有 DFS fold 逻辑处理。
6. 当前用户消息保持最高任务优先级，不被历史 summary 当成新请求。

这意味着跨 wake 连续性来自同一棵 scope tree，而不是额外的 rolling history system block。

## `summary.md` 语义

`summary.md` 是 scope end report。

允许写入的来源：

- LLM 调用 `skill_end(scope_id=<current_scope>, report="...")`。
- 系统兜底关闭未关闭 scope 时，可以留下空 report 或显式 auto-close 标记，但不能把 `chat_reply.message` 伪造成 summary。

不再允许：

- 从 `chat_reply` 自动截取内容写入 `summary.md`。
- 将用户可见回复原文作为 root/wake summary。
- 用 summary 代替用户画像事实存储。

## 生命周期

### 初始化

`session.init` 不再创建一个会被 rest 归档的 root scope 作为本轮全部上下文。

新流程：

1. 确保 `(user_id, agent_id, subagent_id)` 对应的 agent root scope 存在且 active。
2. 在 agent root scope 下创建本次 wake child scope。
3. 把本次 trigger message 绑定到 wake child scope。
4. LLM 准备上下文时，从 agent root scope 装配，而不是从 wake child scope 单独装配。

### 执行

工具步骤仍写入当前最深 active scope。当前 wake scope 是默认 active scope；LLM 可继续打开子 skill scope。

### 结束

本次 wake 结束时关闭 wake child scope，不关闭 agent root scope。

关闭 wake child scope 时：

- 如果 LLM 已调用 `skill_end(..., report=...)`，使用该 report 写入 `summary.md`。
- 如果 LLM 没有关闭，系统可以 auto-close，但不能用 `chat_reply` 派生摘要。

## 废弃旧跨 wake 注入

agent root scope 方案稳定后，下列内容从主 LLM 调用路径移除或默认关闭：

- `<PREV_SCOPE_HISTORY>`
- `<PREV_SCOPE_TAIL>`
- `previous_scope_id` 作为主连续性锚点
- `last_scope_id` 驱动的 wake tail 注入
- chat_reply-derived root summary fallback

这些可以短期保留为 legacy flag，但新路径不依赖它们。

## 数据策略

旧数据不迁移。

原因：

- 现有 archived summaries 已含用户可见回复原文，语义污染严重；
- 迁移会把旧错误语义继续带入新模型；
- 当前目标是验证新 scope-tree 连续性，不是保留历史聊天体验。

施工时直接清理目标 agent 的 archived scopes、active scopes、runtime active sessions、last_scope_id 等旧状态。

## 风险

- Agent root scope 永远 active，会导致 root step timeline 无限增长，需要后续 compact/fusion 策略。
- 如果 LLM 不写 `skill_end.report`，wake summary 会为空，跨 wake 只剩结构但缺语义。
- ContextEngine 当前 closed-scope fold 依赖 `context.jsonl` 中的 `skill_begin` 锚点；系统创建的 wake child scope 需要补齐锚点或升级为 step-tree-first renderer。
- 现有 Runtime 大量地方默认 `scope_id` 等于 root scope id，新模型需要区分 `agent_root_scope_id` 和 `wake_scope_id`。

## 成功标准

- 连续三轮用户对话后，LLM 调用不再出现 `<PREV_SCOPE_HISTORY>` / `<PREV_SCOPE_TAIL>`。
- LLM 调用中的历史上下文来自 agent root DFS fold。
- 上一轮 wake 的细节被折叠为 wake scope 的 `summary.md`。
- 当前 wake 仍展开，用户当前消息可见且优先级明确。
- `summary.md` 内容等于 `skill_end.report`，不是 `chat_reply` 截断文本。
