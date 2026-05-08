# 全面审计纯粹 DSL 目标差距

## Problem Definition

当前代码已经完成一轮 FSM 基建、worker roster、effect boundary、CI guard 改造，但用户明确追问“现在是否纯粹 DSL”，并要求继续全面排查。需要用代码证据系统审计当前形态与“纯粹 DSL”的差距，避免把“DSL 化了一部分”误报为“纯 DSL 终态”。

## Proposed Solution

将审计拆成多个子问题：

1. 证明当前 live path 是否已经接入新 FSM/worker/roster 基建；
2. 审计 worker assembly/action engine/effect adapter 与纯 DSL 目标的差距；
3. 扫描旧路径、兼容分支、未接入新逻辑、residue 词汇与 CI guard 覆盖；
4. 输出可执行的后续工单清单，标注优先级、风险和是否需要拆分。

## Acceptance Criteria

- 每个结论都有文件/行号或命令输出证据。
- 明确区分“已 DSL 化”、“仍是合理 Python 边界”、“不符合纯 DSL 目标”的代码。
- 证明当前 runtime 是否实际走新路径，而不是只新增了未接入代码。
- 发现的 GAP 必须形成工单级清单。
- 必须运行相关 residue/architecture guard/test 命令。
- 最终问题 success check 明确残余风险，不把未完成优化藏起来。

## Verification Plan

- 使用 `rg`、`nl`、`git diff`、targeted tests/lints 审计代码路径。
- 运行 architecture guards：runtime worker supervision、retired vocabulary、deploy smoke、start config、generated artifact lint。
- 运行关键 targeted tests：FSM runner、worker roster、worker effect plan、assembly helper、session/task/saga cutover。
- 账本最终执行 validate/render/status/next。

## Risks

- 审计范围较大，若强行 one_go 容易遗漏；应拆分。
- “纯 DSL”是目标形态，不应把合理的基础设施 Python 代码误判为问题。
- 部分旧词汇可能只存在于防回归测试中，需要区分活路径与 guard 文本。

## Assumptions

- 本轮主要做全面排查与工单化，不直接进行大规模架构重构。
- 远程部署状态不是本轮审计核心，除非代码路径证据需要验证部署脚本。
