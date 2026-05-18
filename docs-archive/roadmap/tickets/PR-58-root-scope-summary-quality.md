# PR-58 — Root scope summaries must be future-self summaries, not pasted user-facing replies

| Field | Value |
|---|---|
| **Ticket** | PR-58 |
| **Status** | `[✓]` 2026-04-25 — implemented, tested, deployed |
| **Opened** | 2026-04-25 |
| **Owner** | __ |
| **Severity** | P1 continuity quality — bad summaries poison the next wake's context. |
| **Blocks** | Reliable `<PREV_SCOPE_HISTORY>` behavior and any future compact memory work. |
| **Blocked by** | — |
| **Invariant** | Root scope history entries should summarize intent, action, and open thread for the next wake; they should not be verbatim `chat_reply` fallbacks. |

## Bug

The latest call's `<PREV_SCOPE_HISTORY>` contains a user-facing reply as the prior scope summary:

```text
我叫**小牛**，是你桌面上的 AI 伙伴～很高兴认识你！

顺便问一下，我应该怎么称呼你呢？
```

That is not a continuity summary for future self. It is the exact text the user already saw.

## Evidence

Source: user-provided LLM request snapshot on 2026-04-25 15:37 Asia/Shanghai.

The same request also contains `skill_end` instructions saying root meta summaries must not paste `chat_reply.message` verbatim, which means the generated context contradicts its own stated contract.

## Impact

- `<PREV_SCOPE_HISTORY>` becomes redundant transcript text instead of compressed state.
- The model loses actionable context like "user asked my name; awaiting preferred address."
- Repeated fallback summaries can accumulate into noisy, misleading long-term context.

## Acceptance Criteria

- For a normal one-turn chat, the next wake's `<PREV_SCOPE_HISTORY>` contains a compact future-self summary rather than the previous `chat_reply` text.
- If the LLM omits `skill_end`, fallback behavior still produces a useful continuity summary or clearly marks the summary as fallback.
- The history entry preserves user intent and open thread without duplicating the user-facing reply verbatim.

## Out of Scope

This ticket intentionally does not specify a repair method.
