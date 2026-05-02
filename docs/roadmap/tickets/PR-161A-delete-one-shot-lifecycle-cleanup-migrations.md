# PR-161A — Delete One-Shot Lifecycle Cleanup Migrations

| Field | Value |
| --- | --- |
| Status | `[done]` |
| Owner | Codex |
| Created | 2026-05-02 |
| Parent | PR-161 |
| Repos | root, docs |

## Goal

删除 PR-41/47/51 时代的一次性 lifecycle 清理脚本和 staging runbook，避免未来维护者误以为这些旧 SQL 仍是当前运维路径。

## Current-State Analysis

- 线上 `chat_messages` 当前 lifecycle 主路径已经由 Entangled message state machine / subscriber ownership 控制。
- PR-160 已把旧 backup tables 清掉，`chat_messages_backup_pr47` / `chat_messages_backup_pr51` 不再存在。
- `scripts/migrations/047_cleanup_ancient_user_message_pending.sql` 和 `048_cleanup_stuck_claimed.sql` 仍在 active scripts 目录。
- `scripts/gateway/migrate_pr41_agent_reply_orphans.sh` 仍指向旧 `gateway.db` 和旧 pending/orphan 形态。
- `docs/runbooks/pr41-pr42-staging-verification.md` 仍教人运行旧迁移。

## Implementation Plan

- [x] 删除上述 one-shot migration/runbook 文件。
- [x] 收紧 `scripts/ci/lint_lifecycle.sh`，移除旧迁移 allowlist，并把这些文件名加入 retired guard。
- [x] 运行 lifecycle lint 与部署/config guard。
- [x] Git 提交。

## Done Criteria

- [x] 旧 one-shot lifecycle cleanup 文件不存在。
- [x] lint 不再 allowlist 已删除 SQL。
- [x] guard 会阻止这些文件名重新出现。
- [x] Verification recorded.

## Verification

- `bash scripts/ci/lint_lifecycle.sh` → OK.
- `python3 scripts/ci/check_start_config_contract.py` → OK.
- `rg` confirmed no active runbook/script references except the guard itself.
