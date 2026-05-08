# Complex Problem Ledger

Ledger: L20260508-131655
Schema: v6
Root: P000 - 全面审核当前代码与 FSM 基建 + 业务 DSL 的 gap
Status: doing
Updated: 2026-05-08T05:35:09+00:00

## Problem Tree
- [done] P000: 全面审核当前代码与 FSM 基建 + 业务 DSL 的 gap
  - [done] P001: 审计 FSM substrate 与状态机接入
  - [done] P002: 审计业务 DSL 与 worker assembly 厚度
  - [done] P003: 审计显式依赖边界与 side-effect adapter
  - [done] P004: 审计旧路径残留与兼容分支
  - [done] P005: 审计测试 CI 部署守卫覆盖

## Active

## Blocked

## Done
- [x] P000: 全面审核当前代码与 FSM 基建 + 业务 DSL 的 gap
- [x] P001: 审计 FSM substrate 与状态机接入
- [x] P002: 审计业务 DSL 与 worker assembly 厚度
- [x] P003: 审计显式依赖边界与 side-effect adapter
- [x] P004: 审计旧路径残留与兼容分支
- [x] P005: 审计测试 CI 部署守卫覆盖

## Tickets
- [done] T000: 全面审核当前代码与 FSM 基建 + 业务 DSL 的 gap -> P000 (split)
- [done] T001: 审计 FSM substrate 与状态机接入 -> P001 (one_go)
- [done] T002: P002 Ticket - 审计业务 DSL 与 worker assembly 厚度 -> P002 (one_go)
- [done] T003: P003 Ticket - 审计显式依赖边界与 side-effect adapter -> P003 (one_go)
- [done] T004: P004 Ticket - 审计旧路径残留与兼容分支 -> P004 (one_go)
- [done] T005: P005 Ticket - 审计测试 CI 部署守卫覆盖 -> P005 (one_go)

## Latest Checks
- [success] C000: P001 FSM substrate 与 Session/Task/Saga 状态机接入审计完成
- [success] C001: P002 worker assembly/业务 DSL 厚度审计完成
- [success] C002: P003 显式依赖边界/side-effect adapter 审计完成
- [success] C003: P004 旧路径残留/兼容分支审计完成
- [success] C004: P005 测试/CI/部署守卫审计完成
- [success] C005: P000 全面审核完成：当前是 ledger-backed FSM coordinator + generic worker substrate，仍有 7 个 gap
