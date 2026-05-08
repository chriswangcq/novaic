# Complex Problem Ledger

Ledger: L20260508-165336
Schema: v6
Root: P000 - 全面排查当前代码与纯粹 DSL 目标的差距
Status: done
Updated: 2026-05-08T09:07:07+00:00

## Problem Tree
- [done] P000: 全面排查当前代码与纯粹 DSL 目标的差距
  - [done] P001: 证明当前 runtime 是否实际走新 FSM/worker/roster 路径
  - [done] P002: 审计业务 DSL 纯度与剩余过程式逻辑 GAP
  - [done] P003: 扫描旧路径、兼容分支、残留词汇与 CI guard 覆盖
  - [done] P004: 汇总纯 DSL 目标后续工单与实施路线

## Active

## Blocked

## Done
- [x] P000: 全面排查当前代码与纯粹 DSL 目标的差距
- [x] P001: 证明当前 runtime 是否实际走新 FSM/worker/roster 路径
- [x] P002: 审计业务 DSL 纯度与剩余过程式逻辑 GAP
- [x] P003: 扫描旧路径、兼容分支、残留词汇与 CI guard 覆盖
- [x] P004: 汇总纯 DSL 目标后续工单与实施路线

## Tickets
- [done] T000: 全面审计纯粹 DSL 目标差距 -> P000 (split)
- [done] T001: Ticket: Prove Runtime Live Path Uses New FSM Worker Roster -> P001 (one_go)
- [done] T002: Ticket: Audit Business DSL Purity Gap -> P002 (one_go)
- [done] T003: Ticket: Scan Legacy Paths, Compat Branches, Residue Vocabulary, and Guards -> P003 (one_go)
- [done] T004: Ticket: Summarize Pure DSL Remediation Backlog -> P004 (one_go)

## Latest Checks
- [success] C000: P001 Runtime live path is wired through runtime_roster, worker registry, and generic FSM transition ledgers; pure DSL is deferred to sibling audits.
- [success] C001: P002 Current runtime is not pure DSL; it is generic substrate plus declarative specs plus imperative action engines and hand-written assembly.
- [success] C002: P003 No active old session/FSM/worker branch was found; only test/CI guard references remain, with a bytecode hygiene gap for generated artifact checks.
- [success] C003: P004 Pure DSL closure backlog created: assembly specs, plan-first engines, task/saga/scheduler/health specs, handler registry review, CI hygiene, and status docs.
- [success] C004: P000 Comprehensive audit complete: live runtime/FSM path confirmed, no active old branch found, not pure DSL yet, and closure backlog DSL-001..DSL-008 recorded.
