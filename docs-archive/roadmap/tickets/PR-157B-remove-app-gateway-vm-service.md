# PR-157B — Remove App Gateway VM Service

| Field | Value |
| --- | --- |
| Status | `[done]` |
| Owner | Codex |
| Parent | [PR-157](PR-157-app-gateway-vm-http-residue-review.md) |
| Repos | novaic-app |

## Goal

物理删除 `src/services/vm.ts` 这条旧 App → Gateway `/api/vm/*` 服务路径，
并把 Linux VM 创建流程迁移到 `DeviceService` 的 Entangled action helper。

## Scope

- [x] 删除 `novaic-app/src/services/vm.ts`。
- [x] `DeviceService` 提供 `resolveSourceImagePath()` / `extractErrorMessage()` 等当前 UI 所需 helper。
- [x] `AddLinuxVMModal` / `AddLinuxVMUserModal` 不再从旧 VM service 导入任何内容。
- [x] `DeviceService` 中仅保留 Entangled action 或 entity cache 读写。

## Tests / Guardrails

- [x] App unit test 覆盖 `resolveSourceImagePath()` 选择本地 path、复用已下载镜像、触发下载三条路径。
- [x] TypeScript build 通过。

## Smoke / Deploy

- [x] `npm run test:unit -- src/application/deviceService.test.ts`
- [x] `npm run build`
- [x] `./deploy frontend` 和需要时 `./deploy desktop`。

## Git

- [x] Commit independently after tests pass.
