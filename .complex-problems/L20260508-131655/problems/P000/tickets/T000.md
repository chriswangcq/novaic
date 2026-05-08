# 全面审核当前代码与 FSM 基建 + 业务 DSL 的 gap

## Problem Definition

需要对当前仓库进行全面审计，判断最新代码是否真正达到“FSM 基建层 + 业务 DSL 层”的目标形态，还是仍存在新基建未接入、业务代码偏厚、隐式依赖、旧路径残留、测试/CI 守卫不足等 gap。

## Proposed Solution

将审计拆成多个独立审计面：FSM substrate、业务 DSL/worker assembly、状态机接入与旧路径、显式依赖边界、测试/CI/部署守卫。每个审计面必须基于文件、测试、grep、diff 或命令证据，最后汇总成当前形态与 gap 列表。

## Acceptance Criteria

- 审计覆盖 Runtime FSM substrate、Session/Task/Saga 状态机、worker assembly DSL、action effect boundaries。
- 审计覆盖旧路径残留：direct SagaOrchestrator/create、active session SSOT、raw worker constructors、direct HTTP clients、coarse deploy status、compat branches。
- 审计覆盖显式依赖边界：time/id/env/http/global state 是否只在边界处出现。
- 审计覆盖测试与 CI 守卫：证明 gap 不会轻易回流。
- 输出明确区分：已达成、部分达成、仍有 gap、风险等级、建议下一步。

## Verification Plan

- 使用 `rg`、`git diff`、`pytest`、lint 脚本和源码阅读。
- 对关键文件给出路径证据。
- 最终账本 success check 映射每个验收项到证据。

## Risks

- 广泛审计可能发现已存在但不属于本次 FSM/DSL 主题的旧债；需要明确标注是否阻塞。
- 当前工作树包含未提交修改，审计必须基于当前文件状态，不假设 main 分支状态。

## Assumptions

- 用户当前需要的是审计报告，不是立即继续改代码。
- 如果发现小型 guard/lint 明显错误，可记录为 gap；不主动大改。
