# PR-165B — Prompt and Tool Wording Notification-Only Cutover

| Field | Value |
| --- | --- |
| Status | `[deployed]` |
| Owner | Codex |
| Created | 2026-05-02 |
| Repos | `novaic-business`, `novaic-common`, docs |
| Depends on | PR-165A |
| Theme | Prompt contract |

## Goal

Make Business prompt text and LLM-visible tool descriptions match the new
subject/environment model. The prompt should say the agent receives
Environment notifications, not already-observed IM bodies.

## Plan

1. Update Business prompt sections that still describe raw IM body injection.
2. Ensure behavior guide tells the model to call `im_read` before answering
   message-triggered wakes.
3. Keep authority prompt direct; only environment events are notification-only.
4. Add prompt snapshot/contract tests that fail on old IM-header-body wording.
5. Smoke a prompt preview/LLM request and confirm wording alignment.
6. Deploy, verify, and commit.

## Required Tests

- Business prompt unit test forbids the old “实际消息内容 already in content”
  contract.
- Business prompt unit test requires notification + `im_read` wording.
- Common tool schema tests continue to pass.

## Done Criteria

- Prompt and tools describe one path: notification -> `im_read` observation.
- No Business prompt text implies unobserved message bodies are already facts.
- Tests, smoke, deploy, and git commit evidence are recorded here.

## Implementation Notes

- Business prompt now documents `[Environment notification]` as a notification
  only, not message content.
- Default behavior guide tells the model to call `im_read(...)` before
  replying when notification hints appear.
- Default capability list includes `im_read`.
- Common prompt fragment contract now requires `im_read`.

## Validation

- Business focused prompt tests:
  `PYTHONPATH=.:../novaic-common pytest -q tests/test_pr111_system_prompt_builder.py tests/test_pr72_prompt_defaults_contract.py tests/test_pr144_prompt_memory_boundary.py tests/test_pr159_product_context_boundary.py`
  -> `15 passed`.
- Business full suite:
  `PYTHONPATH=.:../novaic-common pytest -q` -> `196 passed`.
- Common focused tests:
  `PYTHONPATH=. pytest -q tests/test_environment_tool_schemas.py tests/test_environment_contract.py tests/test_tool_definitions_contract.py`
  -> `17 passed`.
- Common full suite:
  `PYTHONPATH=.:../novaic-agent-runtime pytest -q` -> `119 passed`.
- Production deploy:
  `./deploy services` completed; `./deploy status` reported all backend ports
  healthy and relay active.
- Production smoke:
  Prompt build includes `[Environment notification]` and
  `im_read(notification_ids...)`, and excludes the old `IM header` /
  `<实际消息内容>` wording.

## Git

- Common submodule commit: `b713127 test(common): require im_read in prompt contract`.
- Business submodule commit: `4ef1dc0 feat(business): describe environment notification prompt contract`.
