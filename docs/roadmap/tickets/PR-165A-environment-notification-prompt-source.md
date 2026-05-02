# PR-165A — Environment Notification Prompt Source

| Field | Value |
| --- | --- |
| Status | `[deployed]` |
| Owner | Codex |
| Created | 2026-05-02 |
| Repos | `novaic-agent-runtime`, docs |
| Depends on | PR-165 |
| Theme | Prompt boundary / Environment observation |

## Goal

Stop appending raw user/subagent message bodies to LLM context during
`context.read`. Instead, append bounded Environment notification hints that
contain notification ids and instruct the agent to call `im_read`.

`im_read` must support the promised default behavior: if the model omits
`notification_ids`, Runtime reads the current wake's `input_message_ids` from
Cortex meta and passes those ids to Business Environment.

## Plan

1. Analyze current `handle_context_read` and `im_read` executor paths.
2. Replace raw body merge with notification-only context messages.
3. Make notification context idempotent per notification id.
4. Teach `_exec_im_read` to use current wake meta ids when the model omits
   `notification_ids`.
5. Update/replace unit tests that currently assert raw message body injection.
6. Smoke test a user-message wake shape: prompt contains notification id, not
   raw text; `im_read` can fetch text.
7. Deploy, verify, and commit.

## Required Tests

- Runtime unit test: `context.read` appends notification hints and never raw
  message body.
- Runtime unit test: repeated `context.read` does not duplicate notification
  hints.
- Runtime unit test: `im_read({})` resolves current wake `input_message_ids`.
- Existing Runtime suite subset covering context read/order/session ids.

## Done Criteria

- LLM context has Environment notification hints, not hidden raw message facts.
- The model can observe message contents only through `im_read`.
- No fallback path reintroduces direct message body append.
- Tests, smoke, deploy, and git commit evidence are recorded here.

## Implementation Notes

- Runtime `context.read` no longer fetches Business `messages` rows or renders
  old IM-body headers. It appends `ENVIRONMENT_NOTIFICATION` system hints from
  `scope.meta.input_message_ids`.
- Runtime `im_read({})` now reads current wake `input_message_ids` from Cortex
  meta and passes them to Business Environment.
- Old helper code for `_render_im_content`, `_clean_message_body`, and sender
  header rendering was physically removed from Runtime.

## Validation

- Local Runtime full suite:
  `PYTHONPATH=.:../novaic-common pytest -q` -> `195 passed`.
- Production deploy:
  `./deploy services` completed; `./deploy status` reported all backend ports
  healthy and relay active.
- Production smoke:
  - Runtime `handle_context_read` appends notification hints and does not call
    `entity_get`.
  - Runtime `_exec_im_read({})` resolves current wake ids from Cortex meta.

## Git

- Runtime submodule commit: `2c48e4e feat(runtime): use environment notifications in prompt context`.
