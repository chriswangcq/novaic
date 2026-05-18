# PR-180A — Delete Business device proxy routes with no active caller

Status: `[closed]`

## Finding

Business still exposes these forwarding routes:

- `/internal/agents/{agent_id}/qemu/*`
- `/internal/agents/{agent_id}/vm/{path}`
- `/internal/agents/{agent_id}/mobile/{path}`
- `/internal/agents/{agent_id}/hd/{path}`

They forward to Device Service through `device_client.proxy_qemu_request`.

Runtime no longer exposes or executes the old VM/Mobile/HD tool set from these routes. Current LLM-facing tool schemas come from `common.tools.llm_builtin.AGENT_BUILTIN_TOOL_SCHEMAS`, and Runtime executors are explicit in `task_queue.handlers.tool_handlers._EXECUTORS`.

## Scope

- Remove the Business proxy routes.
- Remove `device_client.proxy_qemu_request`.
- Keep Business hardware orchestration APIs (`device_client.hw_*`) and Device Service owned routes unchanged.
- Add tests/guards that Business does not re-expose these forwarding routes.

## Tests

- Focused Business route guard test.
- Existing Business tests.
- Static scan for `proxy_qemu_request`.

## Deployment / Git

- Deploy Business.
- Commit/push `novaic-business` and root pointer/docs.

## Closure

- Removed Business `/internal/agents/{agent_id}/qemu/*`, `/vm/*`, `/mobile/*`, and `/hd/*` forwarding routes.
- Removed `business.device_client.proxy_qemu_request`.
- Kept Business `hw_*` orchestration and Device Service owned execution routes unchanged.
- Tests: focused Business route guard and device prep tests → `6 passed`; full Business suite → `149 passed, 1 warning`.
- Deployment: `./deploy business`; production Business health returned healthy; removed QEMU proxy route returned `404`.
