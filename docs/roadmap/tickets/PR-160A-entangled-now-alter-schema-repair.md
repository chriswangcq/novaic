# PR-160A — Entangled NOW ALTER Schema Repair

| Field | Value |
| --- | --- |
| Status | `[done]` |
| Owner | Codex |
| Created | 2026-05-02 |
| Parent | PR-160 |
| Repos | Entangled, docs |

## Goal

修复 Entangled 对 `default="NOW"` 字段执行 `ALTER TABLE ADD COLUMN` 时生成 SQLite 不支持的 `DEFAULT (datetime('now'))` 的问题，并验证线上 `agent_state.sleep_started_at` 能被补齐。

## Current-State Analysis

线上 `/opt/novaic/data/entangled.db` 证据：

- `agent_state` 当前列：`agent_id,state,wake_triggers,rest_reason,handoff_notes,rest_started_at,last_active_at,sleep_reason`
- 当前 schema 期望列包含 `sleep_started_at`。
- Entangled 日志反复出现：`Failed to register agent-state: Cannot add a column with non-constant default`。

根因是 `FieldDef.default == "NOW"` 在 `CREATE TABLE` 里合法，但在 SQLite `ALTER TABLE ADD COLUMN` 中不合法。Entangled 应该在 ADD COLUMN 迁移语境下省略非 constant default；需要该时间语义的产品写入方应显式写值。

## Implementation Plan

- [x] Entangled：新增 ADD COLUMN 专用 DDL，`default="NOW"` 不输出 SQL default。
- [x] Entangled：增加单元测试，证明带 NOW 的新增列可应用到已有非空表。
- [x] 部署 Entangled。
- [x] 线上验证 `agent_state.sleep_started_at` 已出现，schema 注册不再报该错误。
- [x] Git 提交。

## Done Criteria

- [x] Unit test covers NOW ADD COLUMN.
- [x] Entangled deployed.
- [x] Online `agent_state` has `sleep_started_at`.
- [x] Recent Entangled logs no longer show `Cannot add a column with non-constant default`.
- [x] Git commits recorded.

## Verification

- `cd Entangled/packages/server-python && python3 -m pytest tests/test_apply_defaults.py tests/test_schema_and_notifier.py` → 17 passed.
- `cd novaic-business && python3 -m pytest tests/test_pr149_retired_agent_selfdrive_surfaces.py tests/test_schema_invariants.py` → 8 passed.
- `./deploy entangled` → deployed and restarted backend services.
- Online `PRAGMA table_info(agent_state);` includes `sleep_started_at`.
- Recent Entangled log shows `ALTER TABLE agent_state ADD COLUMN sleep_started_at TEXT;` and no new `Cannot add a column with non-constant default`.
