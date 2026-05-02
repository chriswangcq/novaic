# PR-178: Remove Cortex SubAgent Spawn Proxy Mutation

Status: `[closed]`

## Problem

`subagent_spawn` has a clean LLM tool path:

1. Common/Cortex expose the Agent action schema.
2. Runtime executes the tool.
3. Runtime calls Business `/internal/subagents/{agent_id}/spawn`.
4. Business owns the actual subagent row, Environment IM row, and notification side effects.

However, Cortex still exposed a direct `subagent action=spawn` proxy command. That allowed a write operation to bypass the Runtime tool executor and Cortex tool trace, making the architecture look like Cortex owned part of the business mutation path.

## Desired boundary

- Cortex/Common may define or project the Agent action surface.
- Runtime owns LLM tool execution.
- Business owns SubAgent creation and Environment writes.
- Cortex proxy must not expose a parallel SubAgent spawn mutation.

## Small Tickets

1. Analyze current callers for Cortex `subagent spawn`.
2. Remove `spawn` support from Cortex CLI and BusinessProxy `_route_subagent`.
3. Keep `subagent list` if still useful as a read/diagnostic command.
4. Update proxy tests to assert `spawn` is unsupported and does not call Business.
5. Update PR-177 wording so it does not teach the now-removed proxy mutation path.
6. Run focused Cortex tests, deploy Cortex, commit, and push.

## Acceptance

- `novaic_cortex.proxy` contains no Business request for `/internal/subagents/{agent_id}/spawn`.
- `novaic_cortex.cli` no longer accepts `subagent spawn`.
- Runtime `subagent_spawn` executor remains the only active Agent write path and still calls Business canonical endpoint.
- Business canonical endpoint remains unchanged.

## Closure

- Cortex CLI/proxy `subagent spawn` was removed.
- Cortex proxy still allows `subagent list` as a read/diagnostic command.
- Runtime remains the only active Agent write executor for `subagent_spawn`.
