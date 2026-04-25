# PR-57 — LLM memory wording must match the active R9 scope-continuity contract

| Field | Value |
|---|---|
| **Ticket** | PR-57 |
| **Status** | `[✓]` 2026-04-25 — implemented, tested, deployed |
| **Opened** | 2026-04-25 |
| **Owner** | __ |
| **Severity** | P1 product contract drift — the prompt claims a memory/notebook model that is not what the current call actually supplies. |
| **Blocks** | Discussion of whether Cortex context is reasonable, because the model is being told the wrong continuity mechanism. |
| **Blocked by** | PR-55 cleanup should be conceptually settled. |
| **Invariant** | The LLM-visible memory story must describe the mechanisms actually present in the request payload. |

## Bug

The latest prompt says the agent has persistent memory and notebook files as its continuity:

```text
你有持久记忆和学习能力，能够跨对话记住用户的偏好和习惯。
每次 session 你都是全新醒来的。你的笔记本和记忆文件就是你的延续。读它们，更新它们，它们是你持久存在的方式。
```

But the active LLM payload only shows the new scope-continuity surface:

- `<PREV_SCOPE_HISTORY>`
- `<PREV_SCOPE_TAIL>`
- `skill_end.report` continuity protocol

There is no direct memory or notebook tool in `tools[]`, and the old Recall path has been removed.

## Evidence

Source: user-provided LLM request snapshot on 2026-04-25 15:37 Asia/Shanghai, plus current cleanup direction:

- Old Recall remnants removed.
- Shell is now a generic local command tool, not a memory-specific first-class API.
- R9 continuity is scope tree + summaries/tail, not ad hoc recovered memory system messages.

## Impact

- The model may overestimate its long-term memory and make false claims to the user.
- The model may try to read or update a "notebook" when no such first-class tool is available.
- Product behavior becomes hard to reason about because the prompt names two different continuity systems.

## Acceptance Criteria

- The prompt's memory section accurately explains the active scope-history/tail continuity contract.
- The prompt does not imply autonomous persistent memory writes unless an executable path exists in the same call.
- A fresh LLM call after cleanup contains no legacy Recall/notebook framing that contradicts R9 scope continuity.

## Out of Scope

This ticket intentionally does not specify a repair method.
