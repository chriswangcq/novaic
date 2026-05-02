# PR-163C — Environment Tool Exposure and Old Communication Tool Cleanup

| Field | Value |
| --- | --- |
| Status | `[deployed]` |
| Owner | Codex |
| Created | 2026-05-02 |
| Parent | PR-163 |
| Repos | `novaic-common`, `novaic-agent-runtime`, `novaic-business`, `novaic-app`, docs |
| Depends on | PR-163B |

## Goal

Expose Environment IM tools to the LLM and remove superseded direct communication tools or aliases.

This is the cutover ticket. It must not leave `chat_reply`/`subagent_send`/`chat_history` as silent fallback branches if their product role is replaced by `im_reply`/`im_send`/`im_read`.

## Current-State Analysis

Completed 2026-05-02.

Current live state:

- `chat_reply`, `subagent_send`, and `chat_history` are still active schemas from `novaic-common/common/tools/llm_builtin.py`.
- Runtime dispatch still registers `_exec_chat_reply`, `_exec_subagent_send`, and `_exec_chat_history` in `task_queue/handlers/tool_handlers.py`.
- `im_read`, `im_reply`, and `im_send` exist as Environment schemas and Runtime candidate executors, but are not active LLM tools yet.
- Business now exposes internal Environment IM routes for read/reply/send.
- Prompt defaults and subagent parent instructions still name `chat_reply` and `subagent_send`.
- Runtime turn-finalizer logic still treats `chat_reply` as the reply/no-followup closer.
- Agent Monitor display contracts still map old communication tools, not `im_*`.

Cutover risk:

- `im_reply` can replace `chat_reply`, but the wake finalizer and prompt wording must switch in the same sequence.
- `im_send` can replace `subagent_send`, but subagent parent instructions must switch in the same sequence.
- `im_read` is not identical to `chat_history`; `chat_history` should be deleted only when the observation model no longer needs generic recent-chat lookup, or retained with a non-overlapping product reason.

## Small Tickets

- [x] [PR-163C1 — Activate Environment IM tool contracts](PR-163C1-activate-environment-im-tool-contracts.md): add `im_*` to active schema/executor/monitor/product contracts while leaving old tools active for one deployable checkpoint.
- [x] [PR-163C2 — Cut prompt and turn semantics to Environment IM](PR-163C2-cut-prompt-turn-semantics-to-environment-im.md): update prompt defaults, subagent parent instructions, no-tool warning, and turn-finalizer closer semantics to prefer `im_reply`/`im_send`.
- [x] [PR-163C3 — Delete superseded direct communication tools](PR-163C3-delete-superseded-communication-tools.md): physically remove old communication schemas/executors/routes or explicitly document any retained non-overlapping product role.

## Required Tests

- Common schema/executor/product semantics alignment tests.
- Runtime tool execution tests.
- Business route/service tests.
- Agent Monitor product-surface tests.
- Production smoke: user reply and subagent message still work through Environment.

## Deploy / Git

- Deploy Common, Business, Runtime, and App if monitor schema changes.
- Commit changed subrepos separately and update root pointers.

## Done Criteria

- Active LLM schemas expose the Environment tools.
- Superseded direct tools are physically deleted or explicitly retained with a documented product reason.
- Prompt wording no longer tells the agent to use old communication tools.
- Deployed 2026-05-02 with production smoke confirming schema/executor/display/semantics alignment.
