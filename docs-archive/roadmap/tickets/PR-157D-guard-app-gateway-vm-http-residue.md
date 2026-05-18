# PR-157D — Guard App Gateway VM HTTP Residue

| Field | Value |
| --- | --- |
| Status | `[done]` |
| Owner | Codex |
| Parent | [PR-157](PR-157-app-gateway-vm-http-residue-review.md) |
| Repos | root scripts/ci, novaic-app |

## Goal

用测试/CI 固化边界：App active source 不允许重新通过 Tauri Gateway HTTP
访问 `/api/vm*`，也不允许重新引入 `src/services/vm.ts`。

## Scope

- [x] 新增 guardrail test 或 CI 脚本，扫描 `novaic-app/src`。
- [x] 允许 `gateway_get` 用于 Auth/File/TURN 等非 VM 边界；只禁止 `/api/vm*`。
- [x] 明确排除 `src-tauri/vmcontrol` 的设备执行面路由。

## Tests / Guardrails

- [x] `npm run test:unit -- src/application/appGatewayVmResidue.test.ts`
- [x] 若接入 root CI：对应脚本本地通过。

## Smoke / Deploy

- [x] `npm run build`
- [x] `./deploy frontend`。

## Git

- [x] Commit independently after tests pass.
