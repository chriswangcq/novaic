# PR-153B — Centralize Buffered Input Ownership

| Field | Value |
| --- | --- |
| Status | `[open]` |
| Owner | Codex |
| Created | 2026-05-02 |
| Parent | PR-153 |
| Repos | novaic-business, novaic-agent-runtime, docs |

## Goal

Make the scope that actually starts through `session.init` own `input_message_ids` and message lifecycle `claimed` transitions. Subscriber should dispatch triggers and mark outbox delivery only; it should not append buffered inputs to Cortex or claim messages for an already-running scope.

## Why This Matters

The current buffered path lets Subscriber write `/v1/scope/append_input` and mark buffered messages as claimed by the active scope. If that active scope never reads those appended IDs before finalize, scope_end can still consume them. That is a lifecycle ownership bug.

## Implementation Plan

1. [ ] Merge buffered trigger `message_ids` in `SessionRepository` instead of overwriting the pending row.
2. [ ] Move `claimed` transition for wake inputs to `session.init`, after the wake scope is created and input IDs are appended.
3. [ ] Remove Subscriber's Cortex `append_input` dependency and buffered/saga-started `claimed` transition side effects.
4. [ ] Keep outbox delivery/idempotency behavior unchanged.

## Unit / Guardrail Tests

- [ ] SessionRepository tests prove pending trigger `message_ids` merge without loss.
- [ ] Runtime `session.init` tests prove input messages are claimed by the new wake scope.
- [ ] Subscriber tests prove buffered dispatch does not call Cortex `append_input` or message transition.
- [ ] Existing context/read, scope_end consumed, and aggregation tests pass.

## Smoke / Deploy / Git

- [ ] Smoke quick consecutive messages produce one active session plus pending restart without lost message IDs.
- [ ] Deploy Business and Runtime/Queue.
- [ ] Commit affected repos.
- [ ] Parent repo submodule/docs commit and push.
