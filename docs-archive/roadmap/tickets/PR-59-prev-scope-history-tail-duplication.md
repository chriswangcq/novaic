# PR-59 — `<PREV_SCOPE_HISTORY>` and `<PREV_SCOPE_TAIL>` should not duplicate the same short prior turn

| Field | Value |
|---|---|
| **Ticket** | PR-59 |
| **Status** | `[✓]` 2026-04-25 — implemented, tested, deployed |
| **Opened** | 2026-04-25 |
| **Owner** | __ |
| **Severity** | P2 context efficiency — duplicated prior turns waste tokens and bias the model toward stale text. |
| **Blocks** | Context budget cleanup and clean discussion of the R9 scope-history design. |
| **Blocked by** | PR-58 should clarify summary quality. |
| **Invariant** | A prior scope should not be injected twice at near-identical detail unless the two blocks serve clearly distinct purposes. |

## Bug

The latest LLM call includes both:

- `<PREV_SCOPE_HISTORY>` with the prior user-facing reply.
- `<PREV_SCOPE_TAIL>` with the same prior reply plus the triggering user message.

For a short one-turn prior scope, this gives the model effectively the same content twice.

## Evidence

Source: user-provided LLM request snapshot on 2026-04-25 15:37 Asia/Shanghai.

The prior scope text `我叫**小牛**...` appears in `<PREV_SCOPE_HISTORY>` and again inside `<PREV_SCOPE_TAIL>`.

## Impact

- Context budget is spent on repeated low-value text.
- Recency weighting may overemphasize the previous greeting.
- It becomes harder to inspect whether the DFS scope assembly is doing the right thing, because history and tail are not clearly separated.

## Acceptance Criteria

- A simple two-turn conversation does not inject the same assistant reply in both blocks without an explicit reason.
- `<PREV_SCOPE_HISTORY>` and `<PREV_SCOPE_TAIL>` have clearly distinct roles in generated snapshots.
- Token usage for short prior scopes decreases or remains bounded without losing the last-turn facts.

## Out of Scope

This ticket intentionally does not specify a repair method.
