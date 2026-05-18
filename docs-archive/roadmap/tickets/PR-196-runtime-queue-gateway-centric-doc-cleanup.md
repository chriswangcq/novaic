# PR-196 — Runtime / Queue Gateway-Centric Documentation Cleanup

| Field | Value |
|---|---|
| Status | Done |
| Owner | Codex |
| Repos | novaic-agent-runtime, docs |
| Parent theme | Remove misleading Gateway-centric runtime narratives |

## Problem

Some Runtime and Queue documentation/comments still describe the old world where Gateway owned task DBs, handler execution, business entry, or Runtime inputs/outputs. The live path is Environment notification → Subscriber → Queue Service → Runtime workers, with Cortex and Business as explicit service boundaries.

## Small Tickets

- [x] [PR-196A](PR-196A-runtime-architecture-current-path.md) — Rewrite `docs/runtime-architecture.md` to the current Environment/Queue/Cortex/Factory path.
- [x] [PR-196B](PR-196B-queue-service-comment-cleanup.md) — Replace Queue Service and Saga repository comments that still say Gateway owns queue DB or handler/business entry.
- [x] [PR-196C](PR-196C-runtime-readme-entrypoint-wording.md) — Update Runtime README / entrypoint / LLM config wording so Business, Queue, Cortex, and Factory are the named collaborators.

## Result

Runtime documentation now describes Environment notification → Subscriber → Queue → Runtime → Cortex/Factory/Business. Queue Service comments identify Queue Service as `queue.db` owner. Runtime README/entrypoint/LLM handler wording no longer names Gateway as product state or LLM config owner.

## Acceptance

- Runtime docs no longer say Gateway writes `_chat_messages`, owns queue DB, or receives final status callbacks.
- Queue comments say Queue Service owns `queue.db`.
- Runtime comments/docstrings identify Business as the LLM config/product API owner.
- No behavior changes beyond documentation/comment cleanup.
- Targeted grep verifies old phrases are gone from active docs/source.
