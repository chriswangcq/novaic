# PR-161D — Delete Obsolete Local DB Recovery Scripts

| Field | Value |
| --- | --- |
| Status | `[open]` |
| Owner | Codex |
| Created | 2026-05-02 |
| Parent | PR-161 |
| Repos | root |

## Goal

删除旧 local DB / old agent-loop recovery 脚本，避免用旧 `gateway.db` / `queue.db` 表结构去修当前线上 Entangled+Cortex+Runtime 架构。

## Current-State Analysis

- `scripts/cleanup_all_dbs.sh` / `cleanup_queue_db.sh` 操作旧 local app DB layout。
- `scripts/reset-agent-data.sh` 操作旧 Gateway sessions/pipeline task tables 和 OSS user prefix。
- `scripts/recover_agent_loop.sh` 写旧 `chat_messages.status='sending'`、旧 `subagents.wake_at` 等已退休字段/表意。

## Implementation Plan

- [ ] 删除上述 obsolete recovery/cleanup scripts。
- [ ] 扩展 guard，阻止这些脚本名重新出现。
- [ ] 运行 deploy/config guard 与 lifecycle guard。
- [ ] Git 提交。

## Done Criteria

- [ ] Obsolete local recovery scripts 不存在。
- [ ] Guard catches reintroduction.
- [ ] Verification recorded.
