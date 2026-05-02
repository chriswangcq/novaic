# PR-163C1 — Activate Environment IM Tool Contracts

| Field | Value |
| --- | --- |
| Status | `[deployed]` |
| Owner | Codex |
| Created | 2026-05-02 |
| Parent | PR-163C |
| Repos | `novaic-common`, `novaic-agent-runtime`, docs |
| Depends on | PR-163B |

## Goal

Make `im_read`, `im_reply`, and `im_send` first-class active tool contracts by wiring schema exposure, Runtime executor dispatch, product semantics, and Agent Monitor display contracts.

This is an intermediate cutover checkpoint: old direct communication tools remain active until PR-163C2/PR-163C3 switch prompts and delete superseded paths.

## Required Tests

- Common schema contract: Environment tools are active.
- Common product semantics / execution-log display contract includes `im_*`.
- Runtime contract: active schema names, executor names, monitor tool names, and product semantics keys match.
- Runtime unit tests for `im_*` executors still pass.

## Deploy / Git

- Commit `novaic-common`.
- Commit `novaic-agent-runtime`.
- Deploy via `./deploy services`.
- Production smoke: `im_*` appear in active schemas and Runtime executors.

Result:

- `novaic-common` commit `312380a` — `feat(common): activate environment im tool contracts`
- `novaic-agent-runtime` commit `7c59403` — `feat(runtime): activate environment im executors`
- Deployed via `./deploy services`.
- Production smoke:
  - `env_active ['im_read', 'im_reply', 'im_send']`
  - `env_executors ['im_read', 'im_reply', 'im_send']`
  - `display {'im_read': 'environment_observed', 'im_reply': 'reply_sent', 'im_send': 'subagent_message_sent'}`

## Verification

- `PYTHONPATH=.:../novaic-agent-runtime pytest`
  - Common full suite: `112 passed`
- `PYTHONPATH=.:../novaic-common pytest`
  - Runtime full suite: `208 passed`

## Done Criteria

- LLM schema exposure includes `im_read`, `im_reply`, and `im_send`.
- Runtime dispatch can execute all three.
- Agent Monitor has user-facing display kinds for all three.
- No old tool is removed in this ticket.
