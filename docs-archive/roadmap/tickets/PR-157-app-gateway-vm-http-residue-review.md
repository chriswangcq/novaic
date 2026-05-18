# PR-157 — App Gateway `/api/vm/*` Residue Review

| Field | Value |
| --- | --- |
| Status | `[done]` |
| Owner | Codex |
| Parent | Gateway / Business / Entangled boundary cleanup |
| Repos | novaic-app, novaic-business, novaic-device, docs |

## Goal

复核并清理客户端仍通过 `gateway_get` / `gateway_post` 访问 `/api/vm/*`
的旧路径。产品主路径应是：

- App 数据读写通过 Entangled entity/action。
- Gateway 只做 Auth、App WS、file proxy、TURN、WebRTC signaling。
- Device/VmControl 的 `/api/vm*` 只允许存在于设备执行侧或 CloudBridge 内部协议，不允许作为 App → Gateway 业务通路。

## Current Finding

- Gateway 已不挂载 `/api/vm/*`；`main_gateway.py` 明确注释 VM API 由 Device Service 承接。
- App 活代码中 `src/services/vm.ts` 仍以 "Gateway API based VM management" 命名，并通过 Tauri `gateway_get/post` 调 `/api/vm/*`。
- Device Service / VmControl 内部仍有 `/api/vm*` 路由，这是硬件执行面，不属于本票要删的 Gateway HTTP 残留。

## Small Tickets

- [x] [PR-157A](PR-157A-device-entangled-vm-prep-actions.md) — 补齐 image/env VM prep 的 Entangled action。
- [x] [PR-157B](PR-157B-remove-app-gateway-vm-service.md) — 删除 App 旧 `services/vm.ts` Gateway VM 服务。
- [x] [PR-157C](PR-157C-remove-agent-scoped-vm-status-ui-residue.md) — 清理 agent-scoped VM status UI 残留。
- [x] [PR-157D](PR-157D-guard-app-gateway-vm-http-residue.md) — 加 guardrail 防止 App 重新长出 `/api/vm*` Gateway 调用。

## Done Criteria

- [x] `novaic-app/src` 中没有 `gateway_get/post` 调 `/api/vm*`。
- [x] App 创建 Linux device 的镜像检查/下载走 Entangled action。
- [x] 旧 `src/services/vm.ts` 物理删除。
- [x] Guardrail 覆盖 App active source。
- [x] 单元测试、冒烟测试、部署、Git 提交闭环。
