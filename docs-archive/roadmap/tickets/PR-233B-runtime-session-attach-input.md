# PR-233B — Runtime `session.attach_input` Active Wake Delivery

| Field | Value |
| --- | --- |
| Status | `[x]` |
| Owner | Codex |
| Created | 2026-05-05 |
| Repos | `novaic-agent-runtime`, `novaic-cortex`, docs |
| Depends on | PR-233A |

## Objective

Add a runtime task that appends newly delivered IM notification ids to the
current wake scope and claims the corresponding Environment notifications,
without opening a new wake.

## Current-State Analysis

`task_queue/handlers/runtime_handlers.py::handle_session_init()` already owns
the initial wake input registration:

- creates the wake scope
- calls Cortex `append_scope_input`
- transitions Environment notifications to `claimed`

There is no equivalent handler for "the wake is already active; attach more
input to this same wake".

## Implementation Scope

- Add `TaskTopics.SESSION_ATTACH_INPUT`.
- Add a runtime handler, preferably `handle_session_attach_input`.
- Required payload should include explicit values:
  - `agent_id`
  - `subagent_id`
  - `user_id`
  - `scope_id`
  - `agent_root_scope_id`
  - `message_ids`
  - optional `wake_scope_path`
- The handler must:
  - validate non-empty `message_ids`
  - append ids to Cortex wake input
  - transition notifications to `claimed`
  - return structured counts/status
- Do not discover "current scope" implicitly inside the handler.

## Expected Result

When Queue routes an active IM to `session.attach_input`, Cortex wake metadata
contains the new input ids, and the next context preparation can inject
Environment notifications for those ids.

## Implementation Result

- Added `TaskTopics.SESSION_ATTACH_INPUT`.
- Added `handle_session_attach_input()` with explicit payload validation.
- The handler appends `message_ids` to the explicit `scope_id` through Cortex
  and claims Environment notifications with reason `session_attach_input`.
- Shared `derive_agent_root_scope_id()` keeps Queue and Runtime payloads aligned
  without hidden scope lookup.

## Verification

- Handler unit test with fake Cortex bridge and fake Business client.
- Test missing `message_ids` fails clearly.
- Test handler uses explicit `scope_id` / `agent_root_scope_id`, not hidden
  current-session state.

## Verification Result

- `tests/test_pr233_active_inbox_dispatch.py`
- `tests/test_session_init_message_ids.py`
