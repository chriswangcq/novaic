# PR-161C — Delete Gateway Legacy Data/Replayer Scripts

| Field | Value |
| --- | --- |
| Status | `[done]` |
| Owner | Codex |
| Created | 2026-05-02 |
| Parent | PR-161 |
| Repos | root |

## Goal

删除旧 Gateway DB 时代的数据迁移、file backfill、runtime replay 脚本。当前 Gateway 边界已收口为 Auth/App WS/file proxy/WebRTC signaling/sync endpoint discovery；这些脚本继续存在会误导人回到旧业务通路。

## Current-State Analysis

- `scripts/gateway/migrate_legacy_user.py` / `migrate_user_data.py` 面向旧 Gateway auth/data migration。
- `scripts/gateway/backfill_file_id.py` 面向旧 `gateway.db.chat_messages` 附件 shape。
- `scripts/gateway/migrate_execution_logs_subagent_id.sh` 面向旧 execution log subagent id shape。
- `scripts/gateway/replay_gateway_runtime_chain.sh` / `fail_path_replay_gateway.sh` 面向旧 Gateway→Runtime health chain。

## Implementation Plan

- [x] 删除上述 gateway legacy scripts。
- [x] 扩展 guard，阻止这些脚本名重新出现。
- [x] 运行 deploy/config guard 和相关 script lint。
- [x] Git 提交。

## Done Criteria

- [x] Gateway legacy scripts 不存在。
- [x] Guard catches reintroduction.
- [x] Verification recorded.

## Verification

- `python3 scripts/ci/check_start_config_contract.py` → OK.
- `bash scripts/ci/lint_lifecycle.sh` → OK.
- `rg` shows deleted script names only inside the guard.
