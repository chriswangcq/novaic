# 补齐 FSM 基建 + 业务 DSL 全部 GAP

## Problem Definition

基于审计账本 `L20260508-131655` 的 7 个 gap，把当前代码从“已经有 ledger-backed FSM coordinator + generic worker substrate”继续推进到更接近完美形态：

- Generic FSM Runner 承接 Session/Task/Saga 共同 transition/outbox/projection 流程。
- 业务 worker role/effect/action 进一步 DSL 化，避免业务层继续承担大量 assembly plumbing。
- Cortex registry 的 env/time 默认值移到 startup/composition boundary 显式注入。
- 清理旧命名、退休注释、transitional allowlist，避免未来 agent 误读。
- 测试矩阵进入 CI 或等价强门禁。
- worker roster 建立单一 SSOT，由部署/启动/守卫共享。
- 全程不保留向后兼容分支；新逻辑必须接入活路径，有测试和 lint 守卫。

## Proposed Solution

拆成子问题逐项收口：

1. Generic FSM Runner substrate 与 Session/Task/Saga repo 接入。
2. Worker role/effect/action DSL 与 roster SSOT。
3. Cortex registry explicit dependency boundary。
4. 旧词汇/注释/transitional allowlist 清理。
5. CI/full test matrix 与 deploy/start guard 收口。
6. 全局验证、残留扫描、账本关闭。

每个子问题必须执行：实现、删除/迁移旧路径、补测试或 lint、运行局部验证。

## Acceptance Criteria

- 每个 gap 都有对应实现或被证据证明不需要实现。
- 新 substrate/DSL 必须被活路径调用，不允许只添加未接入代码。
- 旧路径/旧名字/兼容分支尽量物理删除；无法删除必须有明确理由和 guard。
- 所有新增/修改的架构边界有测试或 lint 守卫。
- 全仓测试矩阵和关键 lint 通过。

## Verification Plan

- 针对每个子问题运行 targeted tests/lints。
- 最后运行 `./scripts/run_all_tests.sh`。
- 运行 root CI lint chain 中与本改动相关的脚本。
- `git diff --check`。

## Risks

- Generic FSM Runner 抽象过度会增加复杂度；必须保持小而薄，只承接重复模式。
- Worker DSL 如果一次做太大容易破坏部署脚本；需要先建立 roster SSOT，再逐步让脚本/guard 消费。
- CI workflow 加 full matrix 可能增加耗时；若太重，需要拆成并行 job 而不是不接入。

## Assumptions

- 当前分支允许继续修改未提交代码。
- 不需要向后兼容旧 DB/旧 worker entrypoint/旧 HTTP allowlist。
- 本轮目标是代码和守卫落地，不只是设计文档。
