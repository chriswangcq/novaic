# SubAgent IM Identity Binding

## Problem

同一 agent 下多个 subagent 共享 Cortex shell/workspace 是协作团队模型，不需要互相防贼式隔离。但 IM 的 outbound 行为必须有清晰署名：`reply`、`send`、`subagent spawn` 不能因为缺少 subagent 身份而落成默认 `"agent"` 或 `"main"`，否则审计和消息路由会变脏。

当前代码通过 Runtime 注入 `NOVAIC_SUBAGENT_ID`，`agentctl` 再把它作为 `sender_subagent_id` / `parent_subagent_id` 传给 Business。这个方向是对的，但需要把它设计成明确契约并用代码/测试锁住。

## Success Criteria

- 明确设计：同 agent 内部是团队共享边界，不做强隔离；subagent 身份通过每次 shell exec 的 `NOVAIC_SUBAGENT_ID` 注入。
- `agentctl im reply`、`agentctl im send`、`agentctl subagent spawn` 必须要求当前 subagent id，不能静默 fallback。
- Business internal IM reply/send API 必须要求 non-empty `sender_subagent_id`。
- 测试证明同一 agent/workspace 中不同 `NOVAIC_SUBAGENT_ID` 会产生不同 sender/parent 身份。
- 测试证明缺少 subagent id 的 outbound 操作会失败。
- 相关 Cortex / Business / Runtime 测试通过。
