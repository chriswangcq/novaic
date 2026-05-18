# PR-163B — Runtime Executors for Environment IM Tools

| Field | Value |
| --- | --- |
| Status | `[deployed]` |
| Owner | Codex |
| Created | 2026-05-02 |
| Parent | PR-163 |
| Repos | `novaic-agent-runtime`, `novaic-business`, `novaic-common`, docs |
| Depends on | PR-163A |

## Goal

Implement Runtime executors and Business service/API surfaces for `im_read`, `im_reply`, and `im_send`, but keep active exposure gated until PR-163C.

## Required Tests

- Runtime unit tests for all executors.
- Business service/API tests for Environment read/reply/send.
- Failure semantics tests for missing ids, missing target, invalid sender, and storage/transition failure.

## Implementation Result

Completed 2026-05-02.

- Added Business internal Environment IM routes:
  - `POST /internal/environment/{agent_id}/im/read`
  - `POST /internal/environment/{agent_id}/im/reply`
  - `POST /internal/environment/{agent_id}/im/send`
- Added `EnvironmentService.read_messages()` and `EnvironmentService.create_agent_reply()` so Runtime callers do not touch storage directly.
- Added Runtime candidate executors in `task_queue/handlers/environment_tool_handlers.py`.
- Kept `im_read`, `im_reply`, and `im_send` out of active LLM tool exposure until PR-163C.

## Deploy / Git

- Deploy Business + Runtime after tests.
- Commit changed subrepos separately and update root pointers.

Result:

- `novaic-business` commit `e7f95ef` — `feat(business): add environment im internal api`
- `novaic-agent-runtime` commit `116fd04` — `feat(runtime): add environment im candidate executors`
- Deployed via `./deploy services`.
- Production smoke verified candidate tools import and remain inactive:
  - `env_tools ['im_read', 'im_reply', 'im_send']`
  - `executors ['im_read', 'im_reply', 'im_send']`
  - `active_intersection []`
  - Business routes present for `/environment/{agent_id}/im/read|reply|send`.

## Verification

- `PYTHONPATH=.:../novaic-common pytest tests/test_environment_repository.py tests/test_environment_internal_api.py tests/test_pr160_message_content_shape.py tests/test_bulk_transition.py`
  - `24 passed, 1 warning`
- `PYTHONPATH=.:../novaic-common pytest`
  - Runtime full suite: `208 passed`

## Done Criteria

- Executors exist and call Environment service boundaries.
- Candidate schemas have matching executor names.
- Existing `chat_reply`, `subagent_send`, and `chat_history` behavior remains unchanged until PR-163C.
