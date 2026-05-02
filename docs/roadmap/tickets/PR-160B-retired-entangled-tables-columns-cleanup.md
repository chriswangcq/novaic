# PR-160B — Retired Entangled Tables and Columns Cleanup

| Field | Value |
| --- | --- |
| Status | `[done]` |
| Owner | Codex |
| Created | 2026-05-02 |
| Parent | PR-160 |
| Repos | Entangled, online data, docs |

## Goal

把线上 Entangled DB 中已经退出产品路径的表和列物理清掉，并移除 Entangled 活代码里会继续允许旧字段写入的残留 allowlist。

## Current-State Analysis

线上 `/opt/novaic/data/entangled.db` 体检结果：

- Retired tables: `agent_memory` 0 rows, `agent_notebook` 0 rows, `agent_tasks` 0 rows, `chat_messages_backup_pr47` 0 rows, `chat_messages_backup_pr51` 25 rows.
- `agent_drive` stale columns: `memory_md`, `growth_log`, `drive_config` all empty.
- `agent_state` stale columns: `rest_reason` 1 non-empty row, `rest_started_at` 1 non-empty row, `handoff_notes` empty. Current schema uses `sleep_reason` / `sleep_started_at`.
- `subagents` stale columns: `historical_summary` 1 non-empty row, `handoff_notes` empty, `tool_ports` empty, `current_scope_id` empty, `last_scope_id` 3 non-empty rows, `last_scope_archived_at` 3 non-empty rows.
- SQLite online version is 3.45.1, so `ALTER TABLE ... DROP COLUMN` is available.

活代码状态：

- Business active schema no longer declares `historical_summary`, `handoff_notes`, `last_scope_id`, `last_scope_archived_at`, `rest_reason`, `rest_started_at`, or the retired agent-drive columns.
- Runtime tests already assert the PR-43 `last_scope_id` transport path is retired.
- Entangled `subagent_state.EXTRA_ALLOWLIST` still allows `last_scope_id` / `last_scope_archived_at`, which can re-normalize the retired shape if a stale caller sends it.

## Implementation Plan

- [x] Entangled：从 `subagent_state.EXTRA_ALLOWLIST` 删除 `last_scope_id` / `last_scope_archived_at`，更新相关测试为“旧字段被拒绝并告警”。
- [x] Online data：把 `agent_state.rest_reason/rest_started_at` 值迁移到 `sleep_reason/sleep_started_at`（仅目标为空时），然后 drop stale columns。
- [x] Online data：drop retired tables and stale columns from `agent_drive` / `subagents`.
- [x] 部署 Entangled。
- [x] 线上复查 shape：retired tables gone, stale columns gone, active services healthy。
- [x] Git 提交。

## Done Criteria

- [x] Entangled tests prove retired `last_scope_*` extras no longer land.
- [x] Online DB has no PR-160B retired tables.
- [x] Online `agent_drive`, `agent_state`, and `subagents` no longer contain PR-160B stale columns.
- [x] Backend services healthy after cleanup.
- [x] Git commits recorded.

## Verification

- `cd Entangled/packages/server-python && python3 -m pytest tests/test_subagent_state.py tests/test_apply_defaults.py` → 26 passed.
- `cd novaic-agent-runtime && python3 -m pytest tests/test_pr43_last_scope_wiring.py tests/test_pr43_previous_scope_transport.py tests/test_scheduler_dispatch.py` → 10 passed.
- `cd novaic-business && python3 -m pytest tests/test_schema_invariants.py tests/test_im_aggregation.py` → 26 passed.
- `./deploy entangled` → deployed.
- Online shape audit:
  - `retired_tables_present = []`
  - `agent_drive_stale_columns_present = []`
  - `agent_state_stale_columns_present = []`
  - `subagents_stale_columns_present = []`
  - `agent_state.sleep_reason/sleep_started_at/last_active_at/wake_triggers` present.
- `./deploy status` → all backend services healthy; relay active.
- Recent Entangled logs show no `no such column`, `ERROR`, or `Traceback`.
