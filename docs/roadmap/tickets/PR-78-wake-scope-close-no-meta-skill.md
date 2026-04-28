# PR-78 — Make wake the LLM-closed turn scope and remove meta skill

| Field | Value |
| --- | --- |
| Status | `[x]` deployed + smoke verified |
| Severity | P0 continuity correctness |
| Owner | Codex |
| Branch | `codex/focus-new-llm-context` |

## Problem

The live LLM calls still exposed a system-opened `meta` scope and treated the current wake as a hidden lifecycle container. This made simple preference facts like "叫大哥" disappear from later calls unless the model happened to create an extra child skill. The resulting context contradicted the intended Cortex model: maintain a LIFO scope tree, assemble the LLM context from that tree, and fold closed scopes by their own `summary.md`.

## Desired Contract

- `agent-root` is the durable root and is never closed by the LLM.
- Each wake is a real active scope under `agent-root`.
- The active scope stack shown to the LLM includes the current wake.
- After the user-facing reply, the LLM closes the current wake with `skill_end(report=...)`.
- That report is persisted verbatim as the wake scope's `summary.md`.
- Closed wake scopes with non-empty summaries render as folded scope summaries in later agent-root DFS context.
- Blank closed wakes remain cheap structural containers and may expose nested child summaries.
- There is no auto-opened `meta` scope or `meta` skill.

## Implementation Checklist

- [x] Runtime wake saga: remove auto meta skill creation.
- [x] Runtime LLM context handler: show current wake in active stack.
- [x] Runtime turn finalizer: after `chat_reply` with a non-empty stack, continue so the LLM can call `skill_end`.
- [x] Cortex fold renderer: render non-empty closed wake summaries.
- [x] Cortex tool descriptions: teach "reply, then close current wake with `skill_end(report=...)`"; do not mention meta scope.
- [x] Business default prompt: align continuity instructions with wake-as-turn-scope contract.
- [x] Clean active-code wording that still says auto meta / meta skill / root meta scope.

## Unit Tests

- [x] Cortex: closed wake summary appears before the next wake's current user message.
- [x] Cortex: blank wake with nested child summary still exposes the child summary.
- [x] Runtime: wake saga creates only root + wake, no auto meta step.
- [x] Runtime: active stack injection includes the wake scope id.
- [x] Runtime: chat_reply-only with non-empty stack continues thinking.
- [x] Runtime prompt contract: no PREV blocks, no root/meta close instruction, close current wake instruction present.
- [x] Business prompt defaults: wake-as-turn-scope contract present.

## Smoke Test

- [x] Create or use a test agent-root with wake 1 summary `User asked to be called 大哥.`
- [x] Prepare wake 2 context with user asking `我叫啥`.
- [x] Verify the LLM request contains the folded wake 1 summary and the current user message, with no `meta-*` active scope.
- [x] Verify the deployed API path can close the wake with `skill_end(report=...)` and then prepare the next wake from the folded summary.

## Deployment

- [x] Deploy Cortex.
- [x] Deploy agent-runtime.
- [x] Deploy business prompt defaults.
- [x] Check `/health` and worker logs for `skill.ended`, `scope.child_completed`, and absence of auto meta creation.

## GitHub / Commit Work

- [x] Commit `novaic-cortex` changes.
- [x] Commit `novaic-agent-runtime` changes.
- [x] Commit `novaic-business` changes.
- [x] Commit parent repo submodule pointers and this ticket.
- [x] Push submodule commits and parent branch.
