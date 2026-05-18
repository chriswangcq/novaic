# PR-233D — Context Attached Input Observation Guardrails

| Field | Value |
| --- | --- |
| Status | `[x]` |
| Owner | Codex |
| Created | 2026-05-05 |
| Repos | `novaic-agent-runtime`, `novaic-cortex`, docs |
| Depends on | PR-233B, PR-233C |

## Objective

Ensure inputs attached to an active wake are actually observable by the LLM loop
through context preparation and `im_read`, and add guardrails so the old
"active means pending trigger" behavior does not return.

## Current-State Analysis

`context.prepare` injects Environment notification messages based on the wake
scope's `input_message_ids`. `im_read` defaults to the current wake's
`input_message_ids`. Once `session.attach_input` updates Cortex input metadata,
these paths should work, but the behavior must be covered by tests and docs.

## Implementation Scope

- Add tests proving attached input ids appear in prepared context.
- Add tests proving default `im_read` can observe attached ids.
- Update prompt/tool wording if needed so agents understand active wake inboxes.
- Add guardrail/lint or focused test to reject reintroducing the old active
  pending-trigger path for ordinary user IM.
- Update docs to describe:
  - active delivery
  - sleeping wake creation
  - dead recovery wake
  - structural archive of dangling child skill

## Expected Result

The running agent receives the user's next IM as an Environment notification in
the same wake, reads it with `im_read`, and responds without needing a new wake.

## Implementation Result

- Attached inputs flow through the same Cortex `input_message_ids` contract as
  initial wake inputs.
- Existing `context.read` and `im_read` handlers continue to observe wake
  `input_message_ids`; the new attach path updates that explicit input set.
- Runtime topic contract now includes `session.attach_input`, preventing the
  active inbox topic from being dropped silently.
- Queue tests guard against ordinary active user IMs returning to the old
  pending-trigger path.

## Verification

- Context handler tests.
- Environment tool handler tests.
- Runtime queue lifecycle tests.
- Documentation review against PR-233 acceptance criteria.

## Verification Result

- `tests/test_context_read_by_ids.py`
- `tests/unit/task_queue/test_environment_tool_handlers.py`
- `tests/test_runtime_tool_path_contract.py`
- Full `novaic-agent-runtime` module test suite: 205 passed.
