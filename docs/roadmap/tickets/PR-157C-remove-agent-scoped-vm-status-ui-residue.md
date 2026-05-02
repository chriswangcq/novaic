# PR-157C — Remove Agent-Scoped VM Status UI Residue

| Field | Value |
| --- | --- |
| Status | `[done]` |
| Owner | Codex |
| Parent | [PR-157](PR-157-app-gateway-vm-http-residue-review.md) |
| Repos | novaic-app |

## Goal

移除仍把 VM runtime 状态按 `agent_id` 聚合的旧 UI/Hook 残留。当前设备状态应以
`devices` entity + `devices.get_status` action 为准；agent 只通过 binding 关联 device。

## Scope

- [x] 删除未被主界面引用的 legacy `useVm`。
- [x] 删除未被主界面引用的 legacy Dashboard / AgentSelector，避免继续保留旧 VM status 模型。
- [x] Settings 删除 agent 时，若有 binding，按 device id 调 `devices.stop`，不再调用 `vmGetAllStatus`。
- [x] `useDevices` 不再暴露 `vmGetAllStatus` / `vmGetStatus` / `vmIsRunning` / `vmWaitForReady`。

## Tests / Guardrails

- [x] App source scan：无 `vmGetAllStatus` 等 agent-scoped VM status API。
- [x] TypeScript build 通过。

## Smoke / Deploy

- [x] `npm run build`
- [x] `./deploy frontend` 和需要时 `./deploy desktop`。

## Git

- [x] Commit independently after tests pass.
