# PR-63 — LLM-visible `shell` capability needs an explicit safety boundary

| Field | Value |
|---|---|
| **Ticket** | PR-63 |
| **Status** | `[✓]` 2026-04-25 — implemented, tested, deployed |
| **Opened** | 2026-04-25 |
| **Owner** | __ |
| **Severity** | P1 safety/operations — shell is now exposed directly to the LLM, but the prompt does not define enough operational boundaries. |
| **Blocks** | Safe rollout of LLM-facing shell, agent autonomy, and server-side cleanup tasks. |
| **Blocked by** | Shell exposure in the LLM call. |
| **Invariant** | Any LLM-facing shell tool must have explicit rules for destructive operations, external side effects, secrets, network access, and output handling. |

## Bug

The latest `tools[]` correctly includes `shell`, and the prompt's quick reference lists:

```text
shell(command="你的命令", timeout=30)
```

But the LLM-visible contract does not clearly define boundaries for:

- destructive filesystem/database commands
- server mutations and deploys
- secret-bearing output
- network or external side effects
- large output handling

The prompt has general wording like "对外部操作谨慎", but that is not a shell-specific operating contract.

## Evidence

Source: user-provided LLM request snapshot on 2026-04-25 15:37 Asia/Shanghai.

`shell` is the first exposed tool, but its visible description only says it executes sandbox shell commands for local inspection, file operations, tests, scripts, or CLI tools.

## Impact

- The model may run commands that are technically available but operationally unsafe.
- It is hard to distinguish allowed local inspection from risky production/server mutation.
- Future autonomy features will inherit an underspecified command boundary.

## Acceptance Criteria

- The LLM-visible shell contract defines safety expectations for destructive commands, external effects, secrets, network access, and long output.
- Simple read-only commands remain easy for the model to use.
- High-risk command categories are explicitly distinguishable in prompt or tool policy.

## Out of Scope

This ticket intentionally does not specify a repair method.
