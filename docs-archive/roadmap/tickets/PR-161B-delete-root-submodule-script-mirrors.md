# PR-161B — Delete Root Submodule Script Mirrors

| Field | Value |
| --- | --- |
| Status | `[done]` |
| Owner | Codex |
| Created | 2026-05-02 |
| Parent | PR-161 |
| Repos | root, docs |

## Goal

删除 `scripts/submodules/**` 这套父仓库镜像脚本。当前真实入口应在子仓库自身或根 `deploy` / `scripts/start.sh`，镜像副本会产生“两个脚本哪个是准的”的维护分支。

## Current-State Analysis

- `scripts/submodules/**` 有 39 个文件。
- 根 `deploy` 不依赖该目录。
- 只有 `docs/runbooks/local-backends.md` 还把镜像脚本描述成可任选入口。
- `scripts/ci/check_start_config_contract.py` 只 guard 其中一个已删除的历史文件，没有禁止整棵镜像目录回归。

## Implementation Plan

- [x] 删除 `scripts/submodules/**`。
- [x] 更新 runbook，不再推荐镜像入口。
- [x] 增加 guard：`scripts/submodules` 目录不得存在。
- [x] 运行 deploy/config guard。
- [x] Git 提交。

## Done Criteria

- [x] `scripts/submodules` 不存在。
- [x] Active runbook 不再引用 root mirror scripts。
- [x] Guard catches reintroduction.
- [x] Verification recorded.

## Verification

- `python3 scripts/ci/check_start_config_contract.py` → OK.
- `test ! -e scripts/submodules` → OK.
- `rg "scripts/submodules"` shows only guard and historical/ticket references.
