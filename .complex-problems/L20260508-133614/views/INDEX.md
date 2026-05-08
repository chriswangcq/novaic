# Complex Problem Ledger

Ledger: L20260508-133614
Schema: v6
Root: P000 - 补齐 FSM 基建 + 业务 DSL 全部 GAP
Status: doing
Updated: 2026-05-08T06:16:01+00:00

## Problem Tree
- [done] P000: 补齐 FSM 基建 + 业务 DSL 全部 GAP
  - [done] P001: Generic FSM Runner 接入 Session/Task/Saga
  - [done] P002: Worker DSL 与 roster SSOT 收口
    - [done] P007: Roster-driven runtime launch generation
  - [done] P003: Cortex registry 显式依赖边界收口
  - [done] P004: 旧词汇、退休注释、transitional allowlist 清理
  - [done] P005: CI full matrix 与架构守卫门禁接入
  - [done] P006: 全局残留扫描与最终验证

## Active

## Blocked

## Done
- [x] P000: 补齐 FSM 基建 + 业务 DSL 全部 GAP
- [x] P001: Generic FSM Runner 接入 Session/Task/Saga
- [x] P002: Worker DSL 与 roster SSOT 收口
- [x] P003: Cortex registry 显式依赖边界收口
- [x] P004: 旧词汇、退休注释、transitional allowlist 清理
- [x] P005: CI full matrix 与架构守卫门禁接入
- [x] P006: 全局残留扫描与最终验证
- [x] P007: Roster-driven runtime launch generation

## Tickets
- [done] T000: 补齐 FSM 基建 + 业务 DSL 全部 GAP -> P000 (split)
- [done] T001: Generic FSM Runner 接入 Session/Task/Saga -> P001 (one_go)
- [done] T002: P002 Ticket - Worker DSL 与 roster SSOT 收口 -> P002 (one_go)
- [done] T003: P007 Ticket - Roster-driven runtime launch generation -> P007 (one_go)
- [done] T004: P003 Ticket - Cortex registry 显式依赖边界收口 -> P003 (one_go)
- [done] T005: P004 Ticket - 旧词汇、退休注释、transitional allowlist 清理 -> P004 (one_go)
- [done] T006: CI full matrix 与架构守卫门禁接入 -> P005 (one_go)
- [done] T007: 全局残留扫描与最终验证 -> P006 (one_go)

## Latest Checks
- [success] C000: P001 P001 is successful. Active Session/Task/Saga transition write paths now route through the generic `FsmTransitionRunner`, keeping business reducers/handlers away from repeated event/state/outbox persistence mechanics.
- [not_success] C001: P002 P002 is improved but not complete. The canonical roster now drives supervision checks, deploy status, fresh-smoke runtime logs, CI guards, and registry mode order. However, `scripts/start.sh` still manually launches task/saga/outbox/health/scheduler processes with hand-coded loops and command blocks.
- [success] C002: P007 P007 is successful. Runtime launch commands are now generated from the canonical roster and `scripts/start.sh` no longer owns a second worker launch list.
- [success] C003: P002 P002 is now successful after follow-up P007. Worker command modes, supervised process roles, log expectations, deploy status checks, fresh-smoke runtime logs, and launch commands now flow from one canonical roster.
- [success] C004: P003 P003 is successful. The Cortex registry no longer hides environment or clock reads in its constructor; production defaults are resolved in a named boundary factory.
- [success] C005: P004 P004 complete: retired runtime vocabulary physically cleaned and guarded.
- [success] C006: P005 P005 complete: CI and local full-matrix entries now run the runtime architecture guards.
- [success] C007: P006 P006 complete: full matrix and GitHub lint guard surface passed, with one stale roster test corrected.
- [success] C008: P000 P000 complete: all identified FSM substrate + business DSL gaps are closed in the repository verification scope.
