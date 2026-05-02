# PR-161 — No-Value Script and Runbook Cleanup

| Field | Value |
| --- | --- |
| Status | `[open]` |
| Owner | Codex |
| Created | 2026-05-02 |
| Repos | root, novaic-app, novaic-agent-runtime, novaic-business, novaic-gateway, docs |
| Depends on | PR-160 |

## Goal

继续删除无产品价值的旧脚本和 runbook。PR-156 已覆盖最危险的 deploy/config 残留；本票面向剩余历史入口做小步、可验证的清理，避免“看起来还能用”的旧脚本误导维护。

## Why This Matters

AI 时代写新代码很便宜，维护旧分支很贵。脚本和 runbook 是最容易让旧路径复活的地方：即使活代码已经收口，旧命令仍会给未来维护者一个错误入口。

## Required Process

1. 分析现状：扫描 active docs、runbooks、scripts、packaged resources，区分当前路径、历史归档、无价值残留。
2. 创建小工单：每类无价值入口单独成票。
3. 对照小工单实施：每个小票必须包含 lint/guardrail、必要测试、冒烟验证、部署、git 提交。
4. 确认是否收口：若还有无价值旧入口，继续拆票；否则关闭本大票。

## Boundary Invariant

- Current operational runbooks must point to current commands only.
- Historical docs must be clearly archive/archaeology, not operational instructions.
- Scripts that are not current product/dev/deploy paths should be deleted unless a concrete owner and usage is documented.
- Guardrails should cover deleted high-risk names.

## Small Tickets

- [x] PR-161A — Delete One-Shot Lifecycle Cleanup Migrations
- [ ] PR-161B — Delete Root Submodule Script Mirrors
- [ ] PR-161C — Delete Gateway Legacy Data/Replayer Scripts
- [ ] PR-161D — Delete Obsolete Local DB Recovery Scripts

## Done Criteria

- [ ] Active runbooks do not instruct retired deploy/runtime/subscriber/tool paths.
- [ ] No-value scripts are physically deleted, not renamed into limbo.
- [ ] Remaining historical docs are clearly labeled as archive or reviews.
- [ ] Guardrail catches the highest-risk deleted script/runbook names.
- [ ] Affected services/docs are tested or linted, deployed if needed, and git commits are recorded.
