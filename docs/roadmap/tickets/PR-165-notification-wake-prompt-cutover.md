# PR-165 — Notification Wake and Prompt Cutover

| Field | Value |
| --- | --- |
| Status | `[open]` |
| Owner | Codex |
| Created | 2026-05-02 |
| Repos | `novaic-business`, `novaic-agent-runtime`, `novaic-cortex`, docs |
| Depends on | PR-164 |
| Theme | Agent loop / prompt boundary |

## Goal

Move agent wake and prompt assembly to the subject/environment model: prompt receives environment notifications and active work trajectory, not raw unobserved message bodies as hidden context.

The agent should explicitly read the environment when it needs message contents. Subscriber/session code should own triggering and serialization, while Cortex owns work trajectory and Environment owns notification lifecycle.

## Required Process

1. Analyze subscriber, queue, session, prompt builder, pending trigger, and wake finalize ownership.
2. Create small tickets for notification delivery, prompt cutover, and lifecycle finalization.
3. Implement one small ticket at a time.
4. For each small ticket: unit tests, smoke test, deploy plan/result, Git commit/merge evidence.
5. Confirm the old raw-message prompt path is deleted or guarded before closing.

## Planned Small Tickets

- [x] [PR-165A — Environment notification prompt source](PR-165A-environment-notification-prompt-source.md)
- [PR-165B — Prompt and tool wording notification-only cutover](PR-165B-prompt-tool-wording-notification-only.md)
- [PR-165C — Notification lifecycle close/failure semantics](PR-165C-notification-lifecycle-close-failure.md)

## Current-State Analysis

PR-164 completed the Cortex observation/payload/reasoning trace pieces, but
Runtime still has one direct raw-message prompt path:

- `task_queue/handlers/context_handlers.py::handle_context_read` reads
  `scope.meta.input_message_ids`, fetches each `messages` row from Business,
  renders an IM header plus the original body, and appends that as a
  `role=user` context message before every LLM call.
- PR-165A fixed the Runtime hot path: `context.read` now appends
  notification-only hints and `im_read({})` resolves current wake
  `input_message_ids` from Cortex meta.
- Business prompt text still documents “用户侧消息 role=user content 以 IM
  header 开头” and therefore teaches the model to expect already-observed
  message bodies.
- Session lifecycle already has the right structural ownership:
  Subscriber/Queue pass `message_ids`; Runtime `session_init` stores them in
  wake meta and claims them; `wake_finalize`/`scope_end` consumes them after
  successful archive. The gap is prompt assembly and default `im_read`.

## Boundary Invariants

- Message delivery trigger is not cognitive memory.
- Read/unread UI status does not control the agent loop.
- Prompt builder does not smuggle raw IM bodies into context.
- Session serialization has one owner.

## Done Criteria

- Same-sender message bursts still behave correctly.
- Agent can answer only after observing via tools.
- Wake close writes the intended scope summary.
- Guards prevent reintroducing raw IM replay or wake-summary fallback paths.
