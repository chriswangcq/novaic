# PR-120 — Remove Device Service Retired Entangled CLI

| Field | Value |
| --- | --- |
| Status | `[✓]` |
| Owner | Codex |
| Created | 2026-04-30 |
| Repos | `novaic-device`, parent docs |
| Depends on | PR-119 |

## 目标

Device Service 的实体读写已经统一通过 Business proxy，`main_device.py --entangled-url` 只剩 deprecated 参数和 `ServiceConfig.ENTANGLED_*` 写入。删除这条旧入口，避免 Device 被误认为仍可直连 Entangled。

## Detailed Plan

1. [x] Audit Device active code for direct Entangled usage.
   - Device active entity access uses `BusinessEntityClient`.
   - No active `EntangledServiceClient` import in `novaic-device`.
2. [x] Remove `--entangled-url` from `main_device.py`.
3. [x] Remove the associated `ServiceConfig.ENTANGLED_*` mutation branch.
4. [x] Add a guardrail test that prevents the retired CLI and config branch from returning.
5. [x] Run targeted tests and `compileall`.
6. [x] Deploy Device and verify remote source plus service health.
7. [x] Commit and push affected repos.

## Tests

- [x] `python -m pytest tests/test_pr120_no_device_entangled_cli.py`
- [x] `python -m compileall -q .`
- [x] Static search shows no Device active-code `--entangled-url` path.

## Smoke / Deploy

- [x] Deploy affected service.
- [x] Remote source assertion proves the retired Device CLI path is absent.
- [x] `./deploy status` shows backend services healthy.

## Git

- [x] Device commit.
- [x] Parent docs/submodule commit.
- [x] Push all changed repos.
