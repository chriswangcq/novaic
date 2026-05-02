# PR-160 — Online Entangled Data Shape Audit

| Field | Value |
| --- | --- |
| Status | `[done]` |
| Owner | Codex |
| Created | 2026-05-02 |
| Repos | Entangled, novaic-business, novaic-app, novaic-device, docs |
| Depends on | PR-159 |

## Goal

做一次线上数据 shape 体检：重点找 Entangled entity 中仍可能存在的历史字段 shape，并优先清理数据或收紧 guard，而不是为旧 shape 保留兼容代码。

## Why This Matters

旧数据 shape 如果长期存在，会诱导代码继续保留 fallback / normalize / dual-shape 逻辑。当前项目阶段更适合“数据清理 + fail-fast + guardrail”，而不是用兼容层永久支持旧形态。

## Required Process

1. 分析现状：列出关键 Entangled entities、当前 schema、已知旧 shape、线上数据计数。
2. 创建小工单：每类旧 shape 单独成票，包含备份/删除/修复/guard。
3. 对照小工单实施：每个小票必须包含单元测试、线上数据检查、必要数据清理、部署、git 提交。
4. 确认是否收口：若还有旧 shape 或代码兼容分支，继续拆票；否则关闭本大票。

## Boundary Invariant

- Entangled schema is the live schema source.
- App and backend should reject invalid shape or rely on current schema, not silently normalize retired shape.
- One-off cleanup is preferable to permanent compatibility logic.
- Any data mutation must be explicit, backed up when needed, and recorded with count evidence.

## Small Tickets

- [x] PR-160A — Entangled NOW ALTER Schema Repair
- [x] PR-160B — Retired Entangled Tables and Columns Cleanup
- [x] PR-160C — Message Content JSON Shape Normalization

## Done Criteria

- [x] Key online entities have shape count evidence.
- [x] Any stale shape found is either cleaned or documented as intentionally current.
- [x] No active code keeps compatibility only for already-deleted shapes.
- [x] Guardrails prevent the same stale shape from returning.
- [x] Affected services are deployed and git commits are recorded.

## Closure Notes

- PR-160A fixed Entangled `default="NOW"` ALTER migrations and restored `agent_state.sleep_started_at` online.
- PR-160B removed retired tables and stale columns from online Entangled DB and rejected retired subagent continuity extras in Entangled state transitions.
- PR-160C normalized `chat_messages.content` to JSON object shape across Runtime, Business, App, and online data.
