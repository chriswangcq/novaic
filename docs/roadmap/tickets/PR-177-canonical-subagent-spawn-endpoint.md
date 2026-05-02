# PR-177: Canonical SubAgent Spawn Endpoint

Status: `[closed]`

## Problem

Business exposed two live internal endpoints for the same SubAgent spawn behavior:

- `/internal/subagents/{agent_id}/spawn`
- `/internal/agents/{agent_id}/subagent/spawn`

Both created a child SubAgent and emitted the initial `SUBAGENT_SEND` Environment IM message. Runtime used the first path, while Cortex proxy still used the second. This duplicated behavior and made future Environment/subagent maintenance more expensive.

## Scope

- Keep `/internal/subagents/{agent_id}/spawn` as the single canonical Business endpoint.
- Remove the agent-scoped duplicate endpoint from `business/internal/agent.py`.
- Switch Cortex proxy `subagent action=spawn` to the canonical endpoint.
- Add/adjust tests so the duplicate route cannot return silently.

## Non-goals

- Do not rename the `subagent_spawn` LLM tool.
- Do not change the `SUBAGENT_SEND` internal message type.
- Do not change Environment notification dispatch semantics.

## Verification

- Business SubAgent spawn unit test covers the canonical endpoint and asserts the duplicate route is absent.
- Cortex proxy test/guard covers the canonical route.
- Focused Business/Cortex tests pass.

## Closure

- The duplicate `/internal/agents/{agent_id}/subagent/spawn` endpoint was physically removed.
- Cortex proxy now calls `/internal/subagents/{agent_id}/spawn`.
- The canonical path still emits `SUBAGENT_SEND` and Environment IM rows.
