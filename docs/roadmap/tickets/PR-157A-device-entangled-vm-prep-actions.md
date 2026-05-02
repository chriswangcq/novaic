# PR-157A — Device Entangled VM Prep Actions

| Field | Value |
| --- | --- |
| Status | `[done]` |
| Owner | Codex |
| Parent | [PR-157](PR-157-app-gateway-vm-http-residue-review.md) |
| Repos | novaic-business, novaic-device |

## Goal

把 App 当前需要的 VM prep 能力补进 Entangled action 主路径，避免前端为了
environment / cloud image check / cloud image download 回退到 Gateway HTTP。

## Scope

- [x] Device schema 为 `devices` 增加 action：
  - `environment_check`
  - `cloud_image_check`
  - `cloud_image_download`
- [x] Business `devices` action hook 注册对应 handler。
- [x] Business device client 增加 `/internal/hardware/*` 调用封装。
- [x] Device hardware API 增加纯硬件执行 endpoint，委托 CloudBridge typed command。

## Tests / Guardrails

- [x] Device schema action contract test。
- [x] Business action registration / handler source contract test。
- [x] Device hardware endpoint source contract test。

## Smoke / Deploy

- [x] `python3 -m pytest novaic-device/tests/test_pr157_device_vm_prep_actions.py -q`
- [x] `python3 -m pytest novaic-business/tests/test_pr157_device_vm_prep_actions.py -q`
- [x] `./deploy services` 或至少 `./deploy gateway`。

## Git

- [x] Commit independently after tests pass.
