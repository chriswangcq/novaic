# PR-196A — Runtime Architecture Current Path

| Field | Value |
|---|---|
| Status | Done |
| Parent | [PR-196](PR-196-runtime-queue-gateway-centric-doc-cleanup.md) |
| Repo | docs |

## Task

Rewrite `docs/runtime-architecture.md` so it describes the current Runtime path:

`App → Entangled action → Business Environment notification → Subscriber → Queue Service → Saga/Task Workers → Cortex / LLM Factory / tools → Business/Entangled reply projection`.

## Tests / Checks

- Grep: no `_chat_messages`, `Gateway.store`, or “反开给 Gateway” in `docs/runtime-architecture.md`.
- Manual read confirms Runtime does not appear to be Gateway-owned.

## Result

`docs/runtime-architecture.md` was rewritten around App → Entangled action → Business Environment → Subscriber → Queue Service → Runtime → Cortex/LLM Factory/tools.
