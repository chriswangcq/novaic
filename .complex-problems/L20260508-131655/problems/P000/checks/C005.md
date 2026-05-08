# P000 Check - 全面审核当前代码与 FSM 基建 + 业务 DSL 的 gap

## Status

success

## Summary

本次全面审核已完成。当前代码已经从旧 imperative harness 迁移到 ledger-backed FSM coordinator + generic worker substrate 的形态；但距离“最完美形态：单一 Generic FSM Runner + 业务只剩 declarative DSL + 全边界显式 + CI 强门禁”还有 7 个明确 gap。

## Evidence

- P001-P005 五个子审计全部完成并 check success。
- 读取了 FSM substrate、Session/Task/Saga repo/ledger/fsm、worker assembly/handlers/effects、dependency providers、Cortex registry、guard tests、CI/deploy/start scripts。
- 执行并通过 targeted tests/lints 和完整本地测试矩阵。

## Criteria Map

- FSM substrate：已审计，主路径接入成立。
- 业务 DSL/worker assembly：已审计，worker lifecycle 统一但 DSL 未极致。
- 显式依赖边界：已审计，Queue/Runtime 主路径清晰，Cortex registry 有 gap。
- 旧路径残留：已审计，活旧路径未发现，命名/allowlist 残留存在。
- 测试/CI/部署守卫：已审计，本地矩阵全绿，CI 未纳入 full test matrix。

## Execution Map

- 建账本并拆 P001-P005。
- 每个子问题创建 ticket、执行审计、记录 result、做 success check。
- 根问题记录综合审计报告。

## Stress Test

审计刻意覆盖了两个容易误判方向：

- 没有只凭“有 FSM 文件”就认为完成，而是追踪了 repo/ledger/outbox/claim/dispatch 活路径和测试。
- 没有把所有 `legacy` grep 命中当问题，而是分成活代码、测试守卫、命名残留、历史文档。

## Residual Risk

本次是全面审计，不是修复。剩余 gap 已明确列出，后续若要继续推进，需要按新账本拆成实现工单，尤其是 Generic FSM Runner、业务 DSL 化、Cortex registry 显式边界、CI full matrix 和 worker roster SSOT。
