# PR-56 — LLM system prompt must not reference tools absent from the call schema

| Field | Value |
|---|---|
| **Ticket** | PR-56 |
| **Status** | `[✓]` 2026-04-25 — implemented, tested, deployed |
| **Opened** | 2026-04-25 |
| **Owner** | __ |
| **Severity** | P1 correctness — the model is explicitly instructed to use tools that are not present in `tools[]`. |
| **Blocks** | Reliable first-turn behavior, tool-call predictability, prompt/tool contract hardening. |
| **Blocked by** | — |
| **Invariant** | Every tool name mentioned as callable in the LLM-visible prompt must exist in the same request's `tools[]`, unless it is explicitly described as unavailable or historical. |

## Bug

The latest LLM call still tells the agent to use non-existent callable surfaces:

- `使用 task_create 工具创建这些任务。`
- `每了解到一点就立即 drive_update_profile 保存`
- `重要发现写入笔记本`

The actual `tools[]` in the same request contains only:

```text
shell, skill_begin, skill_end, chat_reply,
subagent_spawn, subagent_send, subagent_report, subagent_query, subagent_cancel,
sleep
```

## Evidence

Source: user-provided LLM request snapshot on 2026-04-25 15:37 Asia/Shanghai.

The prompt body contains the phantom callable names, while the call schema does not expose matching function tools.

## Impact

- The model can attempt invalid tool calls or hallucinate unavailable APIs.
- The self-drive section becomes misleading noise for simple user questions.
- Debugging becomes harder because prompt text and executable capability disagree.

## Acceptance Criteria

- No LLM-visible prompt path names `task_create`, `drive_update_profile`, `notebook write/read/update`, or other callable tools unless the same request exposes them in `tools[]`.
- A generated LLM call snapshot for a simple chat turn has zero prompt/tool-name mismatches.
- Existing legitimate business-memory wording is either backed by real tools or phrased as product capability rather than direct tool instruction.

## Out of Scope

This ticket intentionally does not specify a repair method.
