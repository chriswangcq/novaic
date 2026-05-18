# PR-163C2 — Cut Prompt and Turn Semantics to Environment IM

| Field | Value |
| --- | --- |
| Status | `[deployed]` |
| Owner | Codex |
| Created | 2026-05-02 |
| Parent | PR-163C |
| Repos | `novaic-business`, `novaic-agent-runtime`, docs |
| Depends on | PR-163C1 |

## Goal

Switch active agent instructions and turn semantics from old communication tools to Environment IM tools.

## Scope

- Prompt defaults should instruct user replies through `im_reply`, not `chat_reply`.
- Subagent parent/child communication instructions should use `im_send`, not `subagent_send`.
- No-tool warning should point to `im_reply`.
- Turn-finalizer reply/no-followup logic should recognize `im_reply` as the user-reply closer.

## Required Tests

- Business prompt builder/default tests.
- Runtime turn-finalizer tests.
- Runtime no-tool warning tests.
- Prompt smoke verifying no default instruction tells the agent to use `chat_reply` for normal user replies.

## Deploy / Git

- Commit `novaic-business`.
- Commit `novaic-agent-runtime`.
- Deploy via `./deploy services`.
- Production smoke: new LLM context names `im_reply`/`im_send` in instructions.

Result:

- `novaic-common` commit `71c71fb` — `feat(common): point prompt contract to environment im`
- `novaic-business` commit `d33b156` — `feat(business): guide agents to environment im tools`
- `novaic-agent-runtime` commit `d619bf6` — `feat(runtime): treat im_reply as turn closer`
- Deployed via `./deploy services`.
- Production smoke:
  - `has_im_reply True`
  - `has_im_send True`
  - `has_chat_reply False`
  - `has_subagent_send False`
  - `turn_closers ['im_reply']`

## Verification

- `PYTHONPATH=.:../novaic-agent-runtime pytest`
  - Common full suite: `112 passed`
- `PYTHONPATH=.:../novaic-common pytest`
  - Runtime full suite: `208 passed`
- `PYTHONPATH=.:../novaic-common pytest tests/test_pr111_system_prompt_builder.py tests/test_pr72_prompt_defaults_contract.py tests/test_environment_repository.py tests/test_environment_internal_api.py tests/test_pr160_message_content_shape.py tests/test_bulk_transition.py`
  - Business selected suite: `34 passed, 1 warning`

## Done Criteria

- Agent behavior guidance points at Environment IM.
- Old tools may still exist only as temporary compatibility until PR-163C3.
